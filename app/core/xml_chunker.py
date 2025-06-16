"""
xml_chunker.py

Module for chunking XML documents into smaller pieces for processing.
"""
import os
import re
import json
import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------- CONFIG --------
INPUT_DIR = Path("./data")
CHUNK_WORDS = 500
OVERLAP_SENTENCES = 1
OUTPUT_CHUNKS = "./rag_data/chunks.json"

class XMLChunker:
    """
    Class for chunking XML documents into smaller pieces.
    
    Attributes:
        input_dir (Path): Directory containing XML files
        chunk_words (int): Maximum words per chunk
        overlap_sentences (int): Number of sentences to overlap between chunks
        output_chunks (str): Path to save chunked data
    """
    
    def __init__(self, input_dir: str = "./data", chunk_words: int = 500, 
                 overlap_sentences: int = 1, output_chunks: str = "./rag_data/chunks.json"):
        """
        Initialize XMLChunker.
        
        Args:
            input_dir: Directory containing XML files
            chunk_words: Maximum words per chunk
            overlap_sentences: Number of sentences to overlap between chunks
            output_chunks: Path to save chunked data
        """
        self.input_dir = Path(input_dir)
        self.chunk_words = chunk_words
        self.overlap_sentences = overlap_sentences
        self.output_chunks = output_chunks
        logger.info(f"Initialized XMLChunker with input_dir: {self.input_dir.absolute()}")

    def clean_text(self, text: str) -> str:
        """Clean text by removing extra whitespace."""
        if text is None:
            return ""
        return re.sub(r'\s+', ' ', text.strip())

    def infer_metadata_from_filename(self, filename: str) -> Dict:
        """Extract metadata from filename."""
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

    def extract_preamb_metadata(self, root: ET.Element) -> Dict:
        """Extract metadata from preamble."""
        meta = {}
        meta["title"] = self.clean_text(root.findtext(".//SUBJECT"))
        meta["document_id"] = self.clean_text(root.findtext(".//DEPDOC"))
        meta["cfr"] = self.clean_text(root.findtext(".//CFR"))
        meta["effective_date"] = self.clean_text(root.findtext(".//EFFDATE/P"))
        return meta

    def chunk_document(self, root: ET.Element, metadata: Dict) -> List[Dict]:
        """Chunk document into smaller pieces."""
        chunks = []
        section_stack = []
        current_text = []
        chunk_index = 0
        last_chunk_sentences = []

        def current_section():
            return " > ".join(section_stack)

        for elem in root.iter():
            if elem.tag == "HD":
                text = self.clean_text(elem.text)
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
                para = self.clean_text(elem.text)
                if para:
                    current_text.append(para)
                    word_count = sum(len(p.split()) for p in current_text)
                    if word_count >= self.chunk_words:
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
                        last_chunk_sentences = chunk_text.split(". ")[:self.overlap_sentences]
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

    def process_files(self) -> List[Dict]:
        """Process all XML files in input directory."""
        all_chunks = []
        processed_files = []

        logger.info(f"Searching for XML files in {self.input_dir.absolute()}")
        xml_files = list(self.input_dir.rglob("*.xml"))
        logger.info(f"Found {len(xml_files)} XML files")

        for file_path in xml_files:
            relative_path = file_path.relative_to(self.input_dir)
            
            if relative_path.parent == Path("."):
                logger.info(f"⏭️ Skipping root file: {file_path.name}")
                continue
            
            try:
                logger.info(f"📄 Processing {file_path.name} from {relative_path.parent}...")
                
                inferred_meta = self.infer_metadata_from_filename(file_path.name)
                root = ET.parse(file_path).getroot()
                doc_meta = self.extract_preamb_metadata(root)
                full_meta = {**inferred_meta, **doc_meta}
                
                full_meta["subfolder"] = str(relative_path.parent)
                full_meta["full_path"] = str(file_path)
                
                chunks = self.chunk_document(root, full_meta)
                all_chunks.extend(chunks)
                processed_files.append(file_path)
                
                logger.info(f"   ✅ Created {len(chunks)} chunks")
                
            except Exception as e:
                logger.error(f"   ❌ Error processing {file_path.name}: {e}")

        return all_chunks

    def save_chunks(self, chunks: List[Dict]) -> None:
        """Save chunks to output file."""
        os.makedirs(os.path.dirname(self.output_chunks), exist_ok=True)
        with open(self.output_chunks, "w") as f:
            json.dump(chunks, f, indent=2)
        logger.info(f"📦 Saved chunks to {self.output_chunks}")

# -------- MAIN BATCH RUNNER --------
if __name__ == "__main__":
    chunker = XMLChunker()
    all_chunks = chunker.process_files()
    chunker.save_chunks(all_chunks)
    logger.info(f"✅ Processed {len(all_chunks)} chunks from {len(list(INPUT_DIR.rglob('*.xml')))} files.")