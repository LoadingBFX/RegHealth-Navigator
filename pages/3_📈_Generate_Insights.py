import streamlit as st
import openai
import json
import re

from state import (
    init_session, load_index, embed_query, search_chunks,
    get_context, PROMPTS, render_chunks, count_tokens
)

MODEL_TOKEN_LIMITS = {
    "gpt-4": (8192, 3000),
    "gpt-4o": (128000, 16384)
}

# ---------- Setup ----------
init_session()
if not st.session_state.submitted:
    st.warning("Please enter your OpenAI API key and model first.")
    st.stop()

st.title("📈 Generate Strategic Insights")
st.markdown("Analyze healthcare rule content and generate actionable recommendations.")

with st.expander("💡 Example Prompts", expanded=False):
    st.markdown("""
**For 2023 Hospice Rules:**
- What actions should hospice agencies take to prepare for the 2023 final rule updates on provider enrollment and quality reporting?
- What strategic recommendations can you give based on the changes in the 2023 hospice proposed rule regarding health equity?

**For 2023 SNF Rules:**
- What steps should skilled nursing facilities take in response to the 2023 SNF final rule's quality reporting and VBP changes?
- How should SNFs prepare for the proposed permanent cap on wage index decreases outlined in the 2023 SNF proposed rule?
""")

# ---------- User Prompt ----------
scenario = st.text_input("Describe your scenario or request for insights", placeholder="e.g. What actions should providers take in response to the 2025 SNF rule?")

# ---------- Load Metadata ----------
index, metadata = load_index()

# ---------- Hierarchical Filter Options ----------
st.markdown("### 🔍 Optional: Narrow context by metadata")
meta_col1, meta_col2, meta_col3 = st.columns(3)

with meta_col1:
    available_years = sorted(set(str(m["metadata"].get("year")) for m in metadata if m["metadata"].get("year")))
    selected_year = st.selectbox("📅 Year", [""] + available_years)

with meta_col2:
    available_programs = sorted(set(
        m["metadata"]["program"] for m in metadata
        if (not selected_year or str(m["metadata"].get("year")) == selected_year)
    ))
    selected_program = st.selectbox("🏥 Program", [""] + available_programs)

with meta_col3:
    available_rule_types = sorted(set(
        m["metadata"]["rule_type"] for m in metadata
        if (not selected_year or str(m["metadata"].get("year")) == selected_year) and
           (not selected_program or m["metadata"].get("program") == selected_program)
    ))
    selected_rule_type = st.selectbox("📄 Rule Type", [""] + available_rule_types)

show_chunks = st.checkbox("📄 Show chunks used", value=False)
submit_clicked = st.button("Generate Insights")
if scenario and submit_clicked:
    client = openai.OpenAI(api_key=st.session_state.api_key)

    with st.spinner("🤖 Step 1: Extracting metadata from scenario..."):
        clarify_prompt = f"""
You are analyzing a user scenario to extract metadata for healthcare rule insight generation.

Extract as JSON with these fields:
- year
- program (e.g. hospice, snf, mpfs)
- rule_type (proposed or final)
- topic (short phrase summarizing the main subject)

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

        # Override with user-selected filters if provided
        if selected_year:
            extracted["year"] = selected_year
        if selected_program:
            extracted["program"] = selected_program
        if selected_rule_type:
            extracted["rule_type"] = selected_rule_type

        # Warn on mismatch between prompt and selected filters
        mismatches = []
        if selected_year and "year" in extracted and str(extracted["year"]) != selected_year:
            mismatches.append(f"- Year mismatch: `{extracted['year']}` vs filter `{selected_year}`")
        if selected_program and "program" in extracted and extracted["program"].lower() != selected_program.lower():
            mismatches.append(f"- Program mismatch: `{extracted['program']}` vs filter `{selected_program}`")
        if selected_rule_type and "rule_type" in extracted and extracted["rule_type"].lower() != selected_rule_type.lower():
            mismatches.append(f"- Rule type mismatch: `{extracted['rule_type']}` vs filter `{selected_rule_type}`")

        if mismatches:
            st.warning("⚠️ Metadata mismatch between prompt and selected filters:\n" + "\n".join(mismatches))

    with st.spinner("📚 Step 2: Retrieving relevant rule text..."):
        filtered = [
            doc for doc in metadata
            if (not extracted.get("year") or str(doc["metadata"].get("year")) == str(extracted["year"]))
            and (not extracted.get("program") or extracted["program"].lower() == doc["metadata"].get("program", "").lower())
            and (not extracted.get("rule_type") or extracted["rule_type"].lower() == doc["metadata"].get("rule_type", "").lower())
        ]

        if not filtered:
            st.warning("⚠️ No matching documents found using extracted metadata. Searching all documents instead.")
            filtered = metadata

        query_vec = embed_query(scenario, st.session_state.api_key)
        results = search_chunks(query_vec, index, filtered, query=scenario, k=30)
        context, used_chunks = get_context(results, limit=100000)

        if not used_chunks:
            st.error("❌ No relevant content found in retrieved context.")
            st.stop()

        if show_chunks:
            render_chunks(used_chunks)
    with st.spinner("🧠 Step 3: Generating strategic analysis..."):
        prompt = PROMPTS["insight"].format(context=context, query=scenario)
        model = st.session_state.model
        prompt_tokens = count_tokens(prompt, model=model)
        model_limit, max_completion = MODEL_TOKEN_LIMITS.get(model, (8192, 3000))
        max_output_tokens = max(500, min(max_completion, model_limit - prompt_tokens - 500))

        st.markdown(f"ℹ️ Model: `{model}` | Prompt: `{prompt_tokens}` tokens | Max output: `{max_output_tokens}`")

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert healthcare policy advisor generating strategic analysis. "
                        "Use only the retrieved context. Do not make assumptions beyond it."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=max_output_tokens
        )
        insight = response.choices[0].message.content.strip()
        st.markdown("### 📊 Strategic Insight")
        st.markdown(insight)

    with st.spinner("💡 Step 4: Generating actionable recommendations..."):
        summary_prompt = f"""
Based on this analysis, write a clear, structured list of **actionable recommendations** for healthcare organizations.

Your audience includes policy directors, compliance leads, and operations managers. Focus on key changes, risks, or operational next steps.

Insight:
{insight}

Recommendations:
"""

        summary_response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": summary_prompt}
            ],
            temperature=0.4,
            max_tokens=1000
        )
        recommendations = summary_response.choices[0].message.content.strip()
        st.markdown("### ✅ Recommendations")
        st.markdown(recommendations)

        # Store result in session history
        st.session_state.history.append({
            "scenario": scenario,
            "metadata": extracted,
            "analysis": insight,
            "recommendations": recommendations
        })
