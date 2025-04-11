import streamlit as st
from state import init_session
import faiss, openai, tiktoken, json
import numpy as np

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

def embed_query(query):
    client = openai.OpenAI(api_key=st.session_state.api_key)
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=query
    )
    return np.array([response.data[0].embedding], dtype="float32")

def search_chunks(query_embedding, k=15):
    D, I = index.search(query_embedding, k)
    return [metadata[i] for i in I[0]]

def ask_gpt(prompt):
    client = openai.OpenAI(api_key=st.session_state.api_key)
    response = client.chat.completions.create(
        model=st.session_state.model,
        messages=[
            {"role": "system", "content": "You are a healthcare policy strategist."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=2500
    )
    return response.choices[0].message.content

def get_context(chunks, limit=3000):
    context = ""
    for c in chunks:
        s = f"[Section: {c['section_header']}]\n{c['text']}\n"
        if count_tokens(context + s) > limit: break
        context += s
    return context

st.title("📈 Generate Strategic Insights")

st.markdown("Examples:\n- How should hospitals prepare for hospice rule changes in 2025?\n- What should SNFs prioritize based on new QRP updates?")

scenario = st.text_input("Describe a scenario or ask for suggestions")

if scenario and st.button("Generate Insights"):
    emb = embed_query(scenario)
    chunks = search_chunks(emb)
    context = get_context(chunks)

    prompt = f"""
You are a healthcare policy strategist.

Using the information below, generate a set of **actionable recommendations** for hospitals, skilled nursing facilities, or other providers. Focus on compliance, operations, quality improvement, and financial planning.

--- CONTEXT ---
{context}
--- END CONTEXT ---

Scenario: {scenario}
"""
    with st.spinner("Thinking..."):
        output = ask_gpt(prompt)
        st.markdown("### 💡 Strategic Recommendations")
        st.markdown(output)
