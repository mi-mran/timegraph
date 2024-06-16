from dotenv import load_dotenv
from supabase import create_client
import os

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

session = None

email="mi.mran@hotmail.com"
pw="password"

try:
    session = supabase.auth.sign_in_with_password({'email':email, 'password':pw})
except:
    print("Login failed")


print(session.user.email)
print(session.session.access_token)
supabase.postgrest.auth(session.session.access_token)


supabase.auth.sign_out()

#supabase.auth.sign_up({'email': email, 'password': pw})
