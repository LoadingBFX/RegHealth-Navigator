import streamlit as st
from state import init_session

init_session()
if not st.session_state.submitted:
    st.warning("Please enter your OpenAI API key and model first.")
    st.stop()

st.title("🧠 History Viewer")
st.markdown("This page shows all previous queries and answers from your current session.")

if not st.session_state.history:
    st.info("No history yet. Ask a question, compare rules, or generate insights to get started.")
    st.stop()

for i, entry in enumerate(reversed(st.session_state.history)):
    with st.expander(f"🔹 {len(st.session_state.history)-i}. {entry['q'][:80]}..."):
        st.markdown("**📝 Question:**")
        st.markdown(entry["q"])
        st.markdown("---")
        st.markdown("**🤖 Answer:**")
        st.markdown(entry["a"])
