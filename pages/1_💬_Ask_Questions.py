import streamlit as st
import openai
import json
import re

from state import (
    init_session, sidebar_api_setup,  # 👈 ADD THIS
    load_index, embed_query, search_chunks,
    get_context, PROMPTS, render_chunks, count_tokens
)

MODEL_TOKEN_LIMITS = {
    "gpt-4": (8192, 3000),
    "gpt-4o": (128000, 16384)
}

# ---------- Setup ----------
init_session()
sidebar_api_setup()  # 👈 ADD THIS

if not st.session_state.submitted:
    st.warning("Please enter your OpenAI API key and model first in the sidebar.")
    st.stop()

# ---------- UI ----------
st.title("💬 Ask a Question")
st.markdown("Ask any question about healthcare compliance rules. Relevant sections will be retrieved and used to generate an answer.")

with st.expander("💡 Example Questions", expanded=False):
    st.markdown("""
- What are the hospice payment updates in the 2025 final rule?
- What QRP requirements were finalized for SNFs in 2024?
- How is the wage index calculated in the 2022 proposed rule?
""")


# ---------- Load Metadata ----------
index, metadata = load_index()

# ---------- Context-Aware Dropdown Filters ----------
def get_unique_values(field, condition=None):
    return sorted(set(
        doc["metadata"][field]
        for doc in metadata
        if field in doc["metadata"] and (condition is None or condition(doc))
    ))

st.markdown("### 🔍 Optional Filters")
col1, col2, col3 = st.columns(3)

with col2:
    selected_program = st.selectbox("🏥 Program (optional)", [""] + get_unique_values("program"))
with col1:
    selected_year = st.selectbox("📅 Year (optional)", [""] + get_unique_values("year", lambda d: not selected_program or d["metadata"].get("program") == selected_program))
with col3:
    selected_type = st.selectbox("📄 Rule Type (optional)", [""] + get_unique_values("rule_type", lambda d:
        (not selected_program or d["metadata"].get("program") == selected_program) and
        (not selected_year or str(d["metadata"].get("year")) == str(selected_year))
    ))

# ---------- Question Input ----------
query = st.text_input("Your question", placeholder="e.g. What did CMS finalize about SNF QRP reporting in 2025?")
show_chunks = st.checkbox("📄 Show chunks used", value=False)
submit_clicked = st.button("Get Answer")
if query and submit_clicked:
    client = openai.OpenAI(api_key=st.session_state.api_key)

    # ---------- Step 1: Interpret user question ----------
    with st.spinner("🤖 Interpreting your question..."):
        clarify_prompt = f"""
You are an assistant that extracts metadata from user queries about healthcare policy rules.

Extract as JSON with the following fields:
- year
- program (e.g. hospice, snf, mpfs)
- rule_type (proposed or final)
- topic (short phrase summarizing focus)

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
                    st.error(f"⚠️ Could not parse metadata. GPT returned:\n```\n{clarify_raw}\n```")
                    st.stop()
            else:
                st.error(f"⚠️ Could not parse metadata. GPT returned:\n```\n{clarify_raw}\n```")
                st.stop()

        st.markdown(f"🧠 Interpreted query as: `{extracted}`")

        # ---------- Filter mismatch warning ----------
        mismatches = []
        if selected_year and extracted.get("year") and str(selected_year) != str(extracted["year"]):
            mismatches.append(f"- Year mismatch: prompt = `{extracted['year']}`, filter = `{selected_year}`")
        if selected_program and extracted.get("program") and selected_program.lower() != extracted["program"].lower():
            mismatches.append(f"- Program mismatch: prompt = `{extracted['program']}`, filter = `{selected_program}`")
        if selected_type and extracted.get("rule_type") and selected_type.lower() != extracted["rule_type"].lower():
            mismatches.append(f"- Rule type mismatch: prompt = `{extracted['rule_type']}`, filter = `{selected_type}`")

        if mismatches:
            st.warning("⚠️ Your filters do not match what the model inferred from your question:\n" + "\n".join(mismatches))

    # ---------- Step 2: Retrieve relevant context ----------
    with st.spinner("📚 Retrieving relevant rule text..."):
        def doc_matches(doc):
            return (
                (not selected_year or str(doc["metadata"].get("year")) == str(selected_year)) and
                (not selected_program or doc["metadata"].get("program", "").lower() == selected_program.lower()) and
                (not selected_type or doc["metadata"].get("rule_type", "").lower() == selected_type.lower())
            )

        filtered = [doc for doc in metadata if doc_matches(doc)]

        if not filtered:
            st.warning("⚠️ No matching documents found using selected filters. Falling back to inferred metadata...")
            filtered = [
                doc for doc in metadata
                if (not extracted.get("year") or str(doc["metadata"].get("year")) == str(extracted["year"])) and
                (not extracted.get("program") or extracted["program"].lower() in doc["metadata"].get("program", "").lower()) and
                (not extracted.get("rule_type") or extracted["rule_type"].lower() in doc["metadata"].get("rule_type", "").lower())
            ]

        if not filtered:
            st.error("❌ No matching documents found from filters or metadata.")
            st.stop()

        query_vec = embed_query(query, st.session_state.api_key)
        top_chunks = search_chunks(query_vec, index, filtered, query=query, k=30)
        context, used_chunks = get_context(top_chunks, limit=100000)

        if not used_chunks:
            st.error("❌ No relevant context found.")
            st.stop()

        if show_chunks:
            render_chunks(used_chunks)
    # ---------- Step 3: Generate detailed answer ----------
    with st.spinner("🧠 Generating detailed answer..."):
        prompt = PROMPTS["ask"].format(context=context, query=query)
        model = st.session_state.model
        prompt_tokens = count_tokens(prompt, model=model)
        model_limit, max_completion = MODEL_TOKEN_LIMITS.get(model, (8192, 3000))
        max_output_tokens = max(500, min(max_completion, model_limit - prompt_tokens - 500))

        st.markdown(f"ℹ️ Model: `{model}` | Prompt: `{prompt_tokens}` tokens | Max output: `{max_output_tokens}`")

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant answering policy questions based only on retrieved context."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=max_output_tokens
        )
        answer = response.choices[0].message.content.strip()
        st.markdown("### 🧠 Full Answer")
        st.markdown(answer)

    # ---------- Step 4: Generate summary ----------
    with st.spinner("📝 Summarizing the answer..."):
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
        summary = summary_response.choices[0].message.content.strip()
        st.markdown("### 📝 Summary")
        st.markdown(summary)

    # ---------- Log to history ----------
    st.session_state.history.append({
        "question": query,
        "metadata": extracted,
        "answer": answer,
        "summary": summary
    })
