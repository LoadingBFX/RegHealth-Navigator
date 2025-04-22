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
    # -------------------------------
    # ASK A QUESTION
    # -------------------------------
    "ask": """
You are a compliance assistant helping users understand CMS healthcare regulations.

Follow this process:
1. Identify the regulation topics referenced in the user's question.
2. Thoroughly read the provided context.
3. Extract and explain any relevant policy details.
4. Answer the question in full sentences using only the provided context.
5. If the answer is not found, say so clearly.

Rules:
- NEVER make up content.
- NEVER speculate beyond the context.
- Use professional, precise, and regulatory tone.

Context:
{context}

User Question:
{query}

Answer:
""",

    # -------------------------------
    # COMPARE RULES
    # -------------------------------
    "compare": """
You are a senior healthcare policy analyst comparing two versions of a CMS rule.

Reasoning process:
1. Identify the topic and policy focus of the comparison.
2. Analyze each rule section independently.
3. Explain what each rule says in full detail.
4. Compare them point-by-point, highlighting differences and their significance.
5. Focus on operational or compliance implications.

Constraints:
- Use only information from the provided rule text.
- No speculation or assumptions.
- Avoid lists. Write in structured, analytical paragraphs.
- Tone should match the formality expected by compliance officers and legal reviewers.

--- Rule 1 ---
{context1}

--- Rule 2 ---
{context2}

User Query:
{query}

Detailed Comparison:
""",

    # -------------------------------
    # GENERATE STRATEGIC INSIGHTS
    # -------------------------------
    "insight": """
You are a healthcare compliance strategist advising organizations on how to respond to CMS policy updates.

Process:
1. Identify the strategic or operational question being asked.
2. Review the full context of the policy changes or rule sections.
3. Interpret and analyze how the rules affect compliance, reporting, care delivery, or staffing.
4. Provide high-level insight into how organizations should think about this rule.

Expectations:
- Full sentences and well-structured analysis.
- Use terminology familiar to compliance directors and operations leads.
- Include reasoning behind each conclusion.
- Avoid speculative content.

Context:
{context}

Scenario:
{query}

Strategic Insight:
""",

    # -------------------------------
    # FOLLOW-UP RECOMMENDATIONS (after insight)
    # -------------------------------
    "recommendations": """
Based on the above analysis, provide a clear and actionable list of recommendations for healthcare organizations.

Requirements:
- Each recommendation should be specific and relevant to the rule.
- Each item must include:
    - **Bolded Title**
    - A short one-line summary
    - A detailed explanation (2–3 sentences minimum)
    - If applicable, who in the organization it applies to (e.g., Compliance Officer, Finance Team)

Audience:
- Policy directors
- Regulatory compliance teams
- Operational leaders

Insight:
{insight}

Recommendations:
"""
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

# ---------- Sidebar API Setup ----------
def sidebar_api_setup():
    with st.sidebar:
        st.markdown("### 🔐 API Setup")
        st.markdown("Enter your OpenAI API key and select your model to begin.")

        st.session_state.api_key = st.text_input(
            "🔑 OpenAI API Key", 
            value=st.session_state.get("api_key", ""), 
            type="password", 
            key="sidebar_api_key"
        )

        st.session_state.model = st.selectbox(
            "🤖 Model", 
            ["gpt-4o", "gpt-4"], 
            index=["gpt-4o", "gpt-4"].index(st.session_state.get("model", "gpt-4o")),
            key="sidebar_model"
        )

        if st.button("✅ Submit API Key", key="submit_sidebar"):
            if st.session_state.api_key:
                st.session_state.submitted = True
            else:
                st.session_state.submitted = False

        if st.session_state.get("submitted", False) and st.session_state.get("api_key"):
            st.success(f"🟢 Connected using `{st.session_state.model}`")
        else:
            st.warning("🔴 Not connected")
