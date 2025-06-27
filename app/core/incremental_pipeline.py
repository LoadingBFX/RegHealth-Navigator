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
    
    def __init__(self):
        """Initialize the incremental pipeline."""
        self.chunker = IncrementalChunker()
        self.faiss_updater = IncrementalFAISS()
        logger.info("🚀 Initialized Incremental Pipeline")

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
    parser.add_argument("--file", "-f", help="Process specific file (relative to data directory)")
    parser.add_argument("--all", "-a", action="store_true", help="Process all new/modified files")
    parser.add_argument("--status", "-s", action="store_true", help="Show system status")
    parser.add_argument("--validate", "-v", action="store_true", help="Validate system state")
    parser.add_argument("--list", "-l", action="store_true", help="List new/modified files")
    parser.add_argument("--cleanup", "-c", action="store_true", help="Cleanup deleted files and process new/modified files")
    
    args = parser.parse_args()
    
    pipeline = IncrementalPipeline()
    
    if args.validate:
        validation = pipeline.validate_system()
        print("System Validation:")
        print(f"  Valid: {validation['valid']}")
        if validation['issues']:
            print("  Issues:")
            for issue in validation['issues']:
                print(f"    ❌ {issue}")
        if validation['warnings']:
            print("  Warnings:")
            for warning in validation['warnings']:
                print(f"    ⚠️ {warning}")
    
    elif args.status:
        status = pipeline.get_system_status()
        print("System Status:")
        print(f"  Processed files: {status['processed_files_count']}")
        print(f"  Total chunks: {status['total_chunks']}")
        print(f"  FAISS index size: {status['faiss_index_size']}")
        print(f"  FAISS index dimension: {status['faiss_index_dimension']}")
        print(f"  Metadata entries: {status['metadata_entries']}")
        print(f"  New files: {status['new_files_count']}")
        print(f"  Deleted files: {status['deleted_files_count']}")
        if status['new_files']:
            print("  New files list:")
            for file in status['new_files']:
                print(f"    - {file}")
        if status['deleted_files']:
            print("  Deleted files list:")
            for file in status['deleted_files']:
                print(f"    - {file}")
    
    elif args.list:
        new_files = pipeline.chunker.find_new_files()
        deleted_files = pipeline.chunker.find_deleted_files()
        
        if new_files or deleted_files:
            if new_files:
                print(f"Found {len(new_files)} new/modified files:")
                for file_path in new_files:
                    print(f"  - {file_path.relative_to(pipeline.chunker.input_dir)}")
            if deleted_files:
                print(f"Found {len(deleted_files)} deleted files:")
                for file in deleted_files:
                    print(f"  - {file}")
        else:
            print("No new, modified, or deleted files found")
    
    elif args.file:
        result = pipeline.process_single_file(args.file)
        print(f"Processing result: {result}")
    
    elif args.all:
        results = pipeline.process_new_files()
        print(f"Batch processing completed: {len(results)} files processed")
        for result in results:
            print(f"  {result['file']}: {result['chunks_created']} chunks, ${result['estimated_cost']}")
    
    elif args.cleanup:
        result = pipeline.cleanup_and_process()
        print("Cleanup and Incremental Processing Results:")
        print(f"  Deleted files cleaned: {len(result['deleted_files'])}")
        if result['deleted_files']:
            for file in result['deleted_files']:
                print(f"    - {file}")
        print(f"  New files processed: {len(result['new_files'])}")
        if result['new_files']:
            for file in result['new_files']:
                print(f"    - {file}")
        print(f"  Processing results:")
        for r in result['processing_results']:
            print(f"    {r['file']}: {r['chunks_created']} chunks, {r['embeddings_added']} embeddings, ${r.get('estimated_cost', 0)}")
        print(f"  Rebuild results:")
        rebuild = result['rebuild_result']
        if 'embeddings_kept' in rebuild:
            print(f"    Embeddings kept: {rebuild['embeddings_kept']}")
            print(f"    Embeddings removed: {rebuild['embeddings_removed']}")
            print(f"    Rebuild cost: ${rebuild.get('estimated_cost', 0)}")
        else:
            print(f"    Rebuild status: {rebuild}")
        print(f"  Final system status:")
        for k, v in result['final_status'].items():
            print(f"    {k}: {v}")
    else:
        print("Please specify one of: --file, --all, --status, --validate, --list, or --cleanup")
        parser.print_help() 