import streamlit as st
import openai
from state import (
    init_session, sidebar_api_setup,  # ✅ NEW
    load_index, embed_query, search_chunks,
    get_context, PROMPTS, render_chunks, count_tokens
)

# ---------- Setup ----------
init_session()
sidebar_api_setup()  # ✅ NEW

if not st.session_state.submitted:
    st.warning("Please enter your OpenAI API key and model first in the sidebar.")
    st.stop()

# ---------- UI ----------
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

# Load metadata
index, metadata = load_index()

# --- Helper functions ---
def get_unique(metadata, field, condition=None):
    return sorted(set(
        c["metadata"][field]
        for c in metadata
        if field in c["metadata"] and (condition is None or condition(c))
    ))

def get_years_for_program(program):
    return get_unique(metadata, "year", lambda c: c["metadata"].get("program") == program)

def get_rule_types(program, year):
    return get_unique(metadata, "rule_type", lambda c: c["metadata"].get("program") == program and c["metadata"].get("year") == year)

def get_sections(program, year, rule_type):
    return sorted(set(
        c["section_header"]
        for c in metadata
        if c["metadata"].get("program") == program
        and c["metadata"].get("year") == year
        and c["metadata"].get("rule_type") == rule_type
    ))

# --- UI Layout ---
col1, col2 = st.columns(2)

with col1:
    program1 = st.selectbox("Program", get_unique(metadata, "program"), key="program1")
    year1 = st.selectbox("Year", get_years_for_program(program1), key="year1")
    rule_type1 = st.selectbox("Rule Type", get_rule_types(program1, year1), key="type1")
    section1 = st.selectbox("Section (optional)", [""] + get_sections(program1, year1, rule_type1), key="section1")

with col2:
    program2 = st.selectbox("Program", get_unique(metadata, "program"), key="program2")
    year2 = st.selectbox("Year", get_years_for_program(program2), key="year2")
    rule_type2 = st.selectbox("Rule Type", get_rule_types(program2, year2), key="type2")
    section2 = st.selectbox("Section (optional)", [""] + get_sections(program2, year2, rule_type2), key="section2")

query = st.text_input("What do you want to compare?", "What are the differences between the two rules?")
show_chunks = st.checkbox("📄 Show chunks used")
submit = st.button("Compare Rules")

if submit and query:
    client = openai.OpenAI(api_key=st.session_state.api_key)

    with st.spinner("🤖 Step 1: Understanding your comparison focus..."):
        clarify_prompt = f"""You are a policy assistant helping compare two rules. Extract the key focus of the request.

Comparison request:
{query}

Respond with a short phrase (e.g., payment, staffing, QRP, SDOH, etc.):"""

        clarify_response = client.chat.completions.create(
            model=st.session_state.model,
            messages=[{"role": "user", "content": clarify_prompt}],
            temperature=0,
            max_tokens=50
        )
        focus_area = clarify_response.choices[0].message.content.strip()
        st.markdown(f"🔍 Focus area: **{focus_area}**")

    with st.spinner("📚 Step 2: Retrieving relevant context..."):
        def filter_chunks(year, program, rule_type, section):
            return [
                c for c in metadata
                if c["metadata"].get("program") == program
                and c["metadata"].get("year") == year
                and c["metadata"].get("rule_type") == rule_type
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
        tokens = count_tokens(prompt, model=model)
        model_limit, max_completion = {"gpt-4": (8192, 3000), "gpt-4o": (128000, 16384)}.get(model, (8192, 3000))
        max_output_tokens = min(max_completion, model_limit - tokens - 500)

        comparison_response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Compare these two rule excerpts clearly, citing meaningful differences."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=max_output_tokens
        )
        comparison = comparison_response.choices[0].message.content
        st.markdown("### 📊 Comparison")
        st.markdown(comparison)

    with st.spinner("💡 Step 4: Summarizing implications..."):
        summary_prompt = f"""Summarize the key implications of this rule comparison for healthcare providers.

Comparison:
{comparison}

Implications:"""

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
