"""
incremental_chunker.py

Incremental XML chunking based on optimized XMLChunker.
Provides CRUD operations for individual XML files with change detection and tracking.
"""
import os
import json
import hashlib
import logging
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Add the app directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from xml_chunker import XMLChunker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IncrementalChunker:
    """
    Incremental XML chunker that extends XMLChunker with file tracking and change detection.
    
    Provides CRUD operations:
    - Create: Process new XML files
    - Read: Load existing chunks and tracking data  
    - Update: Re-process modified XML files
    - Delete: Remove chunks for deleted XML files
    """
    
    def __init__(self, chunk_words: int = None, overlap_sentences: int = None):
        """
        Initialize IncrementalChunker.
        
        Args:
            chunk_words: Words per chunk (from config if None)
            overlap_sentences: Sentence overlap (from config if None)
        """
        # Initialize base chunker with optimized logic
        self.chunker = XMLChunker(
            chunk_words=chunk_words or config.chunk_words,
            overlap_sentences=overlap_sentences or config.overlap_sentences
        )
        
        # Paths for tracking and output
        self.data_dir = Path(config.docs_data_path)
        self.output_dir = Path(config.build_faiss_output_folder)
        self.processed_files_path = self.output_dir / "processed_files.json"
        self.chunks_path = self.output_dir / "chunks.json"
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load tracking data
        self._processed_files = self._load_processed_files()
        
        logger.info(f"🚀 Initialized IncrementalChunker")
        logger.info(f"📁 Data directory: {self.data_dir}")
        logger.info(f"📁 Output directory: {self.output_dir}")

    def _load_processed_files(self) -> Dict:
        """Load processed files tracking data."""
        if self.processed_files_path.exists():
            try:
                with open(self.processed_files_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"⚠️ Error loading processed files: {e}, starting fresh")
                return {}
        return {}
    
    def _save_processed_files(self) -> None:
        """Save processed files tracking data."""
        try:
            with open(self.processed_files_path, 'w') as f:
                json.dump(self._processed_files, f, indent=2)
        except IOError as e:
            logger.error(f"❌ Error saving processed files: {e}")
            raise

    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file for change detection."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except IOError as e:
            logger.error(f"❌ Error calculating hash for {file_path}: {e}")
            raise

    def _get_relative_path(self, file_path: Path) -> str:
        """Get relative path from data directory."""
        try:
            return str(file_path.relative_to(self.data_dir))
        except ValueError:
            return str(file_path)

    def find_xml_files(self) -> List[Path]:
        """Find all XML files in data directory."""
        if not self.data_dir.exists():
            logger.warning(f"⚠️ Data directory not found: {self.data_dir}")
            return []
        
        xml_files = []
        for xml_file in self.data_dir.rglob("*.xml"):
            # Skip root-level files (common pattern in this project)
            if xml_file.parent == self.data_dir:
                continue
            xml_files.append(xml_file)
        
        return sorted(xml_files)

    def find_new_or_modified_files(self) -> List[Path]:
        """Find XML files that are new or have been modified."""
        all_files = self.find_xml_files()
        new_or_modified = []
        
        for file_path in all_files:
            relative_path = self._get_relative_path(file_path)
            current_hash = self._get_file_hash(file_path)
            
            # Check if file is new or modified
            file_info = self._processed_files.get(relative_path)
            if not file_info or file_info.get('hash') != current_hash:
                new_or_modified.append(file_path)
        
        return new_or_modified

    def find_deleted_files(self) -> List[str]:
        """Find files that were processed but no longer exist."""
        deleted_files = []
        
        for relative_path in list(self._processed_files.keys()):
            file_path = self.data_dir / relative_path
            if not file_path.exists():
                deleted_files.append(relative_path)
        
        return deleted_files

    def load_existing_chunks(self) -> List[Dict]:
        """Load existing chunks from chunks.json."""
        if self.chunks_path.exists():
            try:
                with open(self.chunks_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"⚠️ Error loading chunks: {e}")
                return []
        return []

    def save_chunks(self, chunks: List[Dict]) -> None:
        """Save chunks to chunks.json."""
        try:
            with open(self.chunks_path, 'w') as f:
                json.dump(chunks, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Saved {len(chunks)} chunks to {self.chunks_path}")
        except IOError as e:
            logger.error(f"❌ Error saving chunks: {e}")
            raise

    def process_single_file(self, file_path: str) -> Dict:
        """
        Process a single XML file and return chunks.
        Ensures all chunk metadata includes program, year, rule_type.
        """
        logger.info(f"📄 Processing file: {file_path}")
        absolute_path = self.data_dir / file_path
        if not absolute_path.exists():
            raise FileNotFoundError(f"File not found: {absolute_path}")
        try:
            # Always infer program/year/rule_type from filename
            inferred_meta = self.chunker.infer_metadata_from_filename(absolute_path.name)
            # Process file using optimized XMLChunker
            chunks = self.chunker.process_file(str(absolute_path))
            # Patch each chunk's metadata to ensure program/year/rule_type present
            for chunk in chunks:
                if "metadata" in chunk:
                    chunk["metadata"].update(inferred_meta)
            # Update tracking info
            current_hash = self._get_file_hash(absolute_path)
            self._processed_files[file_path] = {
                'hash': current_hash,
                'chunks_count': len(chunks),
                'processed_at': datetime.now().isoformat(),
                'file_size': absolute_path.stat().st_size
            }
            logger.info(f"✅ Processed {file_path}: {len(chunks)} chunks created")
            return {
                'file_path': file_path,
                'chunks': chunks,
                'chunks_count': len(chunks),
                'status': 'success'
            }
        except Exception as e:
            logger.error(f"❌ Error processing {file_path}: {e}")
            return {
                'file_path': file_path,
                'chunks': [],
                'chunks_count': 0,
                'status': 'error',
                'error': str(e)
            }

    def update_chunks_for_file(self, file_path: str) -> Dict:
        """
        Update chunks for a specific file (remove old + add new).
        Ensures all chunk metadata includes program, year, rule_type.
        """
        logger.info(f"🔄 Updating chunks for: {file_path}")
        try:
            # Step 1: Load existing chunks
            all_chunks = self.load_existing_chunks()
            original_count = len(all_chunks)
            # Step 2: Remove existing chunks for this file
            filtered_chunks = []
            removed_count = 0
            for chunk in all_chunks:
                source_file = chunk.get('metadata', {}).get('source_file', '')
                if source_file != Path(file_path).name:  # Keep chunks from other files
                    filtered_chunks.append(chunk)
                else:
                    removed_count += 1
            # Step 3: Process file to get new chunks
            process_result = self.process_single_file(file_path)
            if process_result['status'] != 'success':
                raise Exception(f"Failed to process file: {process_result.get('error', 'Unknown error')}")
            new_chunks = process_result['chunks']
            # Step 4: Add new chunks
            filtered_chunks.extend(new_chunks)
            # Step 5: Save updated chunks (atomic write)
            self.save_chunks(filtered_chunks)
            self._save_processed_files()
            logger.info(f"✅ Updated chunks for {file_path}: -{removed_count}, +{len(new_chunks)}")
            return {
                'file_path': file_path,
                'chunks_removed': removed_count,
                'chunks_added': len(new_chunks),
                'total_chunks': len(filtered_chunks),
                'status': 'success'
            }
        except Exception as e:
            logger.error(f"❌ Error updating chunks for {file_path}: {e}")
            return {
                'file_path': file_path,
                'chunks_removed': 0,
                'chunks_added': 0,
                'total_chunks': len(self.load_existing_chunks()),
                'status': 'error',
                'error': str(e)
            }

    def remove_chunks_for_file(self, file_path: str) -> Dict:
        """
        Remove all chunks for a specific file.
        
        Args:
            file_path: Path to XML file (relative to data directory)
            
        Returns:
            Dictionary with removal results
        """
        logger.info(f"🗑️ Removing chunks for: {file_path}")
        
        try:
            # Load existing chunks
            all_chunks = self.load_existing_chunks()
            original_count = len(all_chunks)
            
            # Filter out chunks for this file
            filtered_chunks = []
            removed_count = 0
            
            for chunk in all_chunks:
                source_file = chunk.get('metadata', {}).get('source_file', '')
                if source_file != Path(file_path).name:  # Keep chunks from other files
                    filtered_chunks.append(chunk)
                else:
                    removed_count += 1
            
            # Save filtered chunks
            self.save_chunks(filtered_chunks)
            
            # Remove from tracking
            if file_path in self._processed_files:
                del self._processed_files[file_path]
                self._save_processed_files()
            
            logger.info(f"✅ Removed {removed_count} chunks for {file_path}")
            
            return {
                'file_path': file_path,
                'chunks_removed': removed_count,
                'total_chunks_remaining': len(filtered_chunks),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"❌ Error removing chunks for {file_path}: {e}")
            return {
                'file_path': file_path,
                'chunks_removed': 0,
                'total_chunks_remaining': len(self.load_existing_chunks()),
                'status': 'error',
                'error': str(e)
            }

    def cleanup_deleted_files(self) -> Dict:
        """
        Clean up chunks and tracking data for deleted files.
        
        Returns:
            Dictionary with cleanup results
        """
        deleted_files = self.find_deleted_files()
        
        if not deleted_files:
            logger.info("✅ No deleted files to clean up")
            return {
                'deleted_files': [],
                'chunks_removed': 0,
                'status': 'success'
            }
        
        logger.info(f"🧹 Cleaning up {len(deleted_files)} deleted files")
        
        total_removed = 0
        errors = []
        
        for file_path in deleted_files:
            result = self.remove_chunks_for_file(file_path)
            if result['status'] == 'success':
                total_removed += result['chunks_removed']
            else:
                errors.append(f"{file_path}: {result.get('error', 'Unknown error')}")
        
        if errors:
            logger.warning(f"⚠️ Some cleanup operations failed: {errors}")
        
        return {
            'deleted_files': deleted_files,
            'chunks_removed': total_removed,
            'errors': errors,
            'status': 'success' if not errors else 'partial_success'
        }

    def process_new_files(self) -> Dict:
        """
        Process all new or modified files.
        
        Returns:
            Dictionary with processing results
        """
        new_files = self.find_new_or_modified_files()
        
        if not new_files:
            logger.info("✅ No new or modified files found")
            return {
                'processed_files': [],
                'total_chunks_added': 0,
                'errors': [],
                'status': 'success'
            }
        
        logger.info(f"📁 Processing {len(new_files)} new/modified files")
        
        # Load existing chunks
        all_chunks = self.load_existing_chunks()
        total_chunks_added = 0
        processed_files = []
        errors = []
        
        for file_path in new_files:
            relative_path = self._get_relative_path(file_path)
            
            # Update chunks for this file (handles both new and modified)
            result = self.update_chunks_for_file(relative_path)
            
            if result['status'] == 'success':
                total_chunks_added += result['chunks_added']
                processed_files.append(relative_path)
            else:
                errors.append(f"{relative_path}: {result.get('error', 'Unknown error')}")
        
        if errors:
            logger.warning(f"⚠️ Some files failed to process: {errors}")
        
        logger.info(f"✅ Processed {len(processed_files)} files, added {total_chunks_added} chunks")
        
        return {
            'processed_files': processed_files,
            'total_chunks_added': total_chunks_added,
            'errors': errors,
            'status': 'success' if not errors else 'partial_success'
        }

    def get_status(self) -> Dict:
        """Get current status of incremental chunker."""
        all_files = self.find_xml_files()
        new_files = self.find_new_or_modified_files()
        deleted_files = self.find_deleted_files()
        existing_chunks = self.load_existing_chunks()
        
        return {
            'total_xml_files': len(all_files),
            'processed_files': len(self._processed_files),
            'new_or_modified_files': len(new_files),
            'deleted_files': len(deleted_files),
            'total_chunks': len(existing_chunks),
            'data_directory': str(self.data_dir),
            'output_directory': str(self.output_dir),
            'chunks_file_exists': self.chunks_path.exists(),
            'tracking_file_exists': self.processed_files_path.exists()
        }


# -------- MAIN INCREMENTAL CHUNKER RUNNER --------
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Incremental XML chunker with CRUD operations")
    parser.add_argument("--file", "-f", type=str, help="Process specific file (relative to data directory)")
    parser.add_argument("--update", "-u", type=str, help="Update chunks for specific file")
    parser.add_argument("--remove", "-r", type=str, help="Remove chunks for specific file")
    parser.add_argument("--cleanup", "-c", action="store_true", help="Clean up deleted files")
    parser.add_argument("--process-new", "-n", action="store_true", help="Process all new/modified files")
    parser.add_argument("--status", "-s", action="store_true", help="Show system status")
    
    args = parser.parse_args()
    
    chunker = IncrementalChunker()
    
    if args.status:
        status = chunker.get_status()
        print("\n=== Incremental Chunker Status ===")
        for key, value in status.items():
            print(f"{key}: {value}")
    
    elif args.file:
        result = chunker.process_single_file(args.file)
        print(f"\nProcessed {args.file}:")
        print(f"Status: {result['status']}")
        print(f"Chunks: {result['chunks_count']}")
        if result['status'] == 'error':
            print(f"Error: {result['error']}")
    
    elif args.update:
        result = chunker.update_chunks_for_file(args.update)
        print(f"\nUpdated {args.update}:")
        print(f"Status: {result['status']}")
        print(f"Removed: {result['chunks_removed']}")
        print(f"Added: {result['chunks_added']}")
        if result['status'] == 'error':
            print(f"Error: {result['error']}")
    
    elif args.remove:
        result = chunker.remove_chunks_for_file(args.remove)
        print(f"\nRemoved chunks for {args.remove}:")
        print(f"Status: {result['status']}")
        print(f"Chunks removed: {result['chunks_removed']}")
        if result['status'] == 'error':
            print(f"Error: {result['error']}")
    
    elif args.cleanup:
        result = chunker.cleanup_deleted_files()
        print(f"\nCleanup completed:")
        print(f"Status: {result['status']}")
        print(f"Deleted files: {len(result['deleted_files'])}")
        print(f"Chunks removed: {result['chunks_removed']}")
        if result['errors']:
            print(f"Errors: {result['errors']}")
    
    elif args.process_new:
        result = chunker.process_new_files()
        print(f"\nProcessed new files:")
        print(f"Status: {result['status']}")
        print(f"Files processed: {len(result['processed_files'])}")
        print(f"Chunks added: {result['total_chunks_added']}")
        if result['errors']:
            print(f"Errors: {result['errors']}")
    
    else:
        print("Please specify an operation. Use --help for options.")
        parser.print_help()