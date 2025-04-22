import streamlit as st
from state import init_session

# Set wide layout and page title
st.set_page_config(page_title="RegHealth Navigator", layout="wide")

# Initialize session state
init_session()

# ---------- SIDEBAR: API KEY & MODEL ----------
st.sidebar.header("🔐 API Setup")
st.sidebar.markdown("Enter your OpenAI API key and select your model to begin.")

# Input fields stored in session_state
st.session_state.api_key = st.sidebar.text_input(
    "🔑 OpenAI API Key", 
    type="password", 
    value=st.session_state.get("api_key", "")
)

st.session_state.model = st.sidebar.selectbox(
    "🤖 Model", 
    ["gpt-4o", "gpt-4"], 
    index=["gpt-4o", "gpt-4"].index(st.session_state.get("model", "gpt-4o"))
)

# Submit button
if st.sidebar.button("✅ Submit API Key"):
    if not st.session_state.api_key:
        st.sidebar.warning("⚠️ Please enter a valid API key.")
    else:
        st.session_state.submitted = True
        st.sidebar.success(f"Connected using `{st.session_state.model}`")

# ---------- MAIN CONTENT ----------
st.title("🩺 RegHealth Navigator")
st.markdown("""
Welcome to **RegHealth Navigator** — your AI-powered assistant for navigating complex U.S. healthcare compliance rules.

Whether you're a policy analyst, compliance officer, or healthcare provider, this app helps you **explore**, **compare**, and **gain insights** from CMS rule updates.

### 🔍 What You Can Do:
- 💬 **Ask Questions** about any CMS rule and get grounded answers
- 📊 **Compare** proposed vs. final rules or changes across years
- 📈 **Generate Strategic Insights** tailored to your organization
- 📚 **Explore Regulatory Documents** and inspect rule chunks manually

Use the **sidebar** to enter your API key, then click below to begin.
""")

# ---------- NAVIGATION BUTTONS ----------
col1, col2 = st.columns(2)

with col1:
    if st.button("💬 Ask Questions"):
        st.switch_page("pages/1_💬_Ask_Questions.py")
    if st.button("📊 Compare Rules"):
        st.switch_page("pages/2_📊_Compare_Rules.py")
    if st.button("📈 Generate Insights"):
        st.switch_page("pages/3_📈_Generate_Insights.py")

with col2:
    if st.button("📚 Document Explorer"):
        st.switch_page("pages/4_📚_Document_Explorer.py")
    if st.button("🧠 Session History"):
        st.switch_page("pages/5_🧠_History.py")
