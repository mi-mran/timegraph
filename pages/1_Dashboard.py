import streamlit as st
from supabase import create_client
from st_supabase_connection import SupabaseConnection
from dotenv import load_dotenv
import os
import pytesseract
from pdf2image import convert_from_bytes
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
#from sentence_transformers import SentenceTransformer
#from langchain_community.vectorstores import FAISS
import ollama
from itertools import product
import re
import time
import json
from streamlit_timeline import timeline
import requests


def get_pdf_text(pdf_doc):
    text_overall = ""

    pdf = convert_from_bytes(pdf_doc.read(), fmt='jpeg', dpi=150)

    for page_num, page in enumerate(pdf):
        # left, top, right, bottom
        # these coordinates work with SG court proceedings saved as PDFs
        # coordinates also correspond to the dpi used
        page = page.crop((0, 0, page.width, 1500))
    
        text = pytesseract.image_to_string(page, config="--psm 1 --oem 1")
        if not re.search('table of content', text, re.IGNORECASE):
            text_overall += text

    print(text_overall)
    
        # using pypdf2
        #pdf_reader = PdfReader(pdf)
        #for page in pdf_reader.pages:
        #    text += page.extract_text()
    
    doc_name = pdf_doc.name

    return text_overall, doc_name

def upload_pdf_to_bucket(pdf_file, supabase_client):
    supabase_client.storage.from_("documents_file").upload(file=pdf_file, file_options={"content-type": "application/pdf"})
    signed_url = supabase_client.storage.from_("documents_file").create_signed_url(f'{pdf_file.name}', 31536000)

    return signed_url

def get_text_chunks(raw_text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1000,
        chunk_overlap = 200,
        length_function = len,
    )

    chunks = text_splitter.split_text(raw_text)

    return chunks

def add_vectorstore(embed_model, text_chunks, doc_name, doc_url, supabase_client):
    #model = SentenceTransformer('Alibaba-NLP/gte-large-en-v1.5', trust_remote_code=True)
    #embed_model = SentenceTransformerEmbeddings(model_name='sentence-transformers/gtr-t5-base')
    embed_model = embed_model
    embeddings = embed_model.embed_documents(text_chunks)
    #embeddings = model.encode(text_chunks, show_progress_bar=True)

    # test creation of local vecstore
    #vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embed_model)

    update_list = []

    for chunk, embedding in product(text_chunks, embeddings):
        value = {
            'doc_name': doc_name,
            'content': chunk,
            'embedding_vector': embedding,
            'file_url': doc_url
                 }
        update_list.append(value)
    
    #data = supabase_client.table('documents').insert(update_list).execute()
    #data.create_index(measure=vecs.IndexMeasure.cosine_distance)
    print('Uploaded to supabase!')
    #supabase_client.auth.sign_out()
    
    #return embeddings

def vec_search(supabase_client, user_id, k: int = 50):
    # currently not in use since naive sequential similarity search is used instead
    query = "Extract a timeline with dates from the document given below. The timeline should be stored in json as an array of event objects where each event has the attributes 'year', 'month', 'day_of_month' and 'event'."
    #relevant_chunks = vectorstore.similarity_search(query, k=k)
    
    vec_db = supabase_client.table('documents').select('*').eq('user_id', f'{user_id}').execute()
    #print(vec_db[0])
    return vec_db

@st.cache_resource
def load_supabase_client():
    conn = st.connection("supabase", type=SupabaseConnection)
    st_supabase_client = create_client(supabase_url=os.environ.get("SUPABASE_URL"), supabase_key=os.environ.get("SUPABASE_KEY"))

    return st_supabase_client

#@st.cache_data
def get_user_docs(st_supabase_client, user_id):
    user_docs = st_supabase_client.table('documents').select('doc_name').eq('user_id', f'{user_id}').execute()
    if user_docs is not None:
        doc_names = list({v['doc_name']:v for v in user_docs.data}.values())
        return doc_names
    else:
        return None
    
def create_item_summary(text):
    SYSTEM = f"""
            Extract a timeline with dates from the list of texts given below. The timeline should be stored in json as an array of event objects where each event has the attributes "year", "month", "day_of_month" and "event". Here is the text: {text}.
            """
    user_prompt = "Help me generate a timeline from this text. Please return me as an array of event objects where each event has the attributes 'year', 'month', 'day_of_month' and 'event'. Try to summarise and give a concise event title."

    raw_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    {SYSTEM}
    <|eot_id|><|start_header_id|>user<|end_header_id|>
    {user_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
    """
    
    # for local instance of ollama
    #response = ollama.generate(model='llama3', prompt=raw_prompt)
    # for Angeal's cloudflare API endpoint for ollama
    data = {
        # for Glenn's API endpoint for ollama
        "model": "llama3:8b",
        # for local instance of ollama
        #"model": "llama3",
        "prompt": raw_prompt,
        "raw": True,
        "stream": False
        }

    headers = {
        "CF-Access-Client-Id": os.environ.get("CF_ACCESS_CLIENT_ID"),
        "CF-Access-Client-Secret": os.environ.get("CF_ACCESS_CLIENT_SECRET")
        }
    
    # for Angeal's cloudflare API endpoint for ollama
    #response = requests.post("https://home-ollama.justpotato.org/api/generate", data=json.dumps(data), headers=headers).text
    # for Glenn's API endpoint for ollama
    response = requests.post("https://office-ollama.justpotato.org/api/generate", data=json.dumps(data), headers=headers).text
    
    # for Glenn's API endpoint for ollama
    response = json.loads(response)["response"]
    # for local instance of ollama
    #response = response["response"]
    response = response.replace("```json", "").replace("```", "").replace("\n", " ").strip()
    response = json.loads('[' + re.search(r'.*?\[(.*)].*',response).group(1) + ']')
    
    return response

def generate_timeline(st_supabase_client, user_id, doc_name, timeline_container):
    query = "dates and events"
    embed_model = SentenceTransformerEmbeddings(model_name='sentence-transformers/gtr-t5-base')
    embed_query = embed_model.embed_query(query)

    vec_search_table = st_supabase_client.rpc('vector_search', {
    'query_embedding': embed_query,
    'similarity_match_threshold': 0.4,
    'match_count': 10,
    'id_input': user_id,
    'doc_name_input': doc_name
    }).execute()

    all_search_results = []

    for search_result in vec_search_table.data:
        all_search_results.append(search_result['content']) 
    
    response = create_item_summary(all_search_results)

    timeline_json = {}
    timeline_json['title'] = {
        'text': {
            'headline': f'Generated Timeline of {doc_name}',
            'text': 'A timegraph generated summary of chronological events.'
            }
        }
    
    #timeline_json['events'] = []
    timeline_events = []

    for event in response:
        #print(event)

        timeline_events.append(
            {
                "start_date": {
                    'year': event['year'],
                    'month': event['month'],
                    'day': event['day_of_month']
                    },
                    "text": {
                        'headline': event['event']
                        }
            }
        )

    timeline_json['events'] = timeline_events

    #print(timeline_json)
    
    with timeline_container:
        timeline(timeline_json, height=700)

    #return all_search_results


def main():
    load_dotenv()

    st.set_page_config(page_title="Dashboard", page_icon=':pushpin:')

    st_supabase_client = load_supabase_client()
    
    # if user is not logged in
    if 'email' not in st.session_state or st.session_state.email == '':
        st.session_state.email = ''

        user_form = st.empty()

        with user_form.form(key='signin_form'):
            #login_form = st.form(key='signin_form', clear_on_submit=True)
            email = st.text_input(label='Enter email')
            password = st.text_input(label='Enter password', type='password')

            login = st.form_submit_button(label='Sign In')

        if login:
            session = st_supabase_client.auth.sign_in_with_password({'email': email, 'password': password})
            #print(st_supabase_client.auth) 
            st.session_state.email = email
            st.session_state.id = st_supabase_client.auth.get_session().user.id
            user_form.empty()
            success = st.success(f'Successfully logged in as {st.session_state.email}')
            time.sleep(1)
            success.empty()
    
    if st.session_state.email != '':
        logout = st.sidebar.button(label='Log Out')

        if logout:
            st.session_state.email = ''
            st_supabase_client.auth.sign_out()
        
        st.text(f'Logged in as {st.session_state.email}')

    disable_process = True

    if st.session_state.email != '':
        st.markdown("## Upload your documents here:")
        pdf_doc = st.file_uploader("")

        if pdf_doc is not None:
            disable_process = False
        
        if st.button('Upload Document', disabled=disable_process):
            with st.spinner():
                # instantiate embedding model
                embed_model = SentenceTransformerEmbeddings(model_name='sentence-transformers/gtr-t5-base')
                #embed_model = SentenceTransformerEmbeddings(model_name='nreimers/MiniLM-L6-H384-uncased')

                # 1. get text from PDFs and upload PDF file to documents_file bucket
                doc_bucket_url = upload_pdf_to_bucket(pdf_doc, st_supabase_client)
                raw_text, doc_name = get_pdf_text(pdf_doc)
                #st.write(raw_text)

                # 2. get text chunks from extracted texts
                text_chunks = get_text_chunks(raw_text)
                #st.write(text_chunks)

                 # 3. create vector store
                add_vectorstore(embed_model, text_chunks, doc_name, doc_url=doc_bucket_url, supabase_client=st_supabase_client)

                success_upload = st.container()

                with success_upload:
                    st.success(f'Uploaded {pdf_doc.name} to database!')
                    time.sleep(3)
                    success_upload.empty()

                # 4. prompt & search for timeline information
                #vec_results = vec_search(supabase_client=st_supabase_client, user_id=st.session_state.id)
                #vec_results.create_index

                #st.write(vec_results.data)

        current_uploaded_docs = st.container()

        timeline_container = st.container()

        with current_uploaded_docs:
            st.markdown('## Your current documents:')
            all_user_docs = get_user_docs(st_supabase_client, st.session_state.id)
            if all_user_docs is not None:
                st.markdown('Select a document to start building your timeline.')
                for doc_name in all_user_docs:
                    #st.button(label=f"{doc_name['doc_name']}")
                    if st.button(label=f"{doc_name['doc_name']}"):
                        generate_timeline(st_supabase_client, st.session_state.id, doc_name['doc_name'], timeline_container)
            else:
                st.write('You do not have any uploaded documents. Upload a document to start building your timelines.')
            
        #with timeline_container:
        #    st.write('Timeline container')

if __name__ == '__main__':
    main()