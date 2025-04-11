import streamlit as st

def init_session():
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""
    if "model" not in st.session_state:
        st.session_state.model = "gpt-4"
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
