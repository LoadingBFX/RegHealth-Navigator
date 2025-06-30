"""
incremental_pipeline.py

Complete incremental processing pipeline for new XML files.
Combines chunking and FAISS index updating in a single workflow.
"""
import os
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any

# Add the app directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from incremental_chunker import IncrementalChunker
from incremental_faiss import IncrementalFAISS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IncrementalPipeline:
    """
    Complete incremental processing pipeline.
    
    This class orchestrates the entire incremental update process:
    1. Find new or modified XML files
    2. Process them into chunks
    3. Update FAISS index with new embeddings
    4. Update metadata files
    """
    
    def __init__(self, model: str = None):
        """
        Initialize the incremental pipeline.
        
        Args:
            model: Embedding model to use. If None, uses default from config.
                   Available models are defined in config files.
        """
        self.chunker = IncrementalChunker()
        self.faiss_updater = IncrementalFAISS(model=model)
        self.model = model if model else config.default_embedding_model
        logger.info(f"🚀 Initialized Incremental Pipeline with model: {self.model}")

    def process_single_file(self, file_path: str) -> Dict:
        """
        Process a single XML file through the complete pipeline.
        
        Args:
            file_path: Path to the XML file (relative to data directory or absolute)
            
        Returns:
            Dictionary with processing statistics
        """
        logger.info(f"🔄 Starting incremental processing for: {file_path}")
        
        # Step 1: Process file into chunks
        chunks = self.chunker.process_file_incrementally(file_path)
        
        if not chunks:
            logger.warning(f"⚠️ No chunks created for {file_path}")
            return {
                "file": file_path,
                "chunks_created": 0,
                "embeddings_added": 0,
                "estimated_cost": -1.0,
                "status": "no_chunks"
            }
        
        # Step 2: Update FAISS index with new chunks
        faiss_stats = self.faiss_updater.process_incremental_update(chunks)
        
        # Combine statistics
        result = {
            "file": file_path,
            "chunks_created": len(chunks),
            "embeddings_added": faiss_stats["new_embeddings_added"],
            "total_tokens": faiss_stats["total_tokens"],
            "estimated_cost": faiss_stats["estimated_cost"],
            "status": "success"
        }
        
        logger.info(f"✅ Completed incremental processing for {file_path}")
        logger.info(f"   - Chunks: {result['chunks_created']}")
        logger.info(f"   - Embeddings: {result['embeddings_added']}")
        logger.info(f"   - Cost: ${result['estimated_cost']}")
        
        return result

    def process_new_files(self) -> List[Dict]:
        """
        Process all new or modified files through the complete pipeline.
        
        Returns:
            List of processing results for each file
        """
        logger.info("🔄 Starting batch incremental processing")
        
        # Find new files
        new_files = self.chunker.find_new_files()
        
        if not new_files:
            logger.info("✅ No new or modified files found")
            return []
        
        # Process each file
        results = []
        for file_path in new_files:
            relative_path = str(file_path.relative_to(self.chunker.input_dir))
            result = self.process_single_file(relative_path)
            results.append(result)
        
        # Summary
        total_chunks = sum(r["chunks_created"] for r in results)
        total_embeddings = sum(r["embeddings_added"] for r in results)
        total_cost = sum(r["estimated_cost"] for r in results)
        
        logger.info(f"✅ Batch processing completed:")
        logger.info(f"   - Files processed: {len(results)}")
        logger.info(f"   - Total chunks: {total_chunks}")
        logger.info(f"   - Total embeddings: {total_embeddings}")
        logger.info(f"   - Total cost: ${total_cost:.4f}")
        
        return results

    def cleanup_and_process(self) -> Dict[str, Any]:
        """
        Clean up deleted files and process new/modified files.
        
        Returns:
            Dictionary with comprehensive processing results
        """
        logger.info("🔄 Starting cleanup and processing")
        
        # Step 1: Clean up deleted files
        deleted_files = self.chunker.find_deleted_files()
        if deleted_files:
            logger.info(f"🗑️ Found {len(deleted_files)} deleted files to clean up")
            self.chunker.cleanup_deleted_files(deleted_files)
            
            # Update FAISS index to remove embeddings for deleted files
            # Use the more efficient method that doesn't require API calls
            logger.info("🔄 Rebuilding FAISS index after file deletion (no API calls)")
            rebuild_result = self.faiss_updater.rebuild_index_from_existing_embeddings()
            if "error" in rebuild_result:
                logger.warning(f"⚠️ Efficient rebuild failed: {rebuild_result['error']}")
                logger.info("🔄 Falling back to full rebuild with API calls")
                rebuild_result = self.faiss_updater.rebuild_index_from_chunks()
        else:
            logger.info("✅ No deleted files found")
            rebuild_result = {"embeddings_kept": 0, "embeddings_removed": 0}
        
        # Step 2: Process new/modified files
        new_files = self.chunker.find_new_files()
        results = []
        
        for file_path in new_files:
            relative_path = str(file_path.relative_to(self.chunker.input_dir))
            result = self.process_single_file(relative_path)
            results.append(result)
        
        # Get final system status
        final_status = self.get_system_status()
        
        return {
            "deleted_files": deleted_files,
            "new_files": [str(f.relative_to(self.chunker.input_dir)) for f in new_files],
            "processing_results": results,
            "rebuild_result": rebuild_result,
            "final_status": final_status
        }

    def get_system_status(self) -> Dict:
        """Get comprehensive status of the system."""
        # Get chunker status
        processed_files = self.chunker.load_processed_files()
        existing_chunks = self.chunker.load_existing_chunks()
        
        # Get FAISS status
        faiss_stats = self.faiss_updater.get_index_stats()
        
        # Find new files
        new_files = self.chunker.find_new_files()
        
        # Find deleted files
        deleted_files = self.chunker.find_deleted_files()
        
        return {
            "processed_files_count": len(processed_files),
            "total_chunks": len(existing_chunks),
            "new_files_count": len(new_files),
            "deleted_files_count": len(deleted_files),
            "faiss_index_size": faiss_stats.get("index_size", 0),
            "faiss_index_dimension": faiss_stats.get("index_dimension", 0),
            "metadata_entries": faiss_stats.get("metadata_entries", 0),
            "new_files": [str(f.relative_to(self.chunker.input_dir)) for f in new_files],
            "deleted_files": deleted_files
        }

    def validate_system(self) -> Dict:
        """Validate the system state and identify any issues."""
        issues = []
        warnings = []
        
        # Check if chunks.json exists
        if not os.path.exists(self.chunker.output_chunks):
            issues.append("chunks.json not found - run full processing first")
        
        # Check if FAISS index exists
        if not os.path.exists(self.faiss_updater.faiss_index_path):
            issues.append("FAISS index not found - run full processing first")
        
        # Check if metadata exists
        if not os.path.exists(self.faiss_updater.metadata_path):
            issues.append("FAISS metadata not found - run full processing first")
        
        # Check for mismatched counts
        if os.path.exists(self.chunker.output_chunks) and os.path.exists(self.faiss_updater.metadata_path):
            with open(self.chunker.output_chunks, "r") as f:
                chunks = json.load(f)
            with open(self.faiss_updater.metadata_path, "r") as f:
                metadata = json.load(f)
            
            if len(chunks) != len(metadata):
                warnings.append(f"Chunk count mismatch: chunks.json has {len(chunks)}, metadata has {len(metadata)}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }


# -------- MAIN PIPELINE RUNNER --------
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Incremental processing pipeline")
    parser.add_argument("--cleanup", action="store_true", 
                      help="Clean up deleted files and rebuild index")
    parser.add_argument("--model", "-m", 
                      type=str,
                      help="Embedding model to use (defaults to config default)")
    parser.add_argument("--file", "-f", type=str,
                      help="Process a single file")
    parser.add_argument("--status", action="store_true",
                      help="Show system status")
    parser.add_argument("--validate", action="store_true",
                      help="Validate system state")
    
    args = parser.parse_args()
    
    # Initialize pipeline with specified model
    pipeline = IncrementalPipeline(model=args.model)
    
    if args.status:
        status = pipeline.get_system_status()
        print("\n=== System Status ===")
        print(f"Model: {pipeline.model}")
        print(f"Processed files: {status['processed_files_count']}")
        print(f"Total chunks: {status['total_chunks']}")
        print(f"FAISS index size: {status['faiss_index_size']}")
        print(f"FAISS dimension: {status['faiss_index_dimension']}")
        print(f"New files: {len(status['new_files'])}")
        print(f"Deleted files: {len(status['deleted_files'])}")
        
        if status['new_files']:
            print(f"\nNew files: {status['new_files']}")
        if status['deleted_files']:
            print(f"\nDeleted files: {status['deleted_files']}")
    
    elif args.validate:
        validation = pipeline.validate_system()
        print("\n=== System Validation ===")
        print(f"Model: {pipeline.model}")
        print(f"Issues: {len(validation['issues'])}")
        print(f"Warnings: {len(validation['warnings'])}")
        
        if validation['issues']:
            print("\nIssues:")
            for issue in validation['issues']:
                print(f"  ❌ {issue}")
        
        if validation['warnings']:
            print("\nWarnings:")
            for warning in validation['warnings']:
                print(f"  ⚠️ {warning}")
        
        if not validation['issues'] and not validation['warnings']:
            print("✅ System is healthy!")
    
    elif args.file:
        result = pipeline.process_single_file(args.file)
        print(f"\n=== Single File Processing ===")
        print(f"File: {result['file']}")
        print(f"Status: {result['status']}")
        print(f"Chunks: {result['chunks_created']}")
        print(f"Embeddings: {result['embeddings_added']}")
        print(f"Cost: ${result['estimated_cost']}")
    
    elif args.cleanup:
        result = pipeline.cleanup_and_process()
        print(f"\n=== Cleanup and Processing ===")
        print(f"Model: {pipeline.model}")
        print(f"Deleted files: {len(result['deleted_files'])}")
        print(f"New files: {len(result['new_files'])}")
        print(f"Processing results: {len(result['processing_results'])}")
        
        if result['processing_results']:
            total_cost = sum(r['estimated_cost'] for r in result['processing_results'])
            total_chunks = sum(r['chunks_created'] for r in result['processing_results'])
            print(f"Total chunks: {total_chunks}")
            print(f"Total cost: ${total_cost:.4f}")
    
    else:
        results = pipeline.process_new_files()
        print(f"\n=== Batch Processing ===")
        print(f"Model: {pipeline.model}")
        print(f"Files processed: {len(results)}")
        
        if results:
            total_cost = sum(r['estimated_cost'] for r in results)
            total_chunks = sum(r['chunks_created'] for r in results)
            print(f"Total chunks: {total_chunks}")
            print(f"Total cost: ${total_cost:.4f}")
        else:
            print("No new files to process") 