import streamlit as st
import openai
import tiktoken
import json
import numpy as np
import faiss
import re

# ---------- Session Setup ----------
def init_session():
    st.session_state.setdefault("api_key", "")
    st.session_state.setdefault("model", "gpt-4o")  # ✅ default now gpt-4o
    st.session_state.setdefault("submitted", False)
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("show_chunks", False)

# ---------- Tokenizer ----------
encoding = tiktoken.encoding_for_model("gpt-4")
def count_tokens(text: str) -> int:
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

Based on the policy context below, generate helpful recommendations.

Context:
{context}

Scenario: {query}
Recommendations:"""
}

# ---------- Context Assembly ----------
MAX_CONTEXT_TOKENS = 100000  # room for large prompt

def get_context(chunks, limit=MAX_CONTEXT_TOKENS):
    context = ""
    used = []
    for c in chunks:
        section = f"[Section: {c['section_header']}]\n{c['text']}\n"
        if count_tokens(context + section) > limit:
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

# ---------- Rule-Based Filtering ----------
def infer_query_filters(query):
    years = re.findall(r"\b(20[0-5][0-9])\b", query)
    year = years[0] if years else None

    program = None
    if "hospice" in query.lower():
        program = "hospice"
    elif "snf" in query.lower() or "skilled nursing" in query.lower():
        program = "snf"
    elif "physician" in query.lower() or "mpfs" in query.lower():
        program = "mpfs"

    rule_type = None
    if "final rule" in query.lower():
        rule_type = "final"
    elif "proposed rule" in query.lower():
        rule_type = "proposed"

    return year, program, rule_type

# ---------- Load FAISS + Metadata ----------
@st.cache_resource
def load_index():
    idx = faiss.read_index("faiss.index")
    with open("faiss_metadata.json") as f:
        meta = json.load(f)
    return idx, meta

# ---------- Embedding ----------
def embed_query(text, api_key):
    client = openai.OpenAI(api_key=api_key)
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return np.array([response.data[0].embedding], dtype="float32")

# ---------- Search with Filtering + Rerank ----------
def search_chunks(query_embedding, full_index, metadata_all, query, k=20):
    year, program, rule_type = infer_query_filters(query)

    filtered = [
        c for c in metadata_all
        if (not year or str(c["metadata"].get("year", "")).startswith(str(year)))
        and (not program or program.lower() in c["metadata"].get("title", "").lower())
        and (not rule_type or rule_type.lower() in c["metadata"].get("rule_type", "").lower())
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
