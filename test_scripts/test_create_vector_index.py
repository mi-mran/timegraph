from dotenv import load_dotenv
from supabase import create_client
import os
import ollama

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

email=""
pw=""

try:
    session = supabase.auth.sign_in_with_password({'email':email, 'password':pw})
except:
    print("Login failed")

supabase.postgrest.auth(session.session.access_token)

#vec_db = supabase.table('documents').select('*').eq('user_id', f'{session.session.user.id}').execute()
#supabase.auth.get_session().user.id
vec_index_creation = """CREATE INDEX ON documents USING hnsw (embedding_vector vector_cosine_ops)"""

#test = supabase.rpc('create_vec_index', {'id_input': supabase.auth.get_session().user.id, 'doc_name_input': "[2024] SGCA 15.pdf"})
#get_one_record = supabase.table('documents').select('*').execute()

#for record in get_one_record.data:
#    embed_vector = record['embedding_vector'].strip('][').split(',')
#    embed_vector = [float(i) for i in embed_vector]
#    print(len(embed_vector))

#print(get_one_record.data)
#print('Successfully created vector index.')
#print(vec_db.data[0].keys())

#query = "Key dates with format: date month year."
query = "dates and events"
from langchain_community.embeddings import SentenceTransformerEmbeddings
embed_model = SentenceTransformerEmbeddings(model_name='sentence-transformers/gtr-t5-base')
embed_query = embed_model.embed_query(query)

vec_search_table = supabase.rpc('vector_search', {
    'query_embedding': embed_query,
    'similarity_match_threshold': 0.5,
    'match_count': 10,
    'id_input': supabase.auth.get_session().user.id,
    'doc_name_input': "[2024] SGCA 15.pdf"
}).execute()

#for search_result in vec_search_table.data:
#    print(search_result['content'])
#print(vec_search_table.data)

supabase.auth.sign_out()

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

    response = ollama.generate(model='llama3', prompt=raw_prompt)
    
    response = response["response"]
    response = response.replace("```json", "").replace("```", "").replace("\n", " ").strip()
    
    return response

all_search_results = []

for search_result in vec_search_table.data:
    all_search_results.append(search_result['content']) 

overall_results = []

response = create_item_summary(all_search_results)

#for search_result in vec_search_table.data:
#    item = {}
#    item['original_text'] = search_result
#    item['llama_response'] = create_item_summary(search_result['content'])
#    overall_results.append(item)

    #print(item)

print(response)