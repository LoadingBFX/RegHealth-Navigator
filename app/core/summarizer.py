import os
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from openai import OpenAI

# Add the app directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

# -------- OpenAI Client Initialization --------
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else exit("❌ OPENAI_API_KEY is not set.")

SUMMARY_DIR = Path("./summary_outputs")
SUMMARY_DIR.mkdir(exist_ok=True)

# -------- Utilities --------
def count_tokens(text: str) -> int:
    return len(text.encode("utf-8")) // 4  # rough approximation

def chunk_batches(data: List[Dict], batch_size: int) -> List[List[Dict]]:
    return [data[i:i+batch_size] for i in range(0, len(data), batch_size)]

# -------- Prompt Utilities --------
def get_batch_prompt(program: str, batch: List[Dict], batch_num: int) -> str:
    formatted_chunks = "\n\n".join(
        f"[Section {i+1}]\n{c.get('page_content') or c.get('text', '')}" for i, c in enumerate(batch)
    )
    return f"""
You are a senior compliance analyst reviewing CMS {program.upper()} Final Rule content.

Below are multiple sections grouped together. For each distinct topic you identify in the text, extract:
- topic (brief title)
- key_changes (bulleted list with conditions, expiration dates, etc.)
- quantitative_data (numbers, percentages, codes, dates)
- stakeholders_affected (e.g. physicians, billing staff)

Respond as a list of valid JSON objects.

[Start of batched text: Batch {batch_num}]
{formatted_chunks}
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
    json_path = SUMMARY_DIR / f"{file_name}.json"

    if summary_path.exists():
        print("📄 Cached summary found. Loading...\n")
        return summary_path.read_text()

    if json_path.exists():
        print("📄 Found precomputed JSON summary. Skipping chunk-level summarization...")
        with open(json_path, 'r') as jf:
            individual_summaries = json.load(jf)
    else:
        individual_summaries: List[Dict[str, Any]] = []
        batches = chunk_batches(chunks_data, batch_size=5)

        for b_idx, batch in enumerate(batches):
            prompt = get_batch_prompt(program, batch, b_idx + 1)
            print(f"🔄 Summarizing batch {b_idx + 1}/{len(batches)} ({len(batch)} chunks)...")

            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    response_format={"type": "json_object"}
                )
                parsed = json.loads(response.choices[0].message.content)
                if isinstance(parsed, list):
                    individual_summaries.extend(parsed)
                else:
                    individual_summaries.append(parsed)
                print(f"✅ Batch {b_idx + 1} summarized.")
            except Exception as e:
                print(f"❌ Error summarizing batch {b_idx + 1}: {e}")
                continue

        if not individual_summaries:
            return "No report could be generated; all batch analysis failed."

        with open(json_path, 'w') as jf:
            json.dump(individual_summaries, jf, indent=2)
        print(f"💾 Saved intermediate summary JSON to {json_path}")

    year_str = file_name.split('_')[0] if '_' in file_name else "latest"
    joined_summaries = json.dumps(individual_summaries, indent=2)

    if count_tokens(joined_summaries) > 100000:
        print(f"⚠️ Truncating joined summaries to 100000 tokens...")
        joined_summaries = joined_summaries[:350000]

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
    CHUNKS_FILE_PATH = Path(config.faiss_metadata_path)
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
