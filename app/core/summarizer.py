import os
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from openai import OpenAI
from config import config


class SummaryGenerator:
    """
    Summary Generator for CMS regulatory rules using OpenAI.
    
    Responsibilities:
    - Chunk-based summarization using LLM
    - Topic extraction with metadata (key changes, stakeholders, data)
    - Final report synthesis with action items

    Usage:
        generator = SummaryGenerator()
        generator.generate_report(chunk_data, file_name)
    """

    def __init__(self, output_dir: str = "./summary_outputs", openai_api_key: str = os.getenv("OPENAI_API_KEY")):
        if not openai_api_key:
            sys.exit("OPENAI_API_KEY is not set.")
        self.client = OpenAI(api_key=openai_api_key)
        self.summary_dir = Path(output_dir)
        self.summary_dir.mkdir(exist_ok=True)

    def _count_tokens(self, text: str) -> int:
        return len(text.encode("utf-8")) // 4

    def _chunk_batches(self, data: List[Dict], batch_size: int) -> List[List[Dict]]:
        return [data[i:i + batch_size] for i in range(0, len(data), batch_size)]

    def _get_batch_prompt(self, program: str, batch: List[Dict], batch_num: int) -> str:
        formatted = "\n\n".join(
            f"[Section {i + 1}]\n{c.get('page_content') or c.get('text', '')}" for i, c in enumerate(batch)
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
{formatted}
[End of text]
"""

    def _get_final_report_prompt(self, program: str, year: str, summaries: str) -> str:
        try:
            parsed = json.loads(summaries)
            unique_topics = sorted(set(s.get("topic", "").strip() for s in parsed if s.get("topic")))
            section_str = "\n".join(f"- {t}" for t in unique_topics if t)
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

    def generate_report(self, chunks_data: List[Dict], file_name: str) -> str:
        program = "MPFS"
        lower_name = file_name.lower()
        if "hospice" in lower_name:
            program = "Hospice"
        elif "snf" in lower_name:
            program = "SNF"

        summary_path = self.summary_dir / f"{file_name}.md"
        json_path = self.summary_dir / f"{file_name}.json"

        if summary_path.exists():
            print("📄 Cached summary found. Loading...\n")
            return summary_path.read_text()

        if json_path.exists():
            print("📄 Found precomputed JSON summary.")
            with open(json_path, 'r') as jf:
                individual_summaries = json.load(jf)
        else:
            individual_summaries = []
            batches = self._chunk_batches(chunks_data, batch_size=5)

            for b_idx, batch in enumerate(batches):
                prompt = self._get_batch_prompt(program, batch, b_idx + 1)
                print(f"🔄 Summarizing batch {b_idx + 1}/{len(batches)}...")

                try:
                    response = self.client.chat.completions.create(
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
                return "No report generated; all batch analysis failed."

            with open(json_path, 'w') as jf:
                json.dump(individual_summaries, jf, indent=2)
            print(f"💾 Intermediate JSON saved to {json_path}")

        year_str = file_name.split('_')[0] if '_' in file_name else "latest"
        joined_summaries = json.dumps(individual_summaries, indent=2)

        if self._count_tokens(joined_summaries) > 100000:
            print(f"⚠️ Truncating to 100,000 tokens...")
            joined_summaries = joined_summaries[:350000]

        final_prompt = self._get_final_report_prompt(program, year_str, joined_summaries)

        try:
            print("\n🔄 Generating final summary report...")
            final_response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": final_prompt}],
                temperature=0.1,
            )
            final_report = final_response.choices[0].message.content.strip()
            with open(summary_path, 'w') as f:
                f.write(final_report)
            print("✅ Final report saved.")
            return final_report
        except Exception as e:
            print(f"❌ Error generating report: {e}")
            return f"Final synthesis failed. Raw data below:\n\n{joined_summaries}"
