import streamlit as st
from dotenv import load_dotenv
import os
import time
from supabase import create_client
from st_supabase_connection import SupabaseConnection

@st.cache_resource
def load_supabase_client():
    conn = st.connection("supabase", type=SupabaseConnection)
    st_supabase_client = create_client(supabase_url=os.environ.get("SUPABASE_URL"), supabase_key=os.environ.get("SUPABASE_KEY"))
    
    return st_supabase_client

def main():
    load_dotenv()

    st.set_page_config(page_title="Create Account", page_icon=':pushpin:')

    st.text('Create a free account')

    if 'email' not in st.session_state or st.session_state.email == '':
        # if email session state is not set or not instantiated, set it to empty str
        st.session_state.email = ''
    
        st_supabase_client = load_supabase_client()

        signup_form = st.form(key='signup_form', clear_on_submit=True)
        new_user_email = signup_form.text_input(label='Enter email address')
        new_user_pw = signup_form.text_input(label='Enter password', type='password')
        new_user_pw_confirm = signup_form.text_input(label='Re-enter password', type='password')
        signup = signup_form.form_submit_button(label='Sign Up')

        if signup:
            if '' in [new_user_email, new_user_pw, new_user_pw_confirm]:
                # missing email / password check
                err = st.error('Some fields are missing.')
                time.sleep(3)
                err.empty()
            else:
                if new_user_pw != new_user_pw_confirm:
                    # password confirmation mismatch check
                    err = st.error('Password does not match!')
                else:
                    # sign up with supabase auth
                    st_supabase_client.auth.sign_up({'email': new_user_email, 'password': new_user_pw_confirm})
                    # set email session state
                    st.session_state.email = new_user_email
                    success = st.success(f'Successfully created your account! {new_user_email}')
                    del new_user_email, new_user_pw, new_user_pw_confirm
                    time.sleep(5)
                    success.empty()
    else:    
        # if user is already signed in, display link to dashboard instead
        st.text(f'Signed in with account: {st.session_state.email}')
        st.markdown(f"Go to [dashboard](https://timegraph.streamlit.app/Dashboard).")
                    

            

    

if __name__ == '__main__':
    main()