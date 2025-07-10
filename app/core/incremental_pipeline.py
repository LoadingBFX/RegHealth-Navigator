"""
incremental_pipeline.py

Orchestrates the complete incremental processing pipeline.
Coordinates chunking and FAISS operations with atomic transactions and proper error handling.
"""
import os
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple

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
    Complete incremental processing pipeline orchestrator.
    
    Provides high-level CRUD operations that coordinate chunking and embedding:
    - Create: Process new XML files (chunks + embeddings)
    - Read: Get system status and validation
    - Update: Re-process modified XML files
    - Delete: Remove files and associated data
    
    All operations are atomic - either they succeed completely or fail completely.
    """
    
    def __init__(self, model: str = None):
        """
        Initialize the incremental pipeline.
        
        Args:
            model: Embedding model to use (from config if None)
        """
        self.model = model if model else config.default_embedding_model
        
        # Initialize components
        self.chunker = IncrementalChunker()
        self.faiss_manager = IncrementalFAISS(model=self.model)
        
        logger.info(f"🚀 Initialized IncrementalPipeline")
        logger.info(f"💰 Model: {self.model}")
        logger.info(f"📁 Data directory: {self.chunker.data_dir}")
        logger.info(f"📁 Output directory: {self.chunker.output_dir}")

    def process_single_file(self, file_path: str) -> Dict:
        """
        Process a single XML file through the complete pipeline.
        This is an atomic operation - either succeeds completely or fails completely.
        
        Args:
            file_path: Path to XML file (relative to data directory)
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"🔄 Processing single file: {file_path}")
        
        try:
            # Step 1: Update chunks for this file
            chunk_result = self.chunker.update_chunks_for_file(file_path)
            if chunk_result['status'] != 'success':
                raise Exception(f"Chunking failed: {chunk_result.get('error', 'Unknown error')}")
            
            chunks = []
            if chunk_result['chunks_added'] > 0:
                # Load the updated chunks for this file
                all_chunks = self.chunker.load_existing_chunks()
                filename = os.path.basename(file_path)
                chunks = [chunk for chunk in all_chunks 
                         if chunk.get('metadata', {}).get('source_file') == filename]
            
            # Step 2: Update embeddings for this file
            embedding_result = self.faiss_manager.update_embeddings_for_file(file_path, chunks)
            if embedding_result['status'] not in ['success', 'no_changes']:
                # Rollback chunks if embedding failed
                logger.error(f"❌ Embedding failed, rolling back chunks for {file_path}")
                try:
                    self.chunker.remove_chunks_for_file(file_path)
                except Exception as rollback_error:
                    logger.error(f"❌ Rollback failed: {rollback_error}")
                
                raise Exception(f"Embedding failed: {embedding_result.get('error', 'Unknown error')}")
            
            logger.info(f"✅ Successfully processed {file_path}")
            logger.info(f"   - Chunks: {chunk_result['chunks_added']}")
            logger.info(f"   - Embeddings: {embedding_result['embeddings_added']}")
            logger.info(f"   - Cost: ${embedding_result['total_cost']:.4f}")
            
            return {
                'file_path': file_path,
                'chunks_added': chunk_result['chunks_added'],
                'chunks_removed': chunk_result['chunks_removed'],
                'embeddings_added': embedding_result['embeddings_added'],
                'embeddings_removed': embedding_result['embeddings_removed'],
                'total_cost': embedding_result['total_cost'],
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing {file_path}: {e}")
            return {
                'file_path': file_path,
                'chunks_added': 0,
                'chunks_removed': 0,
                'embeddings_added': 0,
                'embeddings_removed': 0,
                'total_cost': 0.0,
                'status': 'error',
                'error': str(e)
            }

    def remove_file(self, file_path: str) -> Dict:
        """
        Remove a file and all associated chunks and embeddings.
        This is an atomic operation.
        
        Args:
            file_path: Path to XML file (relative to data directory)
            
        Returns:
            Dictionary with removal results
        """
        logger.info(f"🗑️ Removing file: {file_path}")
        
        try:
            # Step 1: Remove embeddings
            embedding_result = self.faiss_manager.remove_embeddings_for_file(file_path)
            if embedding_result['status'] != 'success':
                raise Exception(f"Failed to remove embeddings: {embedding_result.get('error', 'Unknown')}")
            
            # Step 2: Remove chunks
            chunk_result = self.chunker.remove_chunks_for_file(file_path)
            if chunk_result['status'] != 'success':
                logger.warning(f"⚠️ Chunks removal had issues: {chunk_result.get('error', 'Unknown')}")
            
            logger.info(f"✅ Successfully removed {file_path}")
            logger.info(f"   - Chunks removed: {chunk_result['chunks_removed']}")
            logger.info(f"   - Embeddings removed: {embedding_result['embeddings_removed']}")
            
            return {
                'file_path': file_path,
                'chunks_removed': chunk_result['chunks_removed'],
                'embeddings_removed': embedding_result['embeddings_removed'],
                'rebuild_cost': embedding_result.get('rebuild_cost', 0.0),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"❌ Error removing {file_path}: {e}")
            return {
                'file_path': file_path,
                'chunks_removed': 0,
                'embeddings_removed': 0,
                'rebuild_cost': 0.0,
                'status': 'error',
                'error': str(e)
            }

    def process_new_and_modified_files(self) -> Dict:
        """
        Process all new and modified files through the complete pipeline.
        
        Returns:
            Dictionary with batch processing results
        """
        logger.info("🔄 Processing new and modified files")
        
        # Find new or modified files
        new_files = self.chunker.find_new_or_modified_files()
        
        if not new_files:
            logger.info("✅ No new or modified files found")
            return {
                'processed_files': [],
                'total_chunks_added': 0,
                'total_embeddings_added': 0,
                'total_cost': 0.0,
                'errors': [],
                'status': 'success'
            }
        
        logger.info(f"📁 Found {len(new_files)} new/modified files to process")
        
        # Process each file
        results = []
        total_chunks_added = 0
        total_embeddings_added = 0
        total_cost = 0.0
        errors = []
        
        for file_path in new_files:
            relative_path = self.chunker._get_relative_path(file_path)
            result = self.process_single_file(relative_path)
            results.append(result)
            
            if result['status'] == 'success':
                total_chunks_added += result['chunks_added']
                total_embeddings_added += result['embeddings_added']
                total_cost += result['total_cost']
            else:
                errors.append(f"{relative_path}: {result.get('error', 'Unknown error')}")
        
        processed_files = [r['file_path'] for r in results if r['status'] == 'success']
        
        logger.info(f"✅ Batch processing completed:")
        logger.info(f"   - Files processed: {len(processed_files)}/{len(new_files)}")
        logger.info(f"   - Total chunks added: {total_chunks_added}")
        logger.info(f"   - Total embeddings added: {total_embeddings_added}")
        logger.info(f"   - Total cost: ${total_cost:.4f}")
        
        if errors:
            logger.warning(f"⚠️ {len(errors)} files failed to process")
        
        return {
            'processed_files': processed_files,
            'total_chunks_added': total_chunks_added,
            'total_embeddings_added': total_embeddings_added,
            'total_cost': total_cost,
            'errors': errors,
            'status': 'success' if not errors else 'partial_success'
        }

    def cleanup_deleted_files(self) -> Dict:
        """
        Clean up chunks and embeddings for deleted files.
        
        Returns:
            Dictionary with cleanup results
        """
        logger.info("🧹 Cleaning up deleted files")
        
        # Find deleted files
        deleted_files = self.chunker.find_deleted_files()
        
        if not deleted_files:
            logger.info("✅ No deleted files to clean up")
            return {
                'deleted_files': [],
                'total_chunks_removed': 0,
                'total_embeddings_removed': 0,
                'total_rebuild_cost': 0.0,
                'errors': [],
                'status': 'success'
            }
        
        logger.info(f"🗑️ Found {len(deleted_files)} deleted files to clean up")
        
        # Remove each deleted file
        results = []
        total_chunks_removed = 0
        total_embeddings_removed = 0
        total_rebuild_cost = 0.0
        errors = []
        
        for file_path in deleted_files:
            result = self.remove_file(file_path)
            results.append(result)
            
            if result['status'] == 'success':
                total_chunks_removed += result['chunks_removed']
                total_embeddings_removed += result['embeddings_removed']
                total_rebuild_cost += result['rebuild_cost']
            else:
                errors.append(f"{file_path}: {result.get('error', 'Unknown error')}")
        
        logger.info(f"✅ Cleanup completed:")
        logger.info(f"   - Files cleaned: {len(deleted_files) - len(errors)}/{len(deleted_files)}")
        logger.info(f"   - Total chunks removed: {total_chunks_removed}")
        logger.info(f"   - Total embeddings removed: {total_embeddings_removed}")
        logger.info(f"   - Total rebuild cost: ${total_rebuild_cost:.4f}")
        
        if errors:
            logger.warning(f"⚠️ {len(errors)} files failed to clean up")
        
        return {
            'deleted_files': deleted_files,
            'total_chunks_removed': total_chunks_removed,
            'total_embeddings_removed': total_embeddings_removed,
            'total_rebuild_cost': total_rebuild_cost,
            'errors': errors,
            'status': 'success' if not errors else 'partial_success'
        }

    def full_incremental_update(self) -> Dict:
        """
        Perform a complete incremental update: cleanup deleted files + process new/modified files.
        
        Returns:
            Dictionary with complete update results
        """
        logger.info("🚀 Starting full incremental update")
        
        # Step 1: Cleanup deleted files
        cleanup_result = self.cleanup_deleted_files()
        
        # Step 2: Process new and modified files
        process_result = self.process_new_and_modified_files()
        
        # Combine results
        total_cost = cleanup_result['total_rebuild_cost'] + process_result['total_cost']
        all_errors = cleanup_result['errors'] + process_result['errors']
        
        logger.info("🎉 Full incremental update completed!")
        logger.info(f"   - Files deleted: {len(cleanup_result['deleted_files'])}")
        logger.info(f"   - Files processed: {len(process_result['processed_files'])}")
        logger.info(f"   - Total cost: ${total_cost:.4f}")
        
        if all_errors:
            logger.warning(f"⚠️ {len(all_errors)} operations had errors")
        
        return {
            'cleanup_result': cleanup_result,
            'process_result': process_result,
            'total_cost': total_cost,
            'total_errors': len(all_errors),
            'status': 'success' if not all_errors else 'partial_success'
        }

    def get_system_status(self) -> Dict:
        """Get comprehensive system status."""
        chunker_status = self.chunker.get_status()
        faiss_status = self.faiss_manager.get_status()
        
        return {
            'model': self.model,
            'chunker': chunker_status,
            'faiss': faiss_status,
            'data_consistency': self._check_data_consistency()
        }

    def validate_system(self) -> Dict:
        """Validate system consistency and health."""
        issues = []
        warnings = []
        
        # Check chunker status
        chunker_status = self.chunker.get_status()
        if not chunker_status['chunks_file_exists']:
            issues.append("chunks.json does not exist")
        
        # Check FAISS status
        faiss_status = self.faiss_manager.get_status()
        if not faiss_status['index_exists']:
            issues.append("FAISS index does not exist")
        
        # Check consistency
        faiss_validation = self.faiss_manager.validate_consistency()
        issues.extend(faiss_validation['issues'])
        warnings.extend(faiss_validation['warnings'])
        
        # Check for pending operations
        new_files = self.chunker.find_new_or_modified_files()
        deleted_files = self.chunker.find_deleted_files()
        
        if new_files:
            warnings.append(f"{len(new_files)} files need processing")
        if deleted_files:
            warnings.append(f"{len(deleted_files)} deleted files need cleanup")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'pending_operations': {
                'new_files': len(new_files),
                'deleted_files': len(deleted_files)
            },
            'system_stats': {
                'total_xml_files': chunker_status['total_xml_files'],
                'processed_files': chunker_status['processed_files'],
                'total_chunks': chunker_status['total_chunks'],
                'index_size': faiss_status['index_size'],
                'metadata_entries': faiss_status['metadata_entries']
            }
        }

    def _check_data_consistency(self) -> Dict:
        """Check consistency between chunks and embeddings."""
        try:
            chunks = self.chunker.load_existing_chunks()
            metadata = self.faiss_manager.load_metadata()
            
            chunks_count = len(chunks)
            metadata_count = len(metadata)
            
            return {
                'chunks_count': chunks_count,
                'metadata_count': metadata_count,
                'consistent': chunks_count == metadata_count,
                'difference': abs(chunks_count - metadata_count)
            }
        except Exception as e:
            return {
                'error': str(e),
                'consistent': False
            }

    def estimate_processing_cost(self, file_paths: List[str] = None) -> Dict:
        """
        Estimate the cost of processing specified files or all pending files.
        
        Args:
            file_paths: List of file paths to estimate (estimates all pending if None)
            
        Returns:
            Dictionary with cost estimates
        """
        if file_paths is None:
            # Estimate for all new/modified files
            files_to_estimate = self.chunker.find_new_or_modified_files()
            file_paths = [self.chunker._get_relative_path(f) for f in files_to_estimate]
        
        if not file_paths:
            return {
                'estimated_files': 0,
                'estimated_chunks': 0,
                'estimated_cost': 0.0
            }
        
        total_chunks = 0
        valid_files = 0
        
        for file_path in file_paths:
            try:
                # Do a dry run of chunking to estimate
                absolute_path = self.chunker.data_dir / file_path
                if absolute_path.exists():
                    chunks = self.chunker.chunker.process_file(str(absolute_path))
                    total_chunks += len(chunks)
                    valid_files += 1
            except Exception as e:
                logger.warning(f"⚠️ Could not estimate {file_path}: {e}")
        
        # Estimate cost using FAISS manager
        dummy_chunks = [{'text': 'dummy text'} for _ in range(total_chunks)]
        estimated_cost = self.faiss_manager.estimate_cost(dummy_chunks)
        
        return {
            'estimated_files': valid_files,
            'estimated_chunks': total_chunks,
            'estimated_cost': estimated_cost
        }


# -------- MAIN INCREMENTAL PIPELINE RUNNER --------
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Incremental processing pipeline with CRUD operations")
    parser.add_argument("--file", "-f", type=str, help="Process specific file (relative to data directory)")
    parser.add_argument("--remove", "-r", type=str, help="Remove specific file and its data")
    parser.add_argument("--process-new", "-n", action="store_true", help="Process all new/modified files")
    parser.add_argument("--cleanup", "-c", action="store_true", help="Clean up deleted files")
    parser.add_argument("--full-update", "-u", action="store_true", help="Full incremental update (cleanup + process)")
    parser.add_argument("--status", "-s", action="store_true", help="Show system status")
    parser.add_argument("--validate", "-v", action="store_true", help="Validate system health")
    parser.add_argument("--estimate", "-e", action="store_true", help="Estimate processing cost for pending files")
    parser.add_argument("--model", "-m", type=str, help="Embedding model to use")
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = IncrementalPipeline(model=args.model)
    
    if args.status:
        status = pipeline.get_system_status()
        print("\n=== System Status ===")
        print(f"Model: {status['model']}")
        print(f"\nChunker:")
        for key, value in status['chunker'].items():
            print(f"  {key}: {value}")
        print(f"\nFAISS:")
        for key, value in status['faiss'].items():
            print(f"  {key}: {value}")
        print(f"\nData Consistency:")
        for key, value in status['data_consistency'].items():
            print(f"  {key}: {value}")
    
    elif args.validate:
        validation = pipeline.validate_system()
        print("\n=== System Validation ===")
        print(f"Valid: {validation['valid']}")
        
        if validation['issues']:
            print("\nIssues:")
            for issue in validation['issues']:
                print(f"  ❌ {issue}")
        
        if validation['warnings']:
            print("\nWarnings:")
            for warning in validation['warnings']:
                print(f"  ⚠️ {warning}")
        
        print(f"\nPending Operations:")
        for key, value in validation['pending_operations'].items():
            print(f"  {key}: {value}")
        
        print(f"\nSystem Stats:")
        for key, value in validation['system_stats'].items():
            print(f"  {key}: {value}")
    
    elif args.estimate:
        estimate = pipeline.estimate_processing_cost()
        print("\n=== Cost Estimate ===")
        print(f"Files to process: {estimate['estimated_files']}")
        print(f"Estimated chunks: {estimate['estimated_chunks']}")
        print(f"Estimated cost: ${estimate['estimated_cost']:.4f}")
    
    elif args.file:
        result = pipeline.process_single_file(args.file)
        print(f"\nProcessed {args.file}:")
        print(f"Status: {result['status']}")
        print(f"Chunks added: {result['chunks_added']}")
        print(f"Embeddings added: {result['embeddings_added']}")
        print(f"Cost: ${result['total_cost']:.4f}")
        if result['status'] == 'error':
            print(f"Error: {result['error']}")
    
    elif args.remove:
        result = pipeline.remove_file(args.remove)
        print(f"\nRemoved {args.remove}:")
        print(f"Status: {result['status']}")
        print(f"Chunks removed: {result['chunks_removed']}")
        print(f"Embeddings removed: {result['embeddings_removed']}")
        print(f"Rebuild cost: ${result['rebuild_cost']:.4f}")
        if result['status'] == 'error':
            print(f"Error: {result['error']}")
    
    elif args.process_new:
        result = pipeline.process_new_and_modified_files()
        print(f"\nProcessed new/modified files:")
        print(f"Status: {result['status']}")
        print(f"Files processed: {len(result['processed_files'])}")
        print(f"Total chunks added: {result['total_chunks_added']}")
        print(f"Total embeddings added: {result['total_embeddings_added']}")
        print(f"Total cost: ${result['total_cost']:.4f}")
        if result['errors']:
            print(f"Errors: {len(result['errors'])}")
    
    elif args.cleanup:
        result = pipeline.cleanup_deleted_files()
        print(f"\nCleaned up deleted files:")
        print(f"Status: {result['status']}")
        print(f"Files cleaned: {len(result['deleted_files'])}")
        print(f"Total chunks removed: {result['total_chunks_removed']}")
        print(f"Total embeddings removed: {result['total_embeddings_removed']}")
        print(f"Total rebuild cost: ${result['total_rebuild_cost']:.4f}")
        if result['errors']:
            print(f"Errors: {len(result['errors'])}")
    
    elif args.full_update:
        result = pipeline.full_incremental_update()
        print(f"\nFull incremental update:")
        print(f"Status: {result['status']}")
        print(f"Total cost: ${result['total_cost']:.4f}")
        print(f"Total errors: {result['total_errors']}")
    
    else:
        print("Please specify an operation. Use --help for options.")
        parser.print_help()