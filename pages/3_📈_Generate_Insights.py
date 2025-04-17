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

st.title("📈 Generate Strategic Insights")
st.markdown("Analyze CMS rule content and generate actionable recommendations.")

with st.expander("💡 Example Prompts", expanded=False):
    st.markdown("""
**For 2023 Hospice Rules:**
- What actions should hospice agencies take to prepare for the 2023 final rule updates on provider enrollment and quality reporting?
- What strategic recommendations can you give based on the changes in the 2023 hospice proposed rule regarding health equity?

**For 2023 SNF Rules:**
- What steps should skilled nursing facilities take in response to the 2023 SNF final rule's quality reporting and VBP changes?
- How should SNFs prepare for the proposed permanent cap on wage index decreases outlined in the 2023 SNF proposed rule?
""")

scenario = st.text_input("Describe your scenario or request for insights", placeholder="e.g. What actions should providers take in response to the 2025 SNF rule?")
show_chunks = st.checkbox("📄 Show chunks used", value=False)
submit_clicked = st.button("Generate Insights")

if scenario and submit_clicked:
    client = openai.OpenAI(api_key=st.session_state.api_key)

    with st.spinner("🤖 Step 1: Understanding your scenario..."):
        clarify_prompt = f"""
You are analyzing a user scenario to extract metadata for CMS policy insight generation.

Extract as JSON with these fields:
- year
- program (e.g. hospice, snf, mpfs)
- rule_type (proposed or final)
- topic (short description of the scenario's main subject)

Scenario:
{scenario}

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

        st.markdown(f"🧠 Interpreted scenario as: `{extracted}`")

    with st.spinner("📚 Step 2: Retrieving relevant rule text..."):
        index, metadata = load_index()
        filtered = [
            doc for doc in metadata
            if (not extracted.get("year") or str(doc["metadata"].get("year")) == str(extracted["year"]))
            and (not extracted.get("program") or extracted["program"].lower() in doc["metadata"].get("title", "").lower())
            and (not extracted.get("rule_type") or extracted["rule_type"].lower() in doc["metadata"].get("rule_type", "").lower())
        ]

        if not filtered:
            st.warning("⚠️ No matching documents found using metadata. Falling back to all documents.")
            filtered = metadata

        query_vec = embed_query(scenario, st.session_state.api_key)
        results = search_chunks(query_vec, index, filtered, query=scenario, k=30)
        context, used_chunks = get_context(results, limit=100000)

        if not used_chunks:
            st.error("❌ No relevant context found.")
            st.stop()

        if show_chunks:
            render_chunks(used_chunks)

    with st.spinner("🧠 Step 3: Generating strategic analysis..."):
        prompt = PROMPTS["insight"].format(context=context, query=scenario)
        model = st.session_state.model
        prompt_tokens = count_tokens(prompt)
        model_limit, max_completion = MODEL_TOKEN_LIMITS.get(model, (8192, 3000))
        max_output_tokens = max(500, min(max_completion, model_limit - prompt_tokens - 500))

        st.markdown(f"ℹ️ Model: `{model}` | Prompt: `{prompt_tokens}` tokens | Max output: `{max_output_tokens}`")

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert generating strategic guidance based only on the rule content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=max_output_tokens
        )
        insight = response.choices[0].message.content
        st.markdown("### 📊 Strategic Insight")
        st.markdown(insight)

    with st.spinner("💡 Step 4: Generating Recommendations..."):
        summary_prompt = f"""
Based on this analysis, write a clear, structured list of **actionable recommendations** for healthcare organizations.

Focus on the most important changes or risks from the rule. Your audience includes policy directors and compliance leads.

Insight:
{insight}

Full Recommendations:
"""
        summary_response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.4,
            max_tokens=1000
        )
        recommendations = summary_response.choices[0].message.content
        st.markdown("### ✅ Recommendations")
        st.markdown(recommendations)

        st.session_state.history.append({
            "scenario": scenario,
            "analysis": insight,
            "recommendations": recommendations
        })
