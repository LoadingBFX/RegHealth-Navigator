import streamlit as st
from state import init_session, sidebar_api_setup

init_session()
sidebar_api_setup()  # ✅ Add sidebar support

st.title("🧠 History Viewer")
st.markdown("This page shows all previous queries and answers from your current session.")

if not st.session_state.history:
    st.info("No queries have been made yet.")
    st.stop()

# Reverse order to show most recent first
for i, entry in enumerate(reversed(st.session_state.history), 1):
    title = None

    # Dynamically determine the title based on available keys
    if "q" in entry:
        title = f"💬 Q: {entry['q'][:80]}"
    elif "comparison_query" in entry:
        title = f"📊 Compare: {entry['comparison_query'][:80]}"
    elif "scenario" in entry:
        title = f"📈 Insight: {entry['scenario'][:80]}"
    else:
        title = f"📝 Entry {i}"

    with st.expander(f"{title}"):
        for key, value in entry.items():
            st.markdown(f"**{key.capitalize().replace('_', ' ')}**")
            st.markdown(value)
            st.markdown("---")
