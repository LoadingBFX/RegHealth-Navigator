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

# Load data
index = faiss.read_index("faiss.index")
with open("faiss_metadata.json", "r") as f:
    metadata = json.load(f)

# Count tokens
def count_tokens(text): return len(encoding.encode(text))

# Embedding
def embed_query(query):
    client = openai.OpenAI(api_key=st.session_state.api_key)
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=query
    )
    return np.array([response.data[0].embedding], dtype="float32")

# Search
def search_chunks(query_embedding, k=12):
    D, I = index.search(query_embedding, k)
    return [metadata[i] for i in I[0]]

# GPT
def ask_gpt(prompt):
    client = openai.OpenAI(api_key=st.session_state.api_key)
    response = client.chat.completions.create(
        model=st.session_state.model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant who explains U.S. healthcare policies clearly."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=2500
    )
    return response.choices[0].message.content

# UI
st.title("💬 Ask a Question")
st.markdown("Ask detailed questions about healthcare policy. Try:")
st.markdown("""
- *What are the 2025 SNF payment updates?*
- *How is the hospice cap adjusted this year?*
- *What's new in quality reporting for MPFS?*
""")

query = st.text_input("Your question")

if query and st.button("Get Answer"):
    with st.spinner("Thinking..."):
        emb = embed_query(query)
        chunks = search_chunks(emb)
        context = ""
        for c in chunks:
            s = f"[Section: {c['section_header']}]\n{c['text']}\n"
            if count_tokens(context + s) > 5000: break
            context += s

        prompt = f"""
You are a U.S. healthcare regulation expert.

Use the context below to answer the user's question clearly, including section references and relevant financial, administrative, or clinical details.

--- BEGIN CONTEXT ---
{context}
--- END CONTEXT ---

User Question: {query}
"""
        output = ask_gpt(prompt)
        st.markdown("### 🧠 Answer")
        st.markdown(output)
