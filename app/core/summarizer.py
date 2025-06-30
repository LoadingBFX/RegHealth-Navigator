import os
import json
from pathlib import Path
from typing import List, Dict, Any
from openai import OpenAI

# -------- OpenAI Client Initialization --------
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else exit("❌ OPENAI_API_KEY is not set.")

SUMMARY_DIR = Path("./summary_outputs")
SUMMARY_DIR.mkdir(exist_ok=True)

# -------- Prompt Utilities --------
def get_chunk_prompt(program: str) -> str:
    return f"""
You are a senior compliance analyst reviewing a CMS {program.upper()} Final Rule.

Analyze the following section and extract:
1. topic (main subject)
2. key_changes (bulleted list with conditions, expirations, etc.)
3. quantitative_data (numbers, percentages, codes, dates)
4. stakeholders_affected (who is impacted)

Respond as a single valid JSON object.

[Start of text]
{{chunk}}
[End of text]
"""

def get_final_report_prompt(program: str, year: str, summaries: str) -> str:
    try:
        parsed = json.loads(summaries)
        unique_topics = sorted(set(s.get("topic", "").strip() for s in parsed if s.get("topic")))
        section_str = "\n".join([f"- {t}" for t in unique_topics if t])
        if not section_str:
            raise ValueError("No topics found")
    except Exception:
        section_str = "- Key Policy Changes"

    title = f"Business Intelligence Report: CY {year} {program.upper()} Final Rule"
    return f"""
You are a senior regulatory analyst. Using the structured JSON below, write a professional summary for executives.

### {title}

**Sections to include:**
{section_str}
- Action Items for Stakeholders

Use specific numbers, dates, and codes. Emphasize what is temporary vs. permanent.

[Start of structured JSON data]
{summaries}
[End of structured JSON data]
"""

# -------- Summarization Function --------
def generate_report(chunks_data: List[Dict], file_name: str) -> str:
    if not client:
        return "Error: OpenAI API key not set."

    program = "MPFS"
    lower_name = file_name.lower()
    if "hospice" in lower_name:
        program = "Hospice"
    elif "snf" in lower_name:
        program = "SNF"

    summary_path = SUMMARY_DIR / f"{file_name}.md"
    if summary_path.exists():
        print("📄 Cached summary found. Loading...\n")
        return summary_path.read_text()

    chunk_prompt_template = get_chunk_prompt(program)
    individual_summaries: List[Dict[str, Any]] = []

    for i, chunk_info in enumerate(chunks_data):
        chunk_text = chunk_info.get('page_content') or chunk_info.get('text', '')
        if not chunk_text.strip(): continue

        prompt = chunk_prompt_template.replace("{chunk}", chunk_text)
        print(f"🔄 Analyzing chunk {i+1}/{len(chunks_data)} for {file_name}...")

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            parsed_summary = json.loads(response.choices[0].message.content)
            individual_summaries.append(parsed_summary)
            print(f"✅ Chunk {i+1} analyzed.")
        except Exception as e:
            print(f"❌ Error analyzing chunk {i+1}: {e}")
            continue

    if not individual_summaries:
        return "No report could be generated; all chunk analysis failed."

    year_str = file_name.split('_')[0] if '_' in file_name else "latest"
    joined_summaries = json.dumps(individual_summaries, indent=2)
    final_prompt = get_final_report_prompt(program, year_str, joined_summaries)

    try:
        print("\n🔄 Generating final summary report...")
        final_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": final_prompt}],
            temperature=0.1,
        )
        final_report = final_response.choices[0].message.content.strip()
        with open(summary_path, 'w') as f:
            f.write(final_report)
        print("✅ Final report generated and saved.")
        return final_report
    except Exception as e:
        print(f"❌ Error during report generation: {e}")
        return f"Final synthesis failed. Raw data below:\n\n{joined_summaries}"

# -------- Main Runner --------
if __name__ == "__main__":
    CHUNKS_FILE_PATH = Path("../../rag_data/faiss_metadata.json")
    print(f"Loading chunks from {CHUNKS_FILE_PATH}...")

    try:
        with open(CHUNKS_FILE_PATH, 'r', encoding='utf-8') as f:
            all_chunks = json.load(f)
        print(f"✅ Loaded {len(all_chunks)} chunks.")
    except Exception as e:
        print(f"❌ Error loading chunks: {e}")
        exit(1)

    chunks_by_file: Dict[str, List[Dict]] = {}
    for chunk in all_chunks:
        source_file = chunk.get('metadata', {}).get('source_file', 'unknown.xml')
        chunks_by_file.setdefault(source_file, []).append(chunk)

    print("\nAvailable documents:")
    for i, name in enumerate(sorted(chunks_by_file.keys())):
        print(f"[{i+1}] {name}")

    idx = -1
    while idx == -1:
        try:
            sel = input(f"Select document (1-{len(chunks_by_file)}): ")
            if 1 <= int(sel) <= len(chunks_by_file):
                idx = int(sel) - 1
            else:
                print("❌ Invalid number.")
        except ValueError:
            print("❌ Please enter a number.")

    file = sorted(chunks_by_file.keys())[idx]
    print(f"\n--- Generating summary for: {file} ---")
    report = generate_report(chunks_by_file[file], file)
    print("\n=== Final Report ===\n")
    print(report)
