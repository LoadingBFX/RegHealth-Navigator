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

# -------- ADVANCED PROMPT TEMPLATES (Tailored to your example documents) --------

# This prompt now primes the AI to think like an analyst for a specific company.
# You can customize the "company focus" for different clients.
COMPANY_SPECIFIC_CHUNK_PROMPT = """
You are a senior compliance analyst for a healthcare technology company. Our company provides software solutions for outpatient therapy (Physical Therapy, Occupational Therapy, Speech-Language Pathology), wound care, and telehealth.

Analyze the following section of the Medicare Physician Fee Schedule (MPFS) Final Rule. From the text, extract the key changes and data points relevant to our business focus.

For the provided text chunk, extract the following information:
1.  **topic**: Identify the main regulatory topic (e.g., "Conversion Factor", "Telehealth Modifiers", "Therapy Supervision", "Skin Substitutes Payment").
2.  **key_changes**: In a bulleted list, summarize the specific policy changes, payment rate updates, new/deleted codes, or deadline changes. Be precise.
3.  **quantitative_data**: List any specific numbers, percentages, dollar amounts, or dates mentioned (e.g., "Conversion factor is $33.06", "Payment reduction of 3.37%", "Threshold is $2330", "Effective January 1, 2024").
4.  **stakeholders_affected**: List the primary groups impacted (e.g., "Physical Therapists", "Physicians", "Hospitals", "Billing Staff").

Provide the response as a single, valid JSON object.

[Start of text]
{chunk}
[End of text]
"""

# This prompt synthesizes the structured data into a full report mimicking your examples.
# The {amount} placeholders have been escaped as {{amount}} to fix the KeyError.
FINAL_REPORT_PROMPT = """
You are an expert regulatory analyst creating a business intelligence report for internal company use. The report summarizes the key impacts of the new Medicare Physician Fee Schedule (MPFS) Final Rule.

Using the provided structured data extracted from the rule, generate a comprehensive report. The report must be clear, well-organized, and targeted to an audience of product managers and executives in a company specializing in therapy, wound care, and telehealth software.

The final report must have the following structure:

### **Executive Summary**
A high-level overview of the most critical updates. Start with the change to the payment conversion factor. Then, briefly mention 2-3 other major policy changes, such as telehealth extensions, new caregiver codes, or E/M visit complexity changes.

---

### **Detailed Regulatory Analysis**
Organize all relevant extracted information under the following specific subheadings. Combine related points and present the information in a coherent way. Use bullet points for lists of changes.

**1. Payment and Reimbursement Updates**
   - **Conversion Factor:** State the new CF and compare it to the previous year.
   - **Therapy Threshold (KX Modifier):** Detail the new threshold amounts for PT/SLP and OT. Mention the medical review threshold.
   - **Clinical Labor & RVUs:** Briefly mention any updates to clinical labor rates or RVUs.

**2. Telehealth Policies**
   - **Service Eligibility:** Explain the status of therapy services on the telehealth list (e.g., provisional, temporary).
   - **Practitioner Eligibility:** Clarify the status of therapists (PT, OT, SLP) as eligible telehealth providers.
   - **Supervision:** Describe the policy for virtual direct supervision.
   - **Modifiers and POS Codes:** Summarize the rules for using POS 02, POS 10, and Modifier 95, especially for therapy services.

**3. Therapy-Specific Updates (PT, OT, SLP)**
   - **New or Revised Codes:** Detail any new codes relevant to therapy, such as Caregiver Training (97550, 97551, 97552).
   - **Potentially Misvalued Codes:** Mention if therapy codes have been nominated for review.

**4. Other Key Policy Changes**
   - **Split (or Shared) E/M Visits:** Explain the current definition of "substantive portion."
   - **Drug-Related Modifiers (JW/JZ):** Briefly mention any updates related to tracking discarded drugs.
   - **Skin Substitutes:** Describe the latest CMS stance on payment and coding for these products.

---

### **Action Items for Stakeholders**
Based on the analysis, create a bulleted list of actionable tasks for our company and our customers. For example:
- "Update billing systems with the CY {year} conversion factor of ${{amount}}."
- "Educate therapy providers on the continued use of Modifier 95 for telehealth claims through the end of {year}."
- "Incorporate new Caregiver Training CPT codes (97550-97552) into the therapy software platform."
- "Notify customers about the increased KX modifier threshold of ${{amount}} for PT/SLP and OT."

[Start of structured data]
{summaries}
[End of structured data]
"""

# -------- Summarization Function (Handles new prompts) --------
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

    # Note: The 'year' is passed into the format string here.
    joined_summaries = json.dumps(individual_summaries, indent=2)
    final_prompt = FINAL_REPORT_PROMPT.format(summaries=joined_summaries, year=file_name[:4])

    try:
        print("\n🔄 Generating final intelligence report...")
        final_response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": final_prompt}],
            temperature=0.2,
        )
        final_report = final_response.choices[0].message.content.strip()
        print("✅ Final report generated successfully.")
        return final_report
    except Exception as e:
        print(f"❌ An unexpected error occurred during final report generation: {e}")
        return f"Final synthesis failed. Raw chunk data below:\n\n{joined_summaries}"

# -------- Main Execution Block (with File Selection) --------
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

    source_files_list = sorted(list(chunks_by_source_file.keys())) # Sort for consistent order
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

    # Heuristic to find dates. A more robust solution might involve a dedicated metadata extraction step.
    release_date = "Not Found"
    effective_date = "Not Found"
    for chunk in chunks_for_selected_file[:10]: # Check first 10 chunks for speed
        text = (chunk.get('page_content') or chunk.get('text', '')).lower()
        if "released:" in text:
            release_date = text.split("released:")[1].split("\n")[0].strip()
        if "effective:" in text:
            effective_date = text.split("effective:")[1].split("\n")[0].strip()

    print(f"\n--- Starting processing for: {selected_file} ---")
    report_result = generate_report(chunks_for_selected_file, selected_file)

    # --- Display Final Report ---
    print(f"\n============================================================")
    print(f" Business Intelligence Report: {selected_file}")
    print(f"============================================================")
    print(f"**Rule Released:** {release_date.title()}")
    print(f"**Effective Date:** {effective_date.title()}")
    print("---")
    print(report_result)
    print("\n------------------------------------------------------------\n")

    print("Selected document has been processed.")
