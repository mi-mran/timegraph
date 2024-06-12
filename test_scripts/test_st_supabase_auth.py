from st_supabase_connection import SupabaseConnection
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

# create supabase connection client
st_supabase_client = st.connection(
                name="timegraph",
                type=SupabaseConnection,
                ttl=None,
                url=os.environ.get("SUPABASE_URL"), # remove once added to streamlit cloud env variables
                key=os.environ.get("SUPABASE_KEY"), # remove once added to streamlit cloud env variables
            )

# sign in with email and password auth
st_supabase_client.auth.sign_in_with_password(dict(email='', password=''))
print(st_supabase_client.auth.get_session().access_token)

#print(st_supabase_client)
st_supabase_client.auth.sign_out()