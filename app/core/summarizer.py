import os
import json
from pathlib import Path
from typing import List, Dict, Any
from openai import OpenAI, APIStatusError, APIConnectionError, APITimeoutError

# -------- OpenAI Client Initialization --------
api_key = os.getenv("OPENAI_API_KEY")
client = None
if api_key:
    client = OpenAI(api_key=api_key)
else:
    print("Error: OPENAI_API_KEY environment variable not set. Please set it before running.")
    exit(1)

# -------- ADVANCED PROMPT TEMPLATES (V3 - Added Flexibility) --------

# 1단계 프롬프트: '조건'과 '예외' 같은 뉘앙스 추출을 강조하도록 개선
COMPANY_SPECIFIC_CHUNK_PROMPT = """
You are a senior compliance analyst for a healthcare technology company specializing in software for outpatient therapy (PT, OT, SLP), wound care, and telehealth.

Analyze the following section of the Medicare Physician Fee Schedule (MPFS) Final Rule. From this text, extract key data points relevant to our business.

For the provided text chunk, extract the following information:
1.  **topic**: Identify the main regulatory topic (e.g., "Conversion Factor", "Telehealth Modifiers", "Therapy Supervision", "Skin Substitutes Payment").
2.  **key_changes**: In a bulleted list, summarize the specific policy changes. **Pay close attention to conditions, exceptions, and expiration dates (e.g., "temporary through 2024", "permanent", "does not apply to...") and include them in this summary.**
3.  **quantitative_data**: List all specific numbers, percentages, dollar amounts, CPT/HCPCS codes, or dates mentioned (e.g., "Conversion factor is $32.7442", "3.37% decrease", "Threshold is $2330", "Codes 97550-97552").
4.  **stakeholders_affected**: List the primary groups impacted (e.g., "Physical Therapists", "Physicians", "Hospitals", "Billing Staff").

Provide the response as a single, valid JSON object.

[Start of text]
{chunk}
[End of text]
"""

# 2단계 프롬프트: 유연성 확보를 위해 'Additional Notable Updates' 섹션을 추가
FINAL_REPORT_PROMPT = """
You are a senior regulatory analyst producing a final, client-ready business intelligence report on the new Medicare Physician Fee Schedule (MPFS) Final Rule. Your audience consists of executives and product managers at a healthcare tech company focused on therapy, wound care, and telehealth.

Synthesize the provided JSON data into a comprehensive, professional report. Your tone must be direct, confident, and factual.

**CRITICAL INSTRUCTIONS:**
1.  **Integrate Specific Data:** You MUST integrate the specific quantitative data (dollar amounts, percentages, codes, dates) from the JSON into your narrative. DO NOT use vague phrases like "was updated" or "was revised." State the facts.
2.  **Distinguish Nuances:** Clearly distinguish between permanent policies and temporary flexibilities. ALWAYS state expiration dates explicitly (e.g., "this policy is extended through the end of CY {year}").
3.  **Follow the Structure Precisely:** Generate the report using the exact structure and headings below.

============================================================
### **Business Intelligence Report: CY {year} MPFS Final Rule**
============================================================

### **Key Dates**
- **Rule Released:** (Find and state the release date from the source text)
- **Final Rule Effective:** (Find and state the effective date from the source text)

---

### **Executive Summary**
Provide a high-level overview of the most critical updates. Start with the most important financial impact: the exact new conversion factor and its percentage change from the previous year. Then, briefly summarize 2-3 other major policy shifts, such as the temporary extension of telehealth flexibilities for therapy and the introduction of new service codes.

---

### **Detailed Regulatory Analysis**

**1. Payment and Reimbursement Updates**
   - **Conversion Factor:** State the exact new CY {year} conversion factor. Compare it to the previous year's factor and state the precise percentage decrease.
   - **Therapy Threshold (KX Modifier):** State the exact new dollar thresholds for PT/SLP services and for OT services. Mention the medical review threshold amount and its effective period.
   - **Potentially Misvalued Codes:** List the key therapy codes nominated as potentially misvalued and briefly explain the reason for the review.

**2. Telehealth Policies**
   - **Service & Practitioner Eligibility for Therapy:** Clarify the exact status of therapists (PT, OT, SLP) and therapy codes on the telehealth list. Emphasize that this is a **temporary flexibility extended through the end of CY {year}** and that these practitioners are **not** on the permanent telehealth provider list.
   - **Supervision:** Describe the current policy for virtual direct supervision, including its expiration date at the end of CY {year}.
   - **Modifiers and Place of Service (POS) Codes:** Explain the specific billing rules for outpatient therapy, including the continued use of Modifier 95 and the appropriate POS code through CY {year}.

**3. New & Updated CPT/HCPCS Codes**
   - **Caregiver Training Services:** Detail the new CPT codes (97550, 97551, 97552), their status as "sometimes therapy," and who is eligible to bill for them.
   - **E/M Visit Complexity (G2211):** Explain the implementation of the E/M complexity add-on code G2211 and its impact on budget neutrality.

**4. Other Key Policy Changes**
   - **Split (or Shared) E/M Visits:** State the revised definition of "substantive portion" for billing these visits.
   - **Skin Substitutes:** Summarize the current CMS position on coding and payment for skin substitutes for CY {year}, noting that major changes are deferred to future rulemaking.

**5. Additional Notable Updates**
   - **(Summarize any other significant topics found in the source text that do not fit into the predefined categories above. This is your place to capture novel or unexpected regulatory changes, such as policies on EPCS, the AUC program, or MSSP.)**

---

### **Action Items for Stakeholders**
Create a concise, actionable checklist for our company and customers. Use the specific data you've analyzed.
- Example: "Update billing systems with the CY {year} conversion factor of $32.7442, a 3.37% decrease from CY 2023."
- Example: "Educate therapy providers that their eligibility to furnish telehealth services expires on December 31, {year}, unless new legislation is passed."
- Example: "Incorporate new Caregiver Training CPT codes (97550-97552) into the billing platform and provide guidance on their use."
- Example: "Notify customers that the KX modifier threshold for CY {year} is now $2,330 for PT/SLP and $2,330 for OT."

[Start of structured JSON data]
{summaries}
[End of structured JSON data]
"""

# -------- Summarization Function --------
def generate_report(chunks_data: List[Dict], file_name: str) -> str:
    global client
    if not client: return "Error: OpenAI API key not set."

    individual_summaries: List[Dict[str, Any]] = []

    for i, chunk_info in enumerate(chunks_data):
        chunk_text = chunk_info.get('page_content') or chunk_info.get('text', '')
        if not chunk_text.strip(): continue

        prompt = COMPANY_SPECIFIC_CHUNK_PROMPT.format(chunk=chunk_text)
        print(f"🔄 Analyzing chunk {i+1}/{len(chunks_data)} for {file_name}...")

        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            summary_json_str = response.choices[0].message.content
            parsed_summary = json.loads(summary_json_str)
            individual_summaries.append(parsed_summary)
            print(f"✅ Chunk {i+1} analyzed.")
        except Exception as e:
            print(f"❌ Error analyzing chunk {i+1}: {e}")
            continue

    if not individual_summaries:
        return "No report could be generated; analysis of chunks failed."

    year_str = file_name.split('_')[0] if '_' in file_name else "latest"
    joined_summaries = json.dumps(individual_summaries, indent=2)
    final_prompt = FINAL_REPORT_PROMPT.format(summaries=joined_summaries, year=year_str)

    try:
        print("\n🔄 Generating final, client-ready intelligence report...")
        final_response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": final_prompt}],
            temperature=0.1,
        )
        final_report = final_response.choices[0].message.content.strip()
        print("✅ Final report generated successfully.")
        return final_report
    except Exception as e:
        print(f"❌ An unexpected error occurred during final report generation: {e}")
        return f"Final synthesis failed. Raw chunk data below:\n\n{joined_summaries}"

# -------- Main Execution Block --------
if __name__ == "__main__":
    CHUNKS_FILE_PATH = Path("../../rag_data/faiss_metadata.json")
    print(f"Loading pre-processed chunks from {CHUNKS_FILE_PATH}...")

    try:
        with open(CHUNKS_FILE_PATH, 'r', encoding='utf-8') as f:
            all_loaded_chunks = json.load(f)
        print(f"✅ Successfully loaded {len(all_loaded_chunks)} chunks.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error loading chunks file: {e}. Please ensure it exists and is valid JSON.")
        exit(1)

    chunks_by_source_file: Dict[str, List[Dict]] = {}
    for chunk in all_loaded_chunks:
        source_file = chunk.get('metadata', {}).get('source_file', 'unknown_document.xml')
        chunks_by_source_file.setdefault(source_file, []).append(chunk)

    if not chunks_by_source_file:
        print("⚠️ No processable documents found in the chunks file.")
        exit(0)

    source_files_list = sorted(list(chunks_by_source_file.keys()))
    print("\n--- Available Documents for Summarization ---")
    for i, file_name in enumerate(source_files_list):
        print(f"  [{i + 1}] {file_name}")

    selected_index = -1
    while selected_index == -1:
        try:
            choice = input(f"\nPlease enter the number of the document to process (1-{len(source_files_list)}): ")
            if 1 <= int(choice) <= len(source_files_list):
                selected_index = int(choice) - 1
            else:
                print(f"❌ Invalid number.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")

    selected_file = source_files_list[selected_index]
    chunks_for_selected_file = chunks_by_source_file[selected_file]

    print(f"\n--- Starting processing for: {selected_file} ---")
    report_result = generate_report(chunks_for_selected_file, selected_file)

    print("\n")
    print(report_result)
    print("\n------------------------------------------------------------\n")

    print("Selected document has been processed.")
