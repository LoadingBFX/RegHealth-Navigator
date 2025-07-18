"""
xml_chunker.py

Module for chunking XML documents into smaller pieces for processing.
Provides structure-aware XML parsing and intelligent text chunking.

Functionality:
- Structure-aware XML parsing for regulatory documents
- Intelligent text chunking with overlap management
- Footnote merging and reference resolution
- Special element handling (graphics, tables, billing codes)
- Metadata extraction from filenames and document content
- Logical block identification and section header generation
- HTML entity decoding and text normalization

Process Flow:
1. Parse XML document using ElementTree
2. Preprocess XML (merge footnotes, clean special elements)
3. Extract logical blocks based on structural elements
4. Generate section headers with document context
5. Split text into chunks with configurable word limits
6. Apply sentence overlap for context preservation
7. Extract metadata from filenames and document content
8. Save chunks with comprehensive metadata

Author: 
Previous Team, Dhruv, Fanxing Bu
"""
import os
import re
import json
import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional
import logging
import sys
import html

# Add the app directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------- CONFIG --------
# Use config for input directory path
INPUT_DIR = Path(config.docs_data_path)
CHUNK_WORDS = 500
OVERLAP_SENTENCES = 1
OUTPUT_CHUNKS = os.path.join(config.build_faiss_output_folder, "chunks.json")

# Structural elements that form logical blocks
STRUCTURAL_TAGS = {'SECTION', 'SUBPART', 'APPENDIX', 'CONTENTS', 'SUPLINF', 'PREAMB', 'REGTEXT'}
# Tags that contain meaningful content but are not primary structure
CONTENT_TAGS = {'P', 'E', 'NOTE'}
# Tags to ignore during chunking
IGNORED_TAGS = {'PRTPAGE', 'GPH', 'GID', 'BILCOD', 'FRDOC', 'STARS'}

class XMLChunker:
    """Enhanced XML chunker with structure-aware chunking strategy."""
    
    def __init__(self, chunk_words: int = CHUNK_WORDS, overlap_sentences: int = OVERLAP_SENTENCES):
        self.chunk_words = chunk_words
        self.overlap_sentences = overlap_sentences
        self.input_dir = INPUT_DIR
        self.output_chunks = OUTPUT_CHUNKS
    
    def clean_text(self, text: str) -> str:
        """Enhanced text cleaning function with HTML entity decoding and whitespace normalization."""
        if not text:
            return ""
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text
    
    def process_special_elements(self, elem: ET.Element) -> Optional[str]:
        """Process special XML elements and return appropriate text or None."""
        if elem.tag == "SU":
            # Handle superscript references
            return f"[{elem.text}]" if elem.text else ""
        elif elem.tag == "FTREF":
            # Handle footnote reference markers
            return "[footnote_ref]"
        elif elem.tag == "PRTPAGE":
            # Remove page number markers
            return ""
        elif elem.tag == "GPH":
            # Handle graphic/table placeholders
            gid = elem.find("GID")
            if gid is not None and gid.text:
                return f"[graphic/table: {gid.text}]"
            return "[graphic/table]"
        elif elem.tag == "BILCOD":
            # Remove billing codes
            return ""
        elif elem.tag == "FTNT":
            # Handle footnote content - avoid recursion
            text_parts = []
            if elem.text:
                text_parts.append(elem.text.strip())
            for child in elem:
                if child.text:
                    text_parts.append(child.text.strip())
                if child.tail:
                    text_parts.append(child.tail.strip())
            return ' '.join(part for part in text_parts if part)
        else:
            return None
    
    def extract_text_from_element(self, elem: ET.Element) -> str:
        """Enhanced text extraction from element and its children with special element handling."""
        # Handle special elements first
        special_text = self.process_special_elements(elem)
        if special_text is not None:
            return special_text
        
        # Use itertext() for safe text extraction
        text_parts = []
        
        # Get all text content from element and descendants
        all_text = list(elem.itertext())
        
        # Clean and join text parts
        for text in all_text:
            cleaned = self.clean_text(text)
            if cleaned:
                text_parts.append(cleaned)
        
        result = " ".join(text_parts)
        return result
    
    def merge_footnotes(self, root: ET.Element) -> Dict[str, str]:
        """Collect all footnotes and return a mapping of reference numbers to footnote text."""
        footnotes = {}
        
        for ftnt in root.findall(".//FTNT"):
            # Find the reference number in the footnote
            for su in ftnt.findall(".//SU"):
                ref_num = su.text
                if ref_num:
                    # Extract the footnote text (excluding the reference number itself)
                    footnote_text = self.extract_text_from_element(ftnt)
                    # Clean up the footnote text
                    footnote_text = re.sub(r'^\[\d+\]\s*', '', footnote_text)
                    footnotes[ref_num] = footnote_text.strip()
        
        return footnotes
    
    def replace_footnote_references(self, root: ET.Element, footnotes: Dict[str, str]) -> None:
        """Replace footnote references in the main text with actual footnote content."""
        for p in root.findall(".//P"):
            for su in p.findall(".//SU"):
                ref_num = su.text
                if ref_num and ref_num in footnotes:
                    # Replace the superscript reference with the footnote content
                    footnote_content = footnotes[ref_num]
                    if footnote_content:
                        # Create a new text element with the footnote content
                        su.text = f" ({footnote_content})"
    
    def preprocess_xml(self, root: ET.Element) -> None:
        """Preprocess XML to merge footnotes and clean up special elements."""
        # Collect and merge footnotes
        footnotes = self.merge_footnotes(root)
        self.replace_footnote_references(root, footnotes)
        
        # Skip element removal for now to avoid issues - we'll handle it in text extraction
        pass

    def extract_logical_blocks(self, root: ET.Element) -> List[Dict]:
        """Extract logical blocks based on structural elements."""
        logical_blocks = []
        
        # Extract document-level metadata for section headers
        doc_context = self.extract_document_context(root)
        
        # Find all structural elements
        for elem in root.iter():
            if elem.tag in STRUCTURAL_TAGS:
                block = self.process_structural_element(elem, doc_context)
                if block:
                    logical_blocks.append(block)
        
        return logical_blocks
    
    def extract_document_context(self, root: ET.Element) -> Dict:
        """Extract document-level context for building section headers."""
        context = {}
        
        # Extract REGTEXT information
        regtext = root.find('.//REGTEXT')
        if regtext is not None:
            context['title'] = regtext.get('TITLE', '')
            context['part'] = regtext.get('PART', '')
        
        # Extract PREAMB SUBJECT
        preamb_subject = root.find('.//PREAMB/SUBJECT')
        if preamb_subject is not None:
            context['document_subject'] = self.extract_text_from_element(preamb_subject)
        
        return context
    
    def process_structural_element(self, elem: ET.Element, doc_context: Dict) -> Optional[Dict]:
        """Process a structural element and extract its content block."""
        block_type = elem.tag
        header_parts = []
        content_paragraphs = []
        
        # Build section header based on element type
        if block_type == 'SECTION':
            # For SECTION: find SECTNO and SUBJECT
            sectno = elem.find('./SECTNO')
            subject = elem.find('./SUBJECT')
            
            if sectno is not None:
                sectno_text = self.extract_text_from_element(sectno)
                header_parts.append(sectno_text)
            
            if subject is not None:
                subject_text = self.extract_text_from_element(subject)
                header_parts.append(subject_text)
            
            # Extract all paragraphs in this section
            for p in elem.findall('.//P'):
                para_text = self.extract_text_from_element(p)
                if para_text:
                    content_paragraphs.append(para_text)
                    
        elif block_type == 'SUBPART':
            # For SUBPART: find HD header
            hd = elem.find('./HD')
            if hd is not None:
                hd_text = self.extract_text_from_element(hd)
                header_parts.append(hd_text)
            
            # Extract content from all child elements
            for child in elem:
                if child.tag not in {'HD'}:  # Skip the header we already processed
                    text = self.extract_text_from_element(child)
                    if text:
                        content_paragraphs.append(text)
                        
        elif block_type == 'APPENDIX':
            # For APPENDIX: find HD header
            hd = elem.find('./HD')
            if hd is not None:
                hd_text = self.extract_text_from_element(hd)
                header_parts.append(hd_text)
            
            # Extract all paragraphs and notes
            for p in elem.findall('.//P'):
                para_text = self.extract_text_from_element(p)
                if para_text:
                    content_paragraphs.append(para_text)
                    
        elif block_type == 'CONTENTS':
            # For CONTENTS: extract the table of contents structure
            header_parts.append('Contents')
            
            # Extract all content elements
            for child in elem.iter():
                if child.tag in {'SECTNO', 'SUBJECT', 'HD'}:
                    text = self.extract_text_from_element(child)
                    if text:
                        content_paragraphs.append(text)
                        
        elif block_type == 'SUPLINF':
            # For SUPLINF: Supplementary Information section
            header_parts.append('Supplementary Information')
            
            # Extract all paragraphs and headers within SUPLINF
            for p in elem.findall('.//P'):
                para_text = self.extract_text_from_element(p)
                if para_text:
                    content_paragraphs.append(para_text)
                    
        elif block_type == 'PREAMB':
            # For PREAMB: Preamble section
            header_parts.append('Preamble')
            
            # Extract all paragraphs in preamble
            for p in elem.findall('.//P'):
                para_text = self.extract_text_from_element(p)
                if para_text:
                    content_paragraphs.append(para_text)
                    
        elif block_type == 'REGTEXT':
            # For REGTEXT: Regulatory Text - main content
            header_parts.append('Regulatory Text')
            
            # Extract all content from regulatory text
            for p in elem.findall('.//P'):
                para_text = self.extract_text_from_element(p)
                if para_text:
                    content_paragraphs.append(para_text)
        
        # Build complete section header
        section_header = self.build_section_header(header_parts, doc_context, block_type)
        
        # Combine all content
        full_text = ' '.join(content_paragraphs)
        
        if not full_text.strip():
            return None
            
        return {
            'header': section_header,
            'text': full_text,
            'type': block_type,
            'word_count': len(full_text.split())
        }
    
    def build_section_header(self, header_parts: List[str], doc_context: Dict, block_type: str) -> str:
        """Build comprehensive section header following the format: TITLE + PART > SUBPART > SECTNO + SUBJECT."""
        header_components = []
        
        # Add document-level context
        if doc_context.get('title') and doc_context.get('part'):
            header_components.append(f"{doc_context['title']} CFR Part {doc_context['part']}")
        
        # Add block-specific header
        if header_parts:
            if block_type == 'SECTION' and len(header_parts) >= 2:
                # Format: § sectno subject
                header_components.append(f"§ {header_parts[0]} {header_parts[1]}")
            else:
                header_components.extend(header_parts)
        
        return ' > '.join(header_components) if header_components else f'{block_type}'
    
    def split_into_chunks_with_overlap(self, text: str, max_words: int, overlap_sentences: int) -> List[str]:
        """Split text into chunks with sentence-level overlap."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = []
        current_words = 0
        
        for sentence in sentences:
            sentence_words = len(sentence.split())
            
            # If adding this sentence exceeds max_words and we have content, start new chunk
            if current_words + sentence_words > max_words and current_chunk:
                chunks.append(' '.join(current_chunk))
                
                # Start new chunk with overlap from previous chunk
                overlap_start = max(0, len(current_chunk) - overlap_sentences)
                current_chunk = current_chunk[overlap_start:] + [sentence]
                current_words = sum(len(s.split()) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_words += sentence_words
        
        # Add the final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def chunk_document(self, root: ET.Element, metadata: Dict) -> List[Dict]:
        """Enhanced structure-aware document chunking strategy."""
        # Preprocess the XML to handle footnotes and special elements
        self.preprocess_xml(root)
        
        # Extract logical blocks
        logical_blocks = self.extract_logical_blocks(root)
        
        chunks = []
        chunk_index = 0
        
        for block in logical_blocks:
            section_header = block['header']
            text = block['text']
            word_count = block['word_count']
            
            if word_count <= self.chunk_words:
                # Block fits in single chunk
                chunks.append({
                    'text': text,
                    'section_header': section_header,
                    'metadata': {
                        **metadata,
                        'chunk_id': chunk_index,
                        'block_type': block['type'],
                        'word_count': word_count
                    }
                })
                chunk_index += 1
            else:
                # Split large block into multiple chunks with overlap
                sub_chunks = self.split_into_chunks_with_overlap(
                    text, self.chunk_words, self.overlap_sentences
                )
                
                for i, sub_chunk in enumerate(sub_chunks):
                    chunks.append({
                        'text': sub_chunk,
                        'section_header': section_header,
                        'metadata': {
                            **metadata,
                            'chunk_id': chunk_index,
                            'sub_chunk_index': i,
                            'total_sub_chunks': len(sub_chunks),
                            'block_type': block['type'],
                            'word_count': len(sub_chunk.split())
                        }
                    })
                    chunk_index += 1
        
        return chunks

    def process_file(self, file_path: str) -> List[Dict]:
        """Process a single XML file with enhanced text extraction. Always include program, year, rule_type in metadata."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            # Always infer program/year/rule_type from filename
            inferred_meta = self.infer_metadata_from_filename(os.path.basename(file_path))
            metadata = {
                "source_file": os.path.basename(file_path),
                "file_type": "xml",
                "processing_version": "2.0"
            }
            metadata.update(inferred_meta)
            # Extract additional metadata from XML structure
            agency = root.find(".//AGENCY")
            if agency is not None:
                metadata["agency"] = agency.text
            subject = root.find(".//SUBJECT")
            if subject is not None:
                metadata["subject"] = subject.text
            return self.chunk_document(root, metadata)
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            return []

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

    def process_files(self) -> List[Dict]:
        """Process all XML files in input directory. Always include program, year, rule_type in metadata."""
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
                # Always ensure program/year/rule_type present
                if "program" not in full_meta or "year" not in full_meta or "rule_type" not in full_meta:
                    fallback = self.infer_metadata_from_filename(file_path.name)
                    full_meta.update(fallback)
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