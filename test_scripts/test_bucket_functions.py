from dotenv import load_dotenv
from supabase import create_client
import os

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

# retrieve all files from specified bucket
#data = supabase.storage.from_("documents_file").list()
# retrieve public url for specified file (only works if bucket has only public policies)
#res = supabase.storage.from_('documents_file').get_public_url('_2024__SGCA_15.pdf')
# create and return a signed url, based on the specified url expiry (defined in seconds)
res = supabase.storage.from_('documents_file').create_signed_url('_2024__SGCA_15.pdf', 604800)
print(res)

supabase.auth.sign_out()