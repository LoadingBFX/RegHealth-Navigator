import streamlit as st
from state import (
    init_session, load_index, embed_query, search_chunks,
    get_context, PROMPTS, render_chunks, count_tokens
)
import openai
import json
import re

MODEL_TOKEN_LIMITS = {
    "gpt-4": (8192, 3000),
    "gpt-4o": (128000, 16384)
}

init_session()
if not st.session_state.submitted:
    st.warning("Please enter your OpenAI API key and model first.")
    st.stop()

st.title("💬 Ask a Question")
st.markdown("Ask any question about CMS rules. Relevant sections will be retrieved and used to generate an answer.")

with st.expander("💡 Example Questions", expanded=False):
    st.markdown("""
- What are the hospice payment updates in the 2025 final rule?
- What QRP requirements were finalized for SNFs in 2024?
- How is the wage index calculated in the 2022 proposed rule?
""")

query = st.text_input("Your question", placeholder="e.g. What did CMS finalize about SNF QRP reporting in 2025?")
show_chunks = st.checkbox("📄 Show chunks used", value=False)
submit_clicked = st.button("Get Answer")

if query and submit_clicked:
    with st.spinner("🤖 Step 1: Interpreting your question..."):
        client = openai.OpenAI(api_key=st.session_state.api_key)
        clarify_prompt = f"""
You are an assistant that extracts metadata from user queries about CMS policy rules.

Extract as JSON with the following fields:
- year
- program (e.g. hospice, snf, mpfs)
- rule_type (proposed or final)
- topic (short description of the main subject)

User question:
{query}

Return only the JSON.
"""
        clarify_response = client.chat.completions.create(
            model=st.session_state.model,
            messages=[{"role": "user", "content": clarify_prompt}],
            temperature=0,
            max_tokens=500
        )
        clarify_raw = clarify_response.choices[0].message.content.strip()
        if clarify_raw.startswith("```json"):
            clarify_raw = clarify_raw.strip("```json").strip("```").strip()
        elif clarify_raw.startswith("```"):
            clarify_raw = clarify_raw.strip("```").strip()

        try:
            extracted = json.loads(clarify_raw)
        except:
            match = re.search(r"\{.*\}", clarify_raw, re.DOTALL)
            if match:
                try:
                    extracted = json.loads(match.group())
                except:
                    st.error(f"⚠️ Couldn't parse metadata. GPT returned:\n```\n{clarify_raw}\n```")
                    st.stop()
            else:
                st.error(f"⚠️ Couldn't parse metadata. GPT returned:\n```\n{clarify_raw}\n```")
                st.stop()

        st.markdown(f"🧠 Interpreted query as: `{extracted}`")

    with st.spinner("📚 Step 2: Retrieving relevant rule text..."):
        index, metadata = load_index()
        filtered = [
            doc for doc in metadata
            if (not extracted.get("year") or str(doc["metadata"].get("year")) == str(extracted["year"]))
            and (not extracted.get("program") or extracted["program"].lower() in doc["metadata"].get("title", "").lower())
            and (not extracted.get("rule_type") or extracted["rule_type"].lower() in doc["metadata"].get("rule_type", "").lower())
        ]

        if not filtered:
            st.warning("⚠️ No matching documents found using interpreted metadata. Falling back to all documents.")
            filtered = metadata  # fallback

        query_vec = embed_query(query, st.session_state.api_key)
        top_chunks = search_chunks(query_vec, index, filtered, query=query, k=30)
        context, used_chunks = get_context(top_chunks, limit=100000)

        if not used_chunks:
            st.error("❌ No relevant information found to answer this question.")
            st.stop()

        if show_chunks:
            render_chunks(used_chunks)

    with st.spinner("🧠 Step 3: Generating detailed answer..."):
        prompt = PROMPTS["ask"].format(context=context, query=query)
        model = st.session_state.model
        prompt_tokens = count_tokens(prompt)
        model_limit, max_completion = MODEL_TOKEN_LIMITS.get(model, (8192, 3000))
        max_output_tokens = max(500, min(max_completion, model_limit - prompt_tokens - 500))

        st.markdown(f"ℹ️ Model: `{model}` | Prompt: `{prompt_tokens}` tokens | Max output: `{max_output_tokens}`")

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant answering policy questions based on retrieved context only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=max_output_tokens
        )
        answer = response.choices[0].message.content
        st.markdown("### 🧠 Full Answer")
        st.markdown(answer)

    with st.spinner("📄 Step 4: Summarizing the answer..."):
        summary_prompt = f"""
Summarize the following policy answer in simpler language. Highlight key implications for healthcare providers.

Answer:
{answer}

Summary:
"""
        summary_response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.4,
            max_tokens=800
        )
        summary = summary_response.choices[0].message.content
        st.markdown("### 📝 Summary")
        st.markdown(summary)

        st.session_state.history.append({"q": query, "a": answer, "summary": summary})
