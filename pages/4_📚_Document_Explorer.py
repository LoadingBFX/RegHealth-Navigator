import streamlit as st
from state import (
    init_session, load_index, embed_query, count_tokens
)
import openai
import numpy as np
import faiss

# --- Setup ---
init_session()
if not st.session_state.submitted:
    st.warning("Please enter your OpenAI API key and model first.")
    st.stop()

st.title("📚 Document Explorer")
st.markdown("Browse and inspect indexed regulation chunks by metadata.")

with st.expander("💡 Example Prompts", expanded=False):
    st.markdown("""
- Where can I find hospice wage index updates?
- Show me sections about SNF QRP requirements.
- Where does CMS discuss SDOH in hospice rules?
- What are the new quality measures for MPFS?
- Find the section on in-person visit requirements.
""")

# --- Load Metadata ---
index, metadata = load_index()

# --- Helper Functions ---
def get_unique(metadata, field, condition=None):
    return sorted(set(
        c["metadata"][field]
        for c in metadata
        if field in c["metadata"] and (condition is None or condition(c))
    ))

def get_years_for_program(program):
    return get_unique(metadata, "year", lambda c: c["metadata"].get("program") == program)

def get_rule_types(program, year):
    return get_unique(metadata, "rule_type", lambda c: c["metadata"].get("program") == program and c["metadata"].get("year") == year)

# --- Filter UI ---
programs = get_unique(metadata, "program")
program = st.selectbox("📊 Program", programs)

years = get_years_for_program(program)
year = st.selectbox("📅 Year", years)

rule_types = get_rule_types(program, year)
rule_type = st.selectbox("📄 Rule Type", rule_types)

filtered_docs = [
    doc for doc in metadata
    if doc["metadata"].get("program") == program
    and doc["metadata"].get("year") == year
    and doc["metadata"].get("rule_type") == rule_type
]

if not filtered_docs:
    st.error("❌ No documents available with selected filters.")
    st.stop()

# --- Prompt Input + Submit Button ---
st.markdown("### 🔎 Find relevant section headers")
with st.form("section_lookup"):
    user_query = st.text_input("What are you looking for?", placeholder="e.g. hospice wage index update")
    submitted = st.form_submit_button("🔍 Submit")

if submitted and user_query:
    with st.spinner("Finding most relevant sections..."):
        query_vec = embed_query(user_query, st.session_state.api_key)

        texts = [doc["text"] for doc in filtered_docs]
        headers = [doc["section_header"] for doc in filtered_docs]

        client = openai.OpenAI(api_key=st.session_state.api_key)
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=texts
        )
        vectors = [r.embedding for r in response.data]
        matrix = np.array(vectors).astype("float32")

        temp_index = faiss.IndexFlatL2(len(matrix[0]))
        temp_index.add(matrix)
        D, I = temp_index.search(query_vec, 5)

        top_sections = [filtered_docs[i] for i in I[0] if i < len(filtered_docs)]

        if not top_sections:
            st.error("❌ No matching sections found.")
            st.stop()

        section_labels = [
            f"[{doc['section_header']}] – {doc['metadata']['title']}" for doc in top_sections
        ]

        selected_label = st.selectbox("📁 Select a section to view", section_labels)

        if selected_label:
            index_selected = section_labels.index(selected_label)
            doc = top_sections[index_selected]

            st.markdown("### 📖 Section Text")
            st.markdown(f"**Section:** {doc['section_header']}")
            st.markdown(f"**Rule:** {doc['metadata']['title']} ({doc['metadata']['rule_type'].title()}, {doc['metadata']['year']})")
            st.markdown("---")
            st.markdown(doc["text"])
