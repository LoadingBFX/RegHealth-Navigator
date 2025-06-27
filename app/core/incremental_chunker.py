"""
incremental_chunker.py

Module for incrementally chunking single XML documents and updating the existing chunks database.
"""
import os
import re
import json
import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional, Any
import logging
import sys

# Add the app directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IncrementalChunker:
    """
    Class for incrementally chunking single XML documents.
    
    This class extends the functionality of XMLChunker to support:
    - Processing single files
    - Updating existing chunks database
    - Tracking processed files
    """
    
    def __init__(self, input_dir: str = None, chunk_words: int = 500, 
                 overlap_sentences: int = 1, output_chunks: str = None):
        """
        Initialize IncrementalChunker.
        
        Args:
            input_dir: Directory containing XML files (defaults to config.docs_data_path)
            chunk_words: Maximum words per chunk
            overlap_sentences: Number of sentences to overlap between chunks
            output_chunks: Path to save chunked data (defaults to config.build_faiss_output_folder/chunks.json)
        """
        if input_dir is None:
            self.input_dir = Path(config.docs_data_path)
        else:
            self.input_dir = Path(input_dir)
        
        if output_chunks is None:
            self.output_chunks = os.path.join(config.build_faiss_output_folder, "chunks.json")
        else:
            self.output_chunks = output_chunks
            
        self.chunk_words = chunk_words
        self.overlap_sentences = overlap_sentences
        self.processed_files_tracker = os.path.join(config.build_faiss_output_folder, "processed_files.json")
        
        logger.info(f"Initialized IncrementalChunker with input_dir: {self.input_dir.absolute()}")

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

    def load_existing_chunks(self) -> List[Dict]:
        """Load existing chunks from file."""
        if os.path.exists(self.output_chunks):
            with open(self.output_chunks, "r") as f:
                return json.load(f)
        return []

    def load_processed_files(self) -> Dict:
        """Load the list of processed files."""
        if os.path.exists(self.processed_files_tracker):
            with open(self.processed_files_tracker, "r") as f:
                return json.load(f)
        return {}

    def save_processed_files(self, processed_files: Dict) -> None:
        """Save the list of processed files."""
        os.makedirs(os.path.dirname(self.processed_files_tracker), exist_ok=True)
        with open(self.processed_files_tracker, "w") as f:
            json.dump(processed_files, f, indent=2)

    def get_file_hash(self, file_path: Path) -> str:
        """Get SHA256 hash of file content."""
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

    def is_file_processed(self, file_path: Path) -> bool:
        """Check if file has been processed and not modified."""
        processed_files = self.load_processed_files()
        file_key = str(file_path.relative_to(self.input_dir))
        
        if file_key not in processed_files:
            return False
            
        current_hash = self.get_file_hash(file_path)
        return processed_files[file_key]["hash"] == current_hash

    def process_single_file(self, file_path: Path) -> List[Dict]:
        """Process a single XML file and return chunks."""
        relative_path = file_path.relative_to(self.input_dir)
        
        if relative_path.parent == Path("."):
            logger.info(f"⏭️ Skipping root file: {file_path.name}")
            return []
        
        try:
            logger.info(f"📄 Processing {file_path.name} from {relative_path.parent}...")
            
            inferred_meta = self.infer_metadata_from_filename(file_path.name)
            root = ET.parse(file_path).getroot()
            doc_meta = self.extract_preamb_metadata(root)
            full_meta = {**inferred_meta, **doc_meta}
            
            full_meta["subfolder"] = str(relative_path.parent)
            full_meta["full_path"] = str(file_path)
            
            chunks = self.chunk_document(root, full_meta)
            logger.info(f"   ✅ Created {len(chunks)} chunks")
            
            return chunks
            
        except Exception as e:
            logger.error(f"   ❌ Error processing {file_path.name}: {e}")
            return []

    def update_chunks_database(self, new_chunks: List[Dict], file_path: Path) -> None:
        """Update the chunks database with new chunks."""
        # Load existing chunks
        existing_chunks = self.load_existing_chunks()
        
        # Remove chunks from the same file if they exist
        file_key = str(file_path.relative_to(self.input_dir))
        existing_chunks = [chunk for chunk in existing_chunks 
                          if chunk["metadata"].get("full_path") != str(file_path)]
        
        # Add new chunks
        existing_chunks.extend(new_chunks)
        
        # Save updated chunks
        os.makedirs(os.path.dirname(self.output_chunks), exist_ok=True)
        with open(self.output_chunks, "w") as f:
            json.dump(existing_chunks, f, indent=2)
        
        # Update processed files tracker
        processed_files = self.load_processed_files()
        processed_files[file_key] = {
            "hash": self.get_file_hash(file_path),
            "processed_at": str(Path(file_path).stat().st_mtime),
            "chunks_count": len(new_chunks)
        }
        self.save_processed_files(processed_files)
        
        logger.info(f"📦 Updated chunks database: {len(existing_chunks)} total chunks")

    def process_file_incrementally(self, file_path: str) -> List[Dict]:
        """
        Process a single file incrementally.
        
        Args:
            file_path: Path to the XML file (relative to input_dir or absolute)
            
        Returns:
            List of chunks created for the file
        """
        # Convert to Path object
        if os.path.isabs(file_path):
            file_path = Path(file_path)
        else:
            file_path = self.input_dir / file_path
        
        if not file_path.exists():
            logger.error(f"❌ File not found: {file_path}")
            return []
        
        # Check if file is already processed and unchanged
        if self.is_file_processed(file_path):
            logger.info(f"⏭️ File already processed and unchanged: {file_path.name}")
            return []
        
        # Process the file
        chunks = self.process_single_file(file_path)
        
        if chunks:
            # Update the database
            self.update_chunks_database(chunks, file_path)
            logger.info(f"✅ Successfully processed {file_path.name} with {len(chunks)} chunks")
        else:
            logger.warning(f"⚠️ No chunks created for {file_path.name}")
        
        return chunks

    def find_new_files(self) -> List[Path]:
        """Find files that haven't been processed or have been modified."""
        processed_files = self.load_processed_files()
        new_files = []
        
        xml_files = list(self.input_dir.rglob("*.xml"))
        
        for file_path in xml_files:
            relative_path = file_path.relative_to(self.input_dir)
            
            if relative_path.parent == Path("."):
                continue  # Skip root files
                
            file_key = str(relative_path)
            
            if file_key not in processed_files:
                new_files.append(file_path)
                logger.info(f"🆕 New file found: {file_path.name}")
            else:
                current_hash = self.get_file_hash(file_path)
                if processed_files[file_key]["hash"] != current_hash:
                    new_files.append(file_path)
                    logger.info(f"📝 Modified file found: {file_path.name}")
        
        return new_files

    def find_deleted_files(self) -> List[str]:
        """Find files that have been deleted from the data directory."""
        processed_files = self.load_processed_files()
        deleted_files = []
        
        for file_key in processed_files.keys():
            file_path = self.input_dir / file_key
            if not file_path.exists():
                deleted_files.append(file_key)
                logger.info(f"🗑️ Deleted file detected: {file_key}")
        
        return deleted_files

    def cleanup_deleted_files(self, deleted_files: List[str]) -> None:
        """Remove chunks and metadata for deleted files."""
        if not deleted_files:
            return
        
        # Load existing chunks
        existing_chunks = self.load_existing_chunks()
        processed_files = self.load_processed_files()
        
        # Count chunks to be removed
        chunks_to_remove = 0
        
        # Remove chunks from deleted files
        for file_key in deleted_files:
            # Remove from processed files tracker
            if file_key in processed_files:
                chunks_to_remove += processed_files[file_key].get("chunks_count", 0)
                del processed_files[file_key]
            
            # Remove chunks from the same file
            file_path = self.input_dir / file_key
            existing_chunks = [chunk for chunk in existing_chunks 
                              if chunk["metadata"].get("full_path") != str(file_path)]
        
        # Save updated data
        os.makedirs(os.path.dirname(self.output_chunks), exist_ok=True)
        with open(self.output_chunks, "w") as f:
            json.dump(existing_chunks, f, indent=2)
        
        self.save_processed_files(processed_files)
        
        logger.info(f"🧹 Cleaned up {len(deleted_files)} deleted files, removed {chunks_to_remove} chunks")

    def process_new_files(self) -> List[Dict]:
        """Process all new or modified files."""
        new_files = self.find_new_files()
        
        if not new_files:
            logger.info("✅ No new or modified files found")
            return []
        
        all_new_chunks = []
        for file_path in new_files:
            chunks = self.process_file_incrementally(str(file_path))
            all_new_chunks.extend(chunks)
        
        logger.info(f"✅ Processed {len(new_files)} files, created {len(all_new_chunks)} total chunks")
        return all_new_chunks

    def cleanup_and_process(self) -> Dict[str, Any]:
        """
        Clean up deleted files and process new/modified files.
        
        Returns:
            Dictionary with processing results
        """
        # First, clean up deleted files
        deleted_files = self.find_deleted_files()
        if deleted_files:
            self.cleanup_deleted_files(deleted_files)
        
        # Then process new/modified files
        new_files = self.find_new_files()
        all_new_chunks = []
        
        for file_path in new_files:
            chunks = self.process_file_incrementally(str(file_path))
            all_new_chunks.extend(chunks)
        
        return {
            "deleted_files": deleted_files,
            "new_files": [str(f.relative_to(self.input_dir)) for f in new_files],
            "new_chunks": all_new_chunks,
            "total_chunks_after_cleanup": len(self.load_existing_chunks())
        }


# -------- MAIN INCREMENTAL RUNNER --------
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Incrementally process XML files")
    parser.add_argument("--file", "-f", help="Process specific file (relative to data directory)")
    parser.add_argument("--all", "-a", action="store_true", help="Process all new/modified files")
    parser.add_argument("--list", "-l", action="store_true", help="List new/modified files without processing")
    
    args = parser.parse_args()
    
    chunker = IncrementalChunker()
    
    if args.list:
        new_files = chunker.find_new_files()
        if new_files:
            print(f"Found {len(new_files)} new/modified files:")
            for file_path in new_files:
                print(f"  - {file_path.relative_to(chunker.input_dir)}")
        else:
            print("No new or modified files found")
    
    elif args.file:
        chunks = chunker.process_file_incrementally(args.file)
        print(f"Processed {args.file}: {len(chunks)} chunks created")
    
    elif args.all:
        chunks = chunker.process_new_files()
        print(f"Processed all new files: {len(chunks)} total chunks created")
    
    else:
        print("Please specify --file, --all, or --list")
        parser.print_help() 