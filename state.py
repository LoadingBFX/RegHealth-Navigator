import streamlit as st
import openai
import tiktoken
import json
import numpy as np
import faiss
import re
import os

# ---------- Session Setup ----------
def init_session():
    st.session_state.setdefault("api_key", "")
    st.session_state.setdefault("model", "gpt-4o")
    st.session_state.setdefault("submitted", False)
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("show_chunks", False)

# ---------- Tokenizer Setup ----------
ENCODING_MAP = {
    "gpt-4": tiktoken.encoding_for_model("gpt-4"),
    "gpt-4o": tiktoken.encoding_for_model("gpt-4")
}

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    encoding = ENCODING_MAP.get(model, ENCODING_MAP["gpt-4"])
    return len(encoding.encode(text))

# ---------- Prompt Templates ----------
PROMPTS = {
    "ask": """Use the context below to answer the question as clearly and accurately as possible. If the answer is not in the context, say so.

Context:
{context}

Question: {query}
Answer:""",
    
    "compare": """You are comparing two regulation documents.

Use the following context to answer the user's question clearly. Only use what is in the provided text.

--- Document 1 ---
{context1}

--- Document 2 ---
{context2}

Question: {query}
Answer:""",

    "insight": """You are advising a healthcare organization.

Based on the policy context below, generate helpful, actionable recommendations.

Context:
{context}

Scenario: {query}
Recommendations:"""
}

# ---------- Load FAISS + Metadata ----------
@st.cache_resource
def load_index():
    index_path = os.path.join("rag_data", "faiss.index")
    metadata_path = os.path.join("rag_data", "faiss_metadata.json")

    if not os.path.exists(index_path) or not os.path.exists(metadata_path):
        st.error("❌ Could not find FAISS index or metadata in `rag_data` folder.")
        st.stop()

    idx = faiss.read_index(index_path)
    with open(metadata_path, "r") as f:
        meta = json.load(f)
    return idx, meta

# ---------- Dynamic Metadata Filters ----------
def get_available_filter_values(metadata):
    years = sorted(set(str(doc["metadata"].get("year")) for doc in metadata if doc["metadata"].get("year")))
    programs = sorted(set(doc["metadata"].get("program", "").lower() for doc in metadata if doc["metadata"].get("program")))
    rule_types = sorted(set(doc["metadata"].get("rule_type", "").lower() for doc in metadata if doc["metadata"].get("rule_type")))
    return years, programs, rule_types

def infer_query_filters(query, metadata):
    years, programs, rule_types = get_available_filter_values(metadata)

    # Match year
    found_years = re.findall(r"\b(20[0-5][0-9])\b", query)
    year = next((y for y in found_years if y in years), None)

    # Match program
    query_lower = query.lower()
    program = next((p for p in programs if p in query_lower), None)

    # Match rule_type
    rule_type = None
    if "final" in query_lower and "final" in rule_types:
        rule_type = "final"
    elif "proposed" in query_lower and "proposed" in rule_types:
        rule_type = "proposed"

    return year, program, rule_type

# ---------- Embedding ----------
def embed_query(text, api_key):
    client = openai.OpenAI(api_key=api_key)
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return np.array([response.data[0].embedding], dtype="float32")

# ---------- Context Assembly ----------
MAX_CONTEXT_TOKENS = 100000

def get_context(chunks, limit=MAX_CONTEXT_TOKENS, model="gpt-4o") -> tuple[str, list]:
    context = ""
    used = []
    for c in chunks:
        section = f"[Section: {c['section_header']}]\n{c['text']}\n"
        if count_tokens(context + section, model=model) > limit:
            break
        context += section
        used.append(c)
    return context, used

def render_chunks(chunks):
    with st.expander("📄 Preview Chunks Used", expanded=False):
        for c in chunks:
            st.markdown(f"**[Section: {c['section_header']}]**")
            meta = c.get("metadata", {})
            st.markdown(
                f"`Year:` {meta.get('year', '?')} | "
                f"`Type:` {meta.get('rule_type', '?')} | "
                f"`Title:` {meta.get('title', '?')}`"
            )
            st.markdown(c["text"])
            st.markdown("---")

# ---------- Search with Filtering + Rerank ----------
def search_chunks(query_embedding, full_index, metadata_all, query, k=20):
    year, program, rule_type = infer_query_filters(query, metadata_all)

    filtered = [
        c for c in metadata_all
        if (not year or str(c["metadata"].get("year", "")).startswith(str(year)))
        and (not program or program.lower() == c["metadata"].get("program", "").lower())
        and (not rule_type or rule_type.lower() == c["metadata"].get("rule_type", "").lower())
    ]

    if not filtered:
        filtered = metadata_all  # fallback

    subset_texts = [doc["text"] for doc in filtered]
    client = openai.OpenAI(api_key=st.session_state.api_key)
    response = client.embeddings.create(model="text-embedding-ada-002", input=subset_texts)
    vectors = [r.embedding for r in response.data]
    matrix = np.array(vectors).astype("float32")

    index = faiss.IndexFlatL2(len(matrix[0]))
    index.add(matrix)
    D, I = index.search(query_embedding, min(k, len(matrix)))
    return [filtered[i] for i in I[0] if i < len(filtered)]
