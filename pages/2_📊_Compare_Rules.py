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

st.title("📊 Compare Two Rules")
st.markdown("Compare healthcare final or proposed rules across years or sections.")

with st.expander("💡 Example Comparison Questions", expanded=False):
    st.markdown("""
- What changed in hospice wage index policy between the 2022 proposed and final rules?
- Compare quality reporting updates in the 2023 SNF proposed and final rules.
- How did the 2023 vs. 2024 hospice rules differ in reporting requirements?
- What are the major policy changes in SNF payment between 2023 and 2025?
- Compare the treatment of palliative care in the 2024 and 2025 hospice final rules.
""")

# Load index
index, metadata = load_index()

# Get dynamic metadata options
def get_filtered_options(key, program=None):
    values = set()
    for m in metadata:
        if program and program.lower() not in m["metadata"].get("title", "").lower():
            continue
        if key == "section":
            values.add(m["section_header"])
        else:
            values.add(m["metadata"].get(key))
    return sorted(v for v in values if v)

# Input UI
col1, col2 = st.columns(2)
with col1:
    program1 = st.selectbox("Program", ["Hospice", "SNF"], key="program1")
    year1 = st.selectbox("Year", get_filtered_options("year", program1), key="year1")
    rule_type1 = st.selectbox("Rule Type", get_filtered_options("rule_type", program1), key="type1")
    section1 = st.selectbox("Section (optional)", [""] + get_filtered_options("section", program1), key="section1")
with col2:
    program2 = st.selectbox("Program", ["Hospice", "SNF"], key="program2")
    year2 = st.selectbox("Year", get_filtered_options("year", program2), key="year2")
    rule_type2 = st.selectbox("Rule Type", get_filtered_options("rule_type", program2), key="type2")
    section2 = st.selectbox("Section (optional)", [""] + get_filtered_options("section", program2), key="section2")

query = st.text_input("What do you want to compare?", "What are the differences between the two rules?")
show_chunks = st.checkbox("📄 Show chunks used")
submit = st.button("Compare Rules")

# Helper: mismatch warning
def prompt_filter_mismatch(query, year1, year2, program1, program2):
    mismatches = []
    years = re.findall(r"\b(20[0-5][0-9])\b", query)
    programs = ["hospice", "snf", "mpfs"]
    year_set = {str(year1), str(year2)}
    program_set = {program1.lower(), program2.lower()}
    for y in years:
        if y not in year_set:
            mismatches.append(f"Prompt mentions year `{y}` but selected years are {year_set}")
    for p in programs:
        if p in query.lower() and p not in program_set:
            mismatches.append(f"Prompt references `{p.upper()}` but filters are {program_set}")
    return mismatches
if submit and query:
    mismatches = prompt_filter_mismatch(query, year1, year2, program1, program2)
    if mismatches:
        st.warning("⚠️ Prompt and filter mismatch detected:\n\n- " + "\n- ".join(mismatches))

    client = openai.OpenAI(api_key=st.session_state.api_key)

    with st.spinner("🤖 Step 1: Understanding your comparison focus..."):
        clarify_prompt = f"""
You are a policy assistant helping compare two healthcare regulation documents. Extract the focus area of the comparison request below.

Return a short phrase indicating the topic area (e.g. payment updates, wage index, QRP, staffing, SDOH, palliative care, etc.)

Comparison request:
{query}

Respond only with the topic.
"""
        clarify_response = client.chat.completions.create(
            model=st.session_state.model,
            messages=[{"role": "user", "content": clarify_prompt}],
            temperature=0,
            max_tokens=100
        )
        focus_area = clarify_response.choices[0].message.content.strip()
        st.markdown(f"🔍 Interpreted topic: **{focus_area}**")

    with st.spinner("📚 Step 2: Retrieving context chunks..."):
        def filter_chunks(year, program, rule_type, section):
            return [
                c for c in metadata
                if str(c["metadata"].get("year")) == str(year)
                and rule_type.lower() in c["metadata"].get("rule_type", "").lower()
                and program.lower() in c["metadata"].get("title", "").lower()
                and (not section or section.lower() in c["section_header"].lower())
            ]

        chunks1 = filter_chunks(year1, program1, rule_type1, section1)
        chunks2 = filter_chunks(year2, program2, rule_type2, section2)

        if not chunks1 or not chunks2:
            st.error("❌ One or both selected rule documents are not available in the database.")
            st.stop()

        query_vec = embed_query(focus_area or query, st.session_state.api_key)
        rule1_ranked = search_chunks(query_vec, index, chunks1, query=query, k=20)
        rule2_ranked = search_chunks(query_vec, index, chunks2, query=query, k=20)

        context1, used1 = get_context(rule1_ranked, limit=50000)
        context2, used2 = get_context(rule2_ranked, limit=50000)

        if show_chunks:
            st.markdown("#### 📘 Rule 1 Context")
            render_chunks(used1)
            st.markdown("#### 📗 Rule 2 Context")
            render_chunks(used2)

    with st.spinner("🧠 Step 3: Comparing rules..."):
        model = st.session_state.model
        prompt = PROMPTS["compare"].format(context1=context1, context2=context2, query=query)
        tokens = count_tokens(prompt)
        model_limit, max_completion = MODEL_TOKEN_LIMITS.get(model, (8192, 3000))
        max_output_tokens = min(max_completion, model_limit - tokens - 500)

        comparison_response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Compare these two regulation excerpts clearly, identifying key differences and similarities that matter to healthcare stakeholders."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=max_output_tokens
        )
        comparison = comparison_response.choices[0].message.content
        st.markdown("### 📊 Comparison")
        st.markdown(comparison)

    with st.spinner("💡 Step 4: Summarizing implications..."):
        summary_prompt = f"""
Summarize the key implications of this rule comparison for healthcare organizations.

Comparison:
{comparison}

Implications:
"""
        summary_response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.4,
            max_tokens=800
        )
        implications = summary_response.choices[0].message.content
        st.markdown("### 📝 Implications")
        st.markdown(implications)

        st.session_state.history.append({
            "comparison_query": query,
            "focus": focus_area,
            "comparison": comparison,
            "implications": implications
        })
