import os
import re
import json
import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict

# -------- CONFIG --------
INPUT_DIR = Path("./data")
CHUNK_WORDS = 500
OVERLAP_SENTENCES = 1
OUTPUT_CHUNKS = "./rag_data/chunks.json"

# -------- HELPERS --------
def clean_text(text):
    if text is None:
        return ""
    return re.sub(r'\s+', ' ', text.strip())

def infer_metadata_from_filename(filename: str) -> Dict:
    base = os.path.basename(filename).lower()
    year_match = re.search(r'(20\d{2})', base)
    year = int(year_match.group(1)) if year_match else None
    rule_type = "Proposed" if "proposed" in base else "Final" if "final" in base else "Unknown"
    if "hospice" in base:
        program = "Hospice"
    elif "snf" in base:
        program = "SNF"
    elif "mpfs" in base:
        program = "MPFS"
    else:
        program = "Unknown"
    return {
        "source_file": filename,
        "program": program,
        "rule_type": rule_type,
        "year": year
    }

def extract_preamb_metadata(root: ET.Element) -> Dict:
    meta = {}
    meta["title"] = clean_text(root.findtext(".//SUBJECT"))
    meta["document_id"] = clean_text(root.findtext(".//DEPDOC"))
    meta["cfr"] = clean_text(root.findtext(".//CFR"))
    meta["effective_date"] = clean_text(root.findtext(".//EFFDATE/P"))
    return meta

def chunk_document(root: ET.Element, metadata: Dict, max_chunk_words=CHUNK_WORDS, overlap_sentences=OVERLAP_SENTENCES) -> List[Dict]:
    chunks = []
    section_stack = []
    current_text = []
    chunk_index = 0
    last_chunk_sentences = []

    def current_section():
        return " > ".join(section_stack)

    for elem in root.iter():
        if elem.tag == "HD":
            text = clean_text(elem.text)
            if not text:
                continue
            level = elem.attrib.get("SOURCE", "")
            if level.startswith("HD1"):
                section_stack = [text]
            elif level.startswith("HD2"):
                section_stack = section_stack[:1] + [text]
            elif level.startswith("HD3"):
                section_stack = section_stack[:2] + [text]
            else:
                section_stack = [text]
        elif elem.tag == "P":
            para = clean_text(elem.text)
            if para:
                current_text.append(para)
                word_count = sum(len(p.split()) for p in current_text)
                if word_count >= max_chunk_words:
                    chunk_text = " ".join(current_text)
                    if last_chunk_sentences:
                        chunk_text = " ".join(last_chunk_sentences) + " " + chunk_text
                    chunk_hash = hashlib.sha256(chunk_text.encode()).hexdigest()
                    chunks.append({
                        "text": chunk_text,
                        "section_header": current_section(),
                        "chunk_index": chunk_index,
                        "hash": chunk_hash,
                        "metadata": metadata.copy()
                    })
                    last_chunk_sentences = chunk_text.split(". ")[:overlap_sentences]
                    current_text = []
                    chunk_index += 1

    if current_text:
        chunk_text = " ".join(current_text)
        if last_chunk_sentences:
            chunk_text = " ".join(last_chunk_sentences) + " " + chunk_text
        chunk_hash = hashlib.sha256(chunk_text.encode()).hexdigest()
        chunks.append({
            "text": chunk_text,
            "section_header": current_section(),
            "chunk_index": chunk_index,
            "hash": chunk_hash,
            "metadata": metadata.copy()
        })

    return chunks

# -------- MAIN BATCH RUNNER --------
all_chunks = []
processed_files = []  # Track all processed files

# Method 1: Skip files in root directory, only process subdirectories
for file_path in INPUT_DIR.rglob("*.xml"):
    # Get relative path from INPUT_DIR
    relative_path = file_path.relative_to(INPUT_DIR)
    
    # Skip files in the root directory (no subdirectory)
    if relative_path.parent == Path("."):
        print(f"⏭️ Skipping root file: {file_path.name}")
        continue
    
    try:
        print(f"📄 Processing {file_path.name} from {relative_path.parent}...")
        
        inferred_meta = infer_metadata_from_filename(file_path.name)
        root = ET.parse(file_path).getroot()
        doc_meta = extract_preamb_metadata(root)
        full_meta = {**inferred_meta, **doc_meta}
        
        # Add subfolder information
        full_meta["subfolder"] = str(relative_path.parent)
        full_meta["full_path"] = str(file_path)
        
        chunks = chunk_document(root, full_meta)
        all_chunks.extend(chunks)
        processed_files.append(file_path)
        
        print(f"   ✅ Created {len(chunks)} chunks")
        
    except Exception as e:
        print(f"   ❌ Error processing {file_path.name}: {e}")

# Save output
os.makedirs("rag_data", exist_ok=True)  # Ensure the folder exists
with open(OUTPUT_CHUNKS, "w") as f:
    json.dump(all_chunks, f, indent=2)

print(f"✅ Processed {len(all_chunks)} chunks from {len(list(INPUT_DIR.rglob('*.xml')))} files.")
print(f"📦 Saved chunks to {OUTPUT_CHUNKS}")