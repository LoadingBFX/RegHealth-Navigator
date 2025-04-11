import streamlit as st
from state import init_session
import faiss, openai, json, numpy as np, tiktoken

import streamlit as st
from state import init_session
init_session()

if not st.session_state.submitted:
    st.warning("Please enter your OpenAI API key and model first on the home page.")
    st.stop()


init_session()
encoding = tiktoken.encoding_for_model("gpt-4")

index = faiss.read_index("faiss.index")
with open("faiss_metadata.json", "r") as f:
    metadata = json.load(f)

def count_tokens(text): return len(encoding.encode(text))

def get_unique_options(key):
    return sorted(set(str(d["metadata"].get(key, "")).strip() for d in metadata if d["metadata"].get(key)))

def get_section_headers_filtered(year, rule_type, program):
    return sorted(set(
        d["section_header"]
        for d in metadata
        if str(d["metadata"].get("year")) == year
        and rule_type.lower() in d["metadata"].get("rule_type", "").lower()
        and program.lower() in d["metadata"].get("title", "").lower()
    ))

def ask_gpt(prompt):
    client = openai.OpenAI(api_key=st.session_state.api_key)
    response = client.chat.completions.create(
        model=st.session_state.model,
        messages=[
            {"role": "system", "content": "You are a healthcare policy comparison assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=2500
    )
    return response.choices[0].message.content

def get_context(chunks, token_limit=3000):
    context = ""
    for c in chunks:
        s = f"[Section: {c['section_header']}]\n{c['text']}\n"
        if count_tokens(context + s) > token_limit: break
        context += s
    return context

st.title("📊 Compare Two Rules Side-by-Side")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📘 Rule 1")
    y1 = st.selectbox("Year", get_unique_options("year"), key="y1")
    t1 = st.selectbox("Rule Type", get_unique_options("rule_type"), key="t1")
    p1 = st.selectbox("Program", get_unique_options("program"), key="p1")
    s1 = st.selectbox("Section (optional)", [""] + get_section_headers_filtered(y1, t1, p1), key="s1")

with col2:
    st.subheader("📘 Rule 2")
    y2 = st.selectbox("Year", get_unique_options("year"), key="y2")
    t2 = st.selectbox("Rule Type", get_unique_options("rule_type"), key="t2")
    p2 = st.selectbox("Program", get_unique_options("program"), key="p2")
    s2 = st.selectbox("Section (optional)", [""] + get_section_headers_filtered(y2, t2, p2), key="s2")

question = st.text_input("What do you want to compare?", value="What are the differences between the two rules?")

if st.button("Compare"):
    rule1 = [c for c in metadata if str(c["metadata"].get("year")) == y1 and
             t1.lower() in c["metadata"].get("rule_type", "").lower() and
             p1.lower() in c["metadata"].get("title", "").lower() and
             (s1 == "" or c["section_header"] == s1)]

    rule2 = [c for c in metadata if str(c["metadata"].get("year")) == y2 and
             t2.lower() in c["metadata"].get("rule_type", "").lower() and
             p2.lower() in c["metadata"].get("title", "").lower() and
             (s2 == "" or c["section_header"] == s2)]

    if not rule1 or not rule2:
        st.error("Could not find both rules. Please check filters.")
        st.stop()

    ctx1 = get_context(rule1)
    ctx2 = get_context(rule2)

    prompt = f"""
You are a U.S. Medicare policy expert.

Compare the two rules below. Highlight the differences in:
- payment methodologies
- reporting or quality requirements
- policy scope
- financial implications
- terminology and effective dates

Use bullet points and include section references.

--- RULE 1 ({y1} {t1} {p1}) ---
{ctx1}

--- RULE 2 ({y2} {t2} {p2}) ---
{ctx2}

Question: {question}
"""
    with st.spinner("Comparing..."):
        response = ask_gpt(prompt)
        st.markdown("### 🧠 Comparison")
        st.markdown(response)
