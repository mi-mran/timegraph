# extracting court proceedings as str
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes, convert_from_path
import re

pdf_path = "/Users/imran/Downloads/sg_judgements/[2024] SGCA 15.pdf"
pdf_name = "[2024] SGCA 15.pdf"
text_overall = ""

pdf = convert_from_path(pdf_path, fmt='jpeg', dpi=150)

for page_num, page in enumerate(pdf):
    # left, top, right, bottom
    # these coordinates work with SG court proceedings saved as PDFs
    # coordinates also correspond to the dpi used
    page = page.crop((0, 0, page.width, 1500))
    
    text = pytesseract.image_to_string(page, config="--psm 1 --oem 1")
    if not re.search('table of content', text, re.IGNORECASE):
        text_overall += text


# creating text chunks
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1024,
        chunk_overlap = 200,
        length_function = len,
    )

chunks = text_splitter.split_text(text_overall)

#for chunk in chunks:
#    print(len(chunk))

# creating vectorstore
from langchain_community.embeddings import SentenceTransformerEmbeddings
# FAISS only for local vectorstore testing
#from langchain_community.vectorstores import FAISS

embed_model = SentenceTransformerEmbeddings(model_name='sentence-transformers/gtr-t5-base')
embeddings = embed_model.embed_documents(chunks)
#vectorstore = FAISS.from_texts(texts=chunks, embedding=embed_model)

#print(len(chunks), len(embeddings))

# upload embeddings to supabase
from dotenv import load_dotenv
from supabase import create_client
from itertools import product
import os

def add_embeddings_to_documents_table(supabase, doc_name, chunks, embeddings):
    update_list = []

    for chunk, embedding in product(chunks, embeddings):
        value = {
            'doc_name': doc_name,
            'content': chunk,
            'embedding_vector': embedding,
            # file_url should be retrieved from the documents_file bucket from supabase for documents. setting static url for first test document
            'file_url': 'https://qhefebfqfcpuzdgcftht.supabase.co/storage/v1/object/sign/documents_file/_2024__SGCA_15.pdf?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJkb2N1bWVudHNfZmlsZS9fMjAyNF9fU0dDQV8xNS5wZGYiLCJpYXQiOjE3MTg1NDM5MjYsImV4cCI6MTcxOTE0ODcyNn0.7Sy7NQiHe4x_Sg7V2h9ZOGWy5ixWL-D6PvSnBuL218Q&t=2024-06-16T13%3A18%3A46.383Z'
                 }
        update_list.append(value)
    
    data = supabase.table('documents').insert(update_list).execute()
    print('Uploaded to supabase!')

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

session = None

email=""
pw=""

try:
    session = supabase.auth.sign_in_with_password({'email':email, 'password':pw})
except:
    print("Login failed")

# set user's access token to session
supabase.postgrest.auth(session.session.access_token)

# add embeddings to supabase db for specified document
add_embeddings_to_documents_table(supabase, doc_name=pdf_name, chunks=chunks, embeddings=embeddings)

# checking for single row
get_one_record = supabase.table('documents').select('*').limit(1).execute()

# embedding string
for record in get_one_record.data:
    print(len(record['embedding_vector']))

supabase.auth.sign_out()
