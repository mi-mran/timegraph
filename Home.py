import streamlit as st
from dotenv import load_dotenv
#from PyPDF2 import PdfReader
import pytesseract
from pdf2image import convert_from_bytes
from langchain.text_splitter import RecursiveCharacterTextSplitter
#from langchain_community.embeddings import HuggingFaceInstructEmbeddings
#from sentence_transformers import SentenceTransformer
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS
import ollama

import os


def main():
    load_dotenv()

    if "client" not in st.session_state:
        st.session_state["client"] = None
    else:
        st_supabase_client = st.session_state["client"]

    generic_linebreak = """
    <br/>
    """

    st.set_page_config(page_title="timegraph", page_icon=':pushpin:', initial_sidebar_state='collapsed')

    st.image('assets/timegraph-high-resolution-logo-black-transparent.svg')
    st.html(generic_linebreak)
    st.markdown("##### Summarising timelines from your documents has never been easier.")
    st.html(generic_linebreak)
    
    links_section = """
    <p align="left">
      <a href="#key-features">Key Features</a> •
      <a href="#how-to-use">How To Use (for buildclub demo)</a> •
      <a href="#notes">Notes</a> •
      <a href="#future-development">Future Development</a>
    </p>
    """

    st.html(links_section)

    st.markdown("## Key Features")
    st.markdown("* Upload your own documents and watch as the timeline auto-generates.")
    st.markdown("* Customise the start-end range and keywords to be searched. (coming soon!)")
    st.markdown("* Reference your document right from the timeline. (coming soon!)")

    st.image('assets/timegraph-demo.gif')

    st.markdown("## How to Use")
    st.markdown("1. To get started, <a href='timegraph.streamlit.app/Dashboard' target='_self'>sign up</a> for an account (*disabled for buildclub demo, login only*).", unsafe_allow_html=True)
    
    buildclub_demo_creds = "<div style='padding: 15px; border: 1px solid transparent; border-color: transparent; margin-bottom: 20px; border-radius: 4px; color: #31708f; background-color: #d9edf7; border-color: #bce8f1;'>For buildclub demo users, please use the following login credentials: <br/> Email: buildclub@demo.com <br/> Password: password</div>"
    st.html(buildclub_demo_creds)

    st.markdown("2. Verify your account via an email verification.")
    st.markdown("3. Upload your document. (*Only single document uploads supported at this time. Multi-doc support coming soon!*)")
    st.markdown("4. Grab a coffee while you wait for the hardworking gnomes work their magic.")
    st.markdown("5. Watch your timeline come to life, with links to each event in your document.")

    st.markdown("## Notes")
    st.markdown("timegraph is currently a work in progress and we would love to hear your feedback (whether you're a buildclub judge or not!). We believe in building tools that automate menial workflows, so that users can better focus their time on more important, analytical tasks. Thus far, we have spoken to paralegals and academics on the problems they face with structuring a coherent timeline (ie. fact-finding) when presented with large documents. We would like to hear from you if you have any feedback on how we can expand our use cases, or introducing additional functionalities that you would love to see.")
    st.markdown("Fill up the feedback form with your thoughts (or if you just wanna chat, we're happy to meet new peeps too!)")
    st.markdown("- timegraph team")

    st.markdown("## Future Development")
    st.markdown("We are far from a finished product and here are some of the features that we intend to develop in the near future:")
    st.checkbox("Improve the UI and UX! Most definitely something to be worked on.")
    st.checkbox("Include support for a single timeline from multiple documents.")
    st.checkbox("Allow multiple document filetypes.")
    st.checkbox("Deploy local, on-prem solutions for entities with privacy/security concerns.")
    st.checkbox("Model fine-tuning with LoRA via unsloth for separate network heads per use case.")

    #st.markdown(f"Client state: {st.session_state["client"]}")

    #st.markdown("### Get started")
    #with st.container(border=True):
    #    st.markdown("Ready to create succint, accurate timelines? Upload your document(s) and watch the magic happen!")

    #with st.sidebar:
    #    pass

if __name__ == '__main__':
    #os.environ['KMP_DUPLICATE_LIB_OK']='True'
    main()