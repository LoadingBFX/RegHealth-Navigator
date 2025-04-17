import streamlit as st
from state import init_session

st.set_page_config(page_title="RegHealth Navigator", layout="wide")
init_session()

# ---------- Title & API Setup ----------
st.title("🩺 RegHealth Navigator")

with st.form("setup_form", clear_on_submit=False):
    st.session_state.api_key = st.text_input("🔑 OpenAI API Key", type="password")
    st.session_state.model = st.selectbox("🤖 Choose model", ["gpt-4o"])
    submitted = st.form_submit_button("Submit")

if submitted:
    if not st.session_state.api_key:
        st.warning("❗ Please enter a valid API key.")
    else:
        st.session_state.submitted = True
        st.success("✅ API key saved. You may now use the app.")

# ---------- Detailed Introduction ----------
st.markdown("""
Welcome to **RegHealth Navigator** — your personalized platform for exploring and understanding U.S. **healthcare compliance regulations** with the power of advanced AI.

Whether you're a healthcare administrator, policy analyst, compliance officer, or provider, this app helps you make sense of complex CMS rules and changes across years, programs, and rule types.

### 🔍 What you can do:

- 💬 **Ask Questions**  
  Ask natural-language questions about proposed or final CMS rules. The AI retrieves relevant sections and provides grounded, accurate answers based on regulatory documents.

- 📊 **Compare Rules**  
  Compare how a rule has changed across years, or between proposed and final versions. See side-by-side summaries highlighting key differences in wording, scope, or policy focus.

- 📈 **Generate Strategic Insights**  
  Enter a scenario (e.g., “How should SNFs prepare for the 2025 Final Rule?”) and receive tailored recommendations based on regulatory context.

- 📚 **Explore Documents**  
  Browse and filter regulation content by year, program, rule type, and section header. Search for specific topics and inspect the source text used by the AI.

Use the **sidebar** or the **buttons below** to explore each feature.
""")

# ---------- Feature Buttons ----------
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

# ---------- Sidebar Status ----------
if st.session_state.submitted:
    st.sidebar.success(f"✅ Connected to OpenAI: `{st.session_state.model}`")
else:
    st.sidebar.warning("🔐 Please enter your OpenAI API key to begin.")
