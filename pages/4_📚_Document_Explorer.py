import streamlit as st
import openai
import faiss
import json
import numpy as np

from state import (
    init_session, sidebar_api_setup,  # ✅ Include sidebar_api_setup
    load_index, embed_query, count_tokens
)

# ---------- Setup ----------
init_session()
sidebar_api_setup()  # ✅ Enable sidebar API key input + connection status

if not st.session_state.submitted:
    st.warning("Please enter your OpenAI API key and model first in the sidebar.")
    st.stop()

# ---------- Page UI ----------
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

# ---------- Load FAISS and Metadata ----------
index, metadata = load_index()

# ---------- Filter UI ----------
programs = sorted(set(doc["metadata"].get("program") for doc in metadata if doc["metadata"].get("program")))
program = st.selectbox("🏥 Program", programs)

filtered_by_program = [doc for doc in metadata if doc["metadata"].get("program") == program]

years = sorted(set(doc["metadata"]["year"] for doc in filtered_by_program if "year" in doc["metadata"]))
year = st.selectbox("📅 Year", years)

filtered_by_year = [doc for doc in filtered_by_program if doc["metadata"]["year"] == year]

rule_types = sorted(set(doc["metadata"]["rule_type"] for doc in filtered_by_year if "rule_type" in doc["metadata"]))
rule_type = st.selectbox("📄 Rule Type", rule_types)

filtered_docs = [
    doc for doc in filtered_by_year
    if doc["metadata"]["rule_type"] == rule_type
]

if not filtered_docs:
    st.error("❌ No documents available with selected filters.")
    st.stop()

# ---------- Prompt Input ----------
st.markdown("### 🔎 Find relevant section headers")
with st.form("section_lookup"):
    user_query = st.text_input("What are you looking for?", placeholder="e.g. hospice wage index update")
    submitted = st.form_submit_button("🔍 Submit")

# ---------- Vector Search ----------
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

        # Save results to session
        st.session_state.top_sections = top_sections

# ---------- Section Selector + Display ----------
if "top_sections" in st.session_state and st.session_state.top_sections:
    section_labels = [
        f"[{doc['section_header']}] – {doc['metadata']['title']}" for doc in st.session_state.top_sections
    ]

    selected_label = st.selectbox("📁 Select a section to view", section_labels, key="section_viewer")
    selected_index = section_labels.index(selected_label)
    selected_doc = st.session_state.top_sections[selected_index]

    st.markdown("### 📖 Section Text")
    st.markdown(f"**Section:** {selected_doc['section_header']}")
    st.markdown(f"**Rule:** {selected_doc['metadata']['title']} ({selected_doc['metadata']['rule_type'].title()}, {selected_doc['metadata']['year']})")
    st.markdown("---")
    st.markdown(selected_doc["text"])
