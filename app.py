import streamlit as st
from state import init_session

st.set_page_config(page_title="Healthcare RAG", page_icon="🩺", layout="wide")
init_session()

if not st.session_state.submitted:
    st.title("🔐 Enter API Key & Select Model")
    st.markdown("Before using the app, please provide your OpenAI credentials.")

    st.session_state.api_key = st.text_input("OpenAI API Key", type="password")
    st.session_state.model = st.selectbox("Choose Model", ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"])

    if st.button("Submit"):
        if not st.session_state.api_key:
            st.warning("You must enter an API key to continue.")
        else:
            st.session_state.submitted = True
            st.rerun()
    st.stop()

# Once authenticated
st.title("🩺 Healthcare Policy Navigator")
st.markdown("Use the sidebar or tabs to:")
st.markdown("""
- 💬 Ask questions about regulations  
- 📊 Compare rules  
- 📈 Generate insights  
""")

st.sidebar.success(f"✅ Connected to {st.session_state.model}")
