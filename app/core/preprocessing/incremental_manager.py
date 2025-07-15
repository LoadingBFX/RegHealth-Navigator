"""
Incremental Processing Manager

Provides comprehensive CRUD operations for managing XML documents, chunks, and FAISS indices
with atomic transactions, change detection, and rollback capabilities.

Example:
    # Initialize manager
    manager = IncrementalManager(
        data_directory="data/xml",
        output_directory="output",
        api_key="your-openai-key"
    )
    
    # Process single file
    result = manager.process_file("MPFS/document.xml")
    if result['status'] == 'success':
        print(f"Processed: {result['chunks_added']} chunks, cost: ${result['cost']:.4f}")
    
    # Update existing file
    update_result = manager.update_file("MPFS/document.xml")
    
    # Remove file and its data
    remove_result = manager.remove_file("MPFS/document.xml")
    
    # Full incremental update
    full_result = manager.full_incremental_update()
"""

import os
from pathlib import Path
<<<<<<< HEAD
from typing import Dict, List, Optional, Union, Any, Set
=======
from typing import Dict, List, Optional, Union, Any, Set, Tuple
>>>>>>> dev
import logging
from datetime import datetime

# Import core components
from .xml_chunker import XMLChunker
from .faiss_builder import FAISSBuilder
from .utils import (
    handle_operation, ProcessingError, DataPersistence, 
    FileTracker, SystemValidator, ensure_success, combine_results
)

logger = logging.getLogger(__name__)


class IncrementalManager:
    """
    Comprehensive incremental processing manager with CRUD operations.
    
    This class orchestrates the complete workflow of XML processing, chunking,
    embedding generation, and FAISS index management with atomic operations
    and proper rollback capabilities.
    """
    
    def __init__(
        self,
        data_directory: Union[str, Path],
        output_directory: Union[str, Path],
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small",
        chunk_words: int = 500,
        overlap_sentences: int = 1
    ):
        """
        Initialize IncrementalManager with configuration.
        
        Args:
            data_directory: Directory containing XML files to process
            output_directory: Directory for output files (chunks, index, metadata)
            api_key: OpenAI API key for embeddings
            model: OpenAI embedding model to use
            chunk_words: Target words per chunk
            overlap_sentences: Sentence overlap between chunks
            
        Example:
            manager = IncrementalManager(
                "data/xml",
                "output",
                model="text-embedding-3-large",
                chunk_words=300
            )
        """
        self.data_dir = Path(data_directory)
        self.output_dir = Path(output_directory)
        self.model = model
        
        # Ensure directories exist
        DataPersistence.ensure_directory(self.output_dir)
        
        # Initialize components
        self.chunker = XMLChunker(
            chunk_words=chunk_words,
            overlap_sentences=overlap_sentences
        )
        
<<<<<<< HEAD
        self.faiss_builder = FAISSBuilder(
            api_key=api_key,
            model=model
=======
        # Create FAISS builder with full configuration
        from .config_loader import ConfigLoader
        config_loader = ConfigLoader()
        embedding_config = config_loader.get_embedding_config()
        
        # Extract model-specific config if available
        model_config = None
        if 'price_per_1k_tokens' in embedding_config:
            model_config = {
                'price_per_1k_tokens': embedding_config.get('price_per_1k_tokens'),
                'encoding': embedding_config.get('encoding', 'cl100k_base'),
                'dimension': embedding_config.get('dimension', 1536),
                'max_tokens': embedding_config.get('max_tokens', 8191)
            }
        
        self.faiss_builder = FAISSBuilder(
            api_key=api_key or embedding_config.get('api_key'),
            model=model,
            batch_size=embedding_config.get('batch_size', 50),
            max_retries=embedding_config.get('max_retries', 5),
            rate_limit_delay=embedding_config.get('rate_limit_delay', 1.0),
            model_config=model_config
>>>>>>> dev
        )
        
        self.file_tracker = FileTracker(
            base_directory=self.data_dir,
            tracking_file=self.output_dir / "file_tracking.json"
        )
        
        # File paths
        self.chunks_path = self.output_dir / "chunks.json"
        self.index_path = self.output_dir / "faiss.index"
        self.metadata_path = self.output_dir / "faiss_metadata.json"
        
        # Load existing data
        self._load_existing_data()
        
        logger.info(f"IncrementalManager initialized")
        logger.info(f"  Data directory: {self.data_dir}")
        logger.info(f"  Output directory: {self.output_dir}")
        logger.info(f"  Model: {self.model}")
    
    def _load_existing_data(self) -> None:
        """Load existing chunks and FAISS index if available."""
        try:
            # Try to load existing FAISS index and metadata
            if self.index_path.exists() and self.metadata_path.exists():
                load_result = self.faiss_builder.load_index(self.index_path, self.metadata_path)
                if load_result['status'] == 'success':
                    logger.info(f"Loaded existing index: {load_result['vectors_loaded']} vectors")
                else:
                    logger.warning(f"Failed to load existing index: {load_result.get('error')}")
        except Exception as e:
            logger.warning(f"Error loading existing data: {e}")
    
    def _load_chunks(self) -> List[Dict[str, Any]]:
        """Load chunks from file."""
        if not self.chunks_path.exists():
            return []
        
        result = DataPersistence.load_chunks(self.chunks_path)
        if result['status'] == 'success':
            return result['data']
        else:
            logger.warning(f"Failed to load chunks: {result.get('error')}")
            return []
    
    def _save_chunks(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Save chunks to file with backup."""
        return DataPersistence.save_chunks(chunks, self.chunks_path, create_backup=True)
    
    def _get_file_chunks(self, chunks: List[Dict[str, Any]], filename: str) -> List[Dict[str, Any]]:
        """Get chunks belonging to a specific file."""
        return [
            chunk for chunk in chunks 
            if chunk.get('metadata', {}).get('source_file') == filename
        ]
    
    def _remove_file_chunks(self, chunks: List[Dict[str, Any]], filename: str) -> Tuple[List[Dict[str, Any]], int]:
        """Remove chunks belonging to a specific file."""
        filtered_chunks = []
        removed_count = 0
        
        for chunk in chunks:
            if chunk.get('metadata', {}).get('source_file') == filename:
                removed_count += 1
            else:
                filtered_chunks.append(chunk)
        
        return filtered_chunks, removed_count
    
<<<<<<< HEAD
=======
    def _rebuild_index_by_reorganization(self, original_chunks: List[Dict[str, Any]], remaining_chunks: List[Dict[str, Any]], chunks_removed: int) -> Dict[str, Any]:
        """
        Efficiently remove vectors from FAISS index using remove_ids (following incremental_faiss.py pattern).
        
        Args:
            original_chunks: Original chunk list before removal
            remaining_chunks: Filtered chunk list after removal  
            chunks_removed: Number of chunks that were removed
            
        Returns:
            Result dictionary with reorganization status
        """
        import numpy as np
        import faiss
        
        logger.info(f"Efficiently removing {chunks_removed} vectors using FAISS remove_ids")
        
        if not self.faiss_builder.index or not self.faiss_builder.metadata:
            raise ProcessingError("No existing index to reorganize")
        
        # Basic consistency check (less strict than before)
        index_size = self.faiss_builder.index.ntotal
        metadata_size = len(self.faiss_builder.metadata)
        
        if index_size != metadata_size:
            logger.warning(f"Index-metadata mismatch: {index_size} vectors vs {metadata_size} metadata entries")
            logger.warning("Falling back to full rebuild due to inconsistency")
            return self._fallback_to_full_rebuild(remaining_chunks)
        
        # Find the filename to remove
        removed_files = set()
        original_files = {chunk.get('metadata', {}).get('source_file') for chunk in original_chunks}
        remaining_files = {chunk.get('metadata', {}).get('source_file') for chunk in remaining_chunks}
        removed_files = original_files - remaining_files
        
        if not removed_files:
            logger.info("No files to remove, keeping index unchanged")
            return {'vectors_reorganized': 0, 'metadata_updated': metadata_size}
        
        filename_to_remove = list(removed_files)[0]
        logger.info(f"Removing vectors for file: {filename_to_remove}")
        
        # Find indices to remove
        indices_to_remove = []
        new_metadata = []
        
        for i, metadata_entry in enumerate(self.faiss_builder.metadata):
            source_file = metadata_entry.get('metadata', {}).get('source_file')
            if source_file == filename_to_remove:
                indices_to_remove.append(i)
            else:
                new_metadata.append(metadata_entry)
        
        if not indices_to_remove:
            logger.info(f"No vectors found for file: {filename_to_remove}")
            return {'vectors_reorganized': 0, 'metadata_updated': metadata_size}
        
        if len(new_metadata) == 0:
            # No vectors left, reset index
            self.faiss_builder.reset()
            return {'vectors_reorganized': len(indices_to_remove), 'metadata_updated': 0}
        
        try:
            # Use FAISS native remove_ids for efficiency (like incremental_faiss.py)
            remove_ids = np.array(indices_to_remove, dtype=np.int64)
            logger.info(f"Removing {len(remove_ids)} vectors from index using remove_ids")
            
            self.faiss_builder.index.remove_ids(remove_ids)
            
            # Verify removal worked correctly
            expected_remaining = metadata_size - len(indices_to_remove)
            actual_remaining = self.faiss_builder.index.ntotal
            
            if actual_remaining != expected_remaining:
                logger.warning(f"remove_ids result mismatch: expected {expected_remaining}, got {actual_remaining}")
                raise RuntimeError(f"remove_ids failed: expected {expected_remaining}, got {actual_remaining}")
            
            # Update metadata
            self.faiss_builder.metadata = new_metadata
            
            vectors_removed = len(indices_to_remove)
            logger.info(f"Successfully removed {vectors_removed} vectors using remove_ids, {actual_remaining} remaining")
            
            return {
                'vectors_reorganized': vectors_removed,
                'metadata_updated': len(new_metadata), 
                'remaining_vectors': actual_remaining,
                'efficient_removal': True,
                'status': 'success'  # 确保状态被正确设置
            }
            
        except Exception as e:
            logger.warning(f"FAISS remove_ids failed: {e}, falling back to rebuild")
            # Fallback: rebuild without regenerating embeddings (still efficient)
            return self._fallback_to_reorganization_rebuild(new_metadata)
    
    def _fallback_to_reorganization_rebuild(self, metadata_to_keep: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fallback rebuild that reuses existing embeddings from metadata (following incremental_faiss.py pattern).
        
        Args:
            metadata_to_keep: Metadata entries to preserve
            
        Returns:
            Result dictionary with rebuild status
        """
        import numpy as np
        import faiss
        
        logger.info("Performing reorganization rebuild (reusing existing embeddings)")
        
        if not metadata_to_keep:
            # Reset everything if no metadata remains
            self.faiss_builder.reset()
            return {
                'vectors_reorganized': 0,
                'metadata_updated': 0,
                'fallback_rebuild': True,
                'rebuild_cost': 0.0
            }
        
        # Extract texts from metadata and regenerate embeddings
        texts = [entry['text'] for entry in metadata_to_keep]
        
        # Generate embeddings (this is the only fallback scenario where we have costs)
        embedding_result = self.faiss_builder.generate_embeddings(texts)
        if embedding_result['status'] != 'success':
            raise ProcessingError(f"Failed to regenerate embeddings: {embedding_result.get('error')}")
        
        embeddings = embedding_result['embeddings']
        rebuild_cost = embedding_result['actual_cost']
        
        if embeddings:
            # Create new index
            dimension = len(embeddings[0])
            self.faiss_builder.index = faiss.IndexFlatL2(dimension)
            embedding_matrix = np.array(embeddings).astype('float32')
            self.faiss_builder.index.add(embedding_matrix)
            
            # Update metadata
            self.faiss_builder.metadata = metadata_to_keep
            
            logger.info(f"Reorganization rebuild completed: {len(embeddings)} vectors, cost: ${rebuild_cost:.4f}")
            
            return {
                'vectors_reorganized': len(embeddings),
                'metadata_updated': len(metadata_to_keep),
                'fallback_rebuild': True,
                'rebuild_cost': rebuild_cost
            }
        else:
            raise ProcessingError("Failed to generate embeddings for reorganization rebuild")
    
    def _fallback_to_full_rebuild(self, remaining_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fallback to full rebuild when efficient reorganization is not possible.
        
        Args:
            remaining_chunks: Chunks to rebuild index from
            
        Returns:
            Result dictionary with rebuild status
        """
        logger.info("Performing full rebuild due to data inconsistency")
        
        if not remaining_chunks:
            # Reset everything if no chunks remain
            self.faiss_builder.reset()
            return {
                'vectors_reorganized': 0,
                'metadata_updated': 0,
                'fallback_rebuild': True,
                'rebuild_cost': 0.0
            }
        
        # Build new index from remaining chunks
        build_result = self.faiss_builder.build_index_from_chunks(remaining_chunks, "flat")
        
        if build_result['status'] == 'success':
            rebuild_cost = build_result['total_cost']
            logger.warning(f"Fallback rebuild completed at cost ${rebuild_cost:.4f}")
            
            return {
                'vectors_reorganized': build_result['vectors_created'],
                'metadata_updated': build_result['metadata_entries'],
                'fallback_rebuild': True,
                'rebuild_cost': rebuild_cost
            }
        else:
            raise ProcessingError(f"Fallback rebuild failed: {build_result.get('error')}")
    
>>>>>>> dev
    @handle_operation("file processing", success_fields={'chunks_added': 0, 'cost': 0.0})
    def process_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Process a single XML file through the complete pipeline.
        
        This is an atomic operation that either succeeds completely or fails completely.
        If embedding fails, chunk data is rolled back.
        
        Args:
            file_path: Path to XML file (relative to data directory)
            
        Returns:
            Result dictionary with processing status and statistics
            
        Example:
            result = manager.process_file("MPFS/2024_final.xml")
            if result['status'] == 'success':
                print(f"Added {result['chunks_added']} chunks, cost: ${result['cost']:.4f}")
        """
        file_path = Path(file_path)
        
        # Resolve absolute path
        if not file_path.is_absolute():
            absolute_path = self.data_dir / file_path
        else:
            absolute_path = file_path
            file_path = self.file_tracker.get_relative_path(absolute_path)
        
        if not absolute_path.exists():
            raise ProcessingError(f"File not found: {absolute_path}")
        
        logger.info(f"Processing file: {file_path}")
        
        # Load existing chunks for rollback capability
        existing_chunks = self._load_chunks()
        original_index_state = None
        
        try:
            # Step 1: Process XML file to create chunks
            chunk_result = self.chunker.process_file(absolute_path)
            ensure_success(chunk_result, "XML chunking")
            
            new_chunks = chunk_result['chunks']
            if not new_chunks:
                logger.info(f"No chunks created for {file_path}")
                return {
                    'file_path': str(file_path),
                    'chunks_added': 0,
                    'embeddings_added': 0,
                    'cost': 0.0
                }
            
            # Step 2: Add new chunks to existing collection
            updated_chunks = existing_chunks + new_chunks
            
            # Step 3: Save updated chunks
            save_result = self._save_chunks(updated_chunks)
            ensure_success(save_result, "chunk saving")
            
            # Step 4: Generate embeddings and update index
            if self.faiss_builder.index is not None:
                # Store current index state for rollback
                original_index_state = {
                    'vectors': self.faiss_builder.index.ntotal,
                    'metadata_count': len(self.faiss_builder.metadata)
                }
            
            # Extract texts for embedding
            texts = [chunk['text'] for chunk in new_chunks]
            
            # Generate embeddings
            embedding_result = self.faiss_builder.generate_embeddings(texts)
            ensure_success(embedding_result, "embedding generation")
            
            embeddings = embedding_result['embeddings']
            cost = embedding_result['actual_cost']
            
            # Create/update FAISS index
            if self.faiss_builder.index is None:
                # Create new index
                index_result = self.faiss_builder.create_index(embeddings, "flat")
                ensure_success(index_result, "index creation")
                
                # Create metadata for new chunks
                processed_texts = embedding_result.get('processed_texts', texts)
                new_metadata = self.faiss_builder.create_metadata(new_chunks, processed_texts)
                self.faiss_builder.metadata = new_metadata
            else:
                # Add to existing index
                import numpy as np
                embedding_matrix = np.array(embeddings).astype('float32')
                self.faiss_builder.index.add(embedding_matrix)
                
                # Add to existing metadata
                processed_texts = embedding_result.get('processed_texts', texts)
                new_metadata = self.faiss_builder.create_metadata(new_chunks, processed_texts)
                self.faiss_builder.metadata.extend(new_metadata)
            
            # Step 5: Save updated index and metadata
            save_index_result = self.faiss_builder.save_index(self.index_path, self.metadata_path)
            ensure_success(save_index_result, "index saving")
            
            # Step 6: Update file tracking
            tracking_result = self.file_tracker.update_tracking(
                absolute_path,
                {
                    'chunks_count': len(new_chunks),
                    'embeddings_count': len(embeddings),
                    'processing_cost': cost
                }
            )
            ensure_success(tracking_result, "tracking update")
            
            logger.info(f"Successfully processed {file_path}: {len(new_chunks)} chunks, ${cost:.4f}")
            
            return {
                'file_path': str(file_path),
                'chunks_added': len(new_chunks),
                'embeddings_added': len(embeddings),
                'cost': cost,
                'processing_stats': chunk_result.get('processing_stats', {})
            }
            
        except Exception as e:
            # Rollback on any failure
            logger.error(f"Processing failed for {file_path}, rolling back: {e}")
            
            try:
                # Restore original chunks
                if existing_chunks != self._load_chunks():
                    self._save_chunks(existing_chunks)
                    logger.info("Rolled back chunks file")
                
                # Restore index state if it was modified
                if original_index_state and self.faiss_builder.index is not None:
                    current_vectors = self.faiss_builder.index.ntotal
                    if current_vectors != original_index_state['vectors']:
                        # Reload original index
                        if self.index_path.exists() and self.metadata_path.exists():
                            self.faiss_builder.load_index(self.index_path, self.metadata_path)
                        logger.info("Rolled back FAISS index")
                
            except Exception as rollback_error:
                logger.error(f"Rollback failed: {rollback_error}")
            
            raise ProcessingError(f"File processing failed: {e}")
    
    @handle_operation("file update", success_fields={'chunks_added': 0, 'chunks_removed': 0, 'cost': 0.0})
    def update_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Update processing for a modified file (remove old data + add new).
        
        Args:
            file_path: Path to XML file to update
            
        Returns:
            Result dictionary with update statistics
            
        Example:
            result = manager.update_file("MPFS/2024_final.xml")
            print(f"Updated: -{result['chunks_removed']} +{result['chunks_added']} chunks")
        """
        file_path = Path(file_path)
        filename = file_path.name
        
        logger.info(f"Updating file: {file_path}")
        
        # Step 1: Remove existing data for this file
        remove_result = self.remove_file(file_path)
        if remove_result['status'] != 'success':
            raise ProcessingError(f"Failed to remove old data: {remove_result.get('error')}")
        
        chunks_removed = remove_result['chunks_removed']
        
        # Step 2: Process file with new data
        process_result = self.process_file(file_path)
        if process_result['status'] != 'success':
            raise ProcessingError(f"Failed to process updated file: {process_result.get('error')}")
        
        chunks_added = process_result['chunks_added']
        cost = process_result['cost']
        
        logger.info(f"Updated {file_path}: -{chunks_removed} +{chunks_added} chunks, ${cost:.4f}")
        
        return {
            'file_path': str(file_path),
            'chunks_removed': chunks_removed,
            'chunks_added': chunks_added,
            'embeddings_added': process_result['embeddings_added'],
            'cost': cost,
            'net_change': chunks_added - chunks_removed
        }
    
    @handle_operation("file removal", success_fields={'chunks_removed': 0, 'embeddings_removed': 0})
    def remove_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Remove a file and all its associated data (chunks, embeddings, tracking).
        
        Args:
            file_path: Path to XML file to remove
            
        Returns:
            Result dictionary with removal statistics
            
        Example:
            result = manager.remove_file("MPFS/old_document.xml")
            print(f"Removed {result['chunks_removed']} chunks")
        """
        file_path = Path(file_path)
        filename = file_path.name
        
        logger.info(f"Removing file data: {file_path}")
        
        # Step 1: Load current chunks
        chunks = self._load_chunks()
        original_count = len(chunks)
        
        # Step 2: Remove chunks for this file
        filtered_chunks, chunks_removed = self._remove_file_chunks(chunks, filename)
        
        if chunks_removed == 0:
            logger.info(f"No chunks found for {file_path}")
            return {
                'file_path': str(file_path),
                'chunks_removed': 0,
                'embeddings_removed': 0,
                'rebuild_cost': 0.0
            }
        
        # Step 3: Save updated chunks
        save_result = self._save_chunks(filtered_chunks)
        ensure_success(save_result, "chunk file update")
        
<<<<<<< HEAD
        # Step 4: Rebuild FAISS index without this file's data
=======
        # Step 4: Rebuild FAISS index efficiently without regenerating embeddings
>>>>>>> dev
        embeddings_removed = 0
        rebuild_cost = 0.0
        
        if filtered_chunks:
<<<<<<< HEAD
            # Rebuild index from remaining chunks
            logger.info(f"Rebuilding FAISS index without {filename}")
            
            build_result = self.faiss_builder.build_index_from_chunks(filtered_chunks, "flat")
            ensure_success(build_result, "index rebuild")
            
            embeddings_removed = chunks_removed  # Approximate
            rebuild_cost = build_result['total_cost']
            
            # Save rebuilt index
            save_index_result = self.faiss_builder.save_index(self.index_path, self.metadata_path)
            ensure_success(save_index_result, "rebuilt index save")
=======
            # Use efficient index reorganization instead of full rebuild
            logger.info(f"Reorganizing FAISS index without {filename} (no embedding regeneration)")
            
            rebuild_result = self._rebuild_index_by_reorganization(chunks, filtered_chunks, chunks_removed)
            ensure_success(rebuild_result, "index reorganization")
            
            embeddings_removed = chunks_removed
            rebuild_cost = 0.0  # No API costs for reorganization
            
            # Save reorganized index
            save_index_result = self.faiss_builder.save_index(self.index_path, self.metadata_path)
            ensure_success(save_index_result, "reorganized index save")
>>>>>>> dev
        else:
            # No chunks left, remove index files
            if self.index_path.exists():
                self.index_path.unlink()
            if self.metadata_path.exists():
                self.metadata_path.unlink()
            
            # Reset FAISS builder
            self.faiss_builder.reset()
            
            embeddings_removed = chunks_removed
        
        # Step 5: Remove file tracking
        self.file_tracker.remove_tracking(file_path)
        
        logger.info(f"Removed {file_path}: {chunks_removed} chunks, rebuild cost: ${rebuild_cost:.4f}")
        
        return {
            'file_path': str(file_path),
            'chunks_removed': chunks_removed,
            'embeddings_removed': embeddings_removed,
            'rebuild_cost': rebuild_cost,
            'remaining_chunks': len(filtered_chunks)
        }
    
    @handle_operation("batch processing", success_fields={'files_processed': 0, 'total_cost': 0.0})
    def process_multiple_files(self, file_paths: List[Union[str, Path]]) -> Dict[str, Any]:
        """
        Process multiple files in batch with error handling.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            Result dictionary with batch processing statistics
            
        Example:
            result = manager.process_multiple_files(["doc1.xml", "doc2.xml"])
            print(f"Processed {result['files_processed']}/{len(file_paths)} files")
        """
        if not file_paths:
            return {
                'files_processed': 0,
                'total_files': 0,
                'total_cost': 0.0,
                'file_results': [],
                'errors': []
            }
        
        results = []
        total_cost = 0.0
        successful_files = 0
        errors = []
        
        for file_path in file_paths:
            try:
                result = self.process_file(file_path)
                results.append(result)
                
                if result['status'] == 'success':
                    successful_files += 1
                    total_cost += result.get('cost', 0.0)
                else:
                    errors.append(f"{file_path}: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                error_msg = f"{file_path}: {str(e)}"
                errors.append(error_msg)
                results.append({
                    'file_path': str(file_path),
                    'status': 'error',
                    'error': str(e)
                })
                logger.error(f"Error processing {file_path}: {e}")
        
        logger.info(f"Batch processing completed: {successful_files}/{len(file_paths)} files successful")
        
        return {
            'files_processed': successful_files,
            'total_files': len(file_paths),
            'total_cost': total_cost,
            'file_results': results,
            'errors': errors,
            'success_rate': successful_files / len(file_paths) if file_paths else 0
        }
    
    @handle_operation("incremental update", success_fields={'files_processed': 0, 'files_removed': 0})
    def full_incremental_update(self) -> Dict[str, Any]:
        """
        Perform complete incremental update: process new/modified files and clean up deleted files.
        
        Returns:
            Result dictionary with comprehensive update statistics
            
        Example:
            result = manager.full_incremental_update()
            print(f"Updated {result['files_processed']} files, removed {result['files_removed']}")
        """
        logger.info("Starting full incremental update")
        
        # Step 1: Find files that need processing
        changed_result = self.file_tracker.find_changed_files()
        ensure_success(changed_result, "change detection")
        changed_files = changed_result['files']
        
        # Step 2: Find deleted files
        deleted_result = self.file_tracker.find_deleted_files()
        ensure_success(deleted_result, "deletion detection")
        deleted_files = deleted_result['file_paths']
        
        # Step 3: Clean up deleted files
        cleanup_results = []
        total_cleanup_cost = 0.0
        
        for deleted_file in deleted_files:
            try:
                remove_result = self.remove_file(deleted_file)
                cleanup_results.append(remove_result)
                if remove_result['status'] == 'success':
                    total_cleanup_cost += remove_result.get('rebuild_cost', 0.0)
            except Exception as e:
                logger.error(f"Error removing {deleted_file}: {e}")
                cleanup_results.append({
                    'file_path': deleted_file,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Step 4: Process changed/new files
        if changed_files:
            # Convert to relative paths
            relative_paths = [self.file_tracker.get_relative_path(f) for f in changed_files]
            process_result = self.process_multiple_files(relative_paths)
        else:
            process_result = {
                'files_processed': 0,
                'total_cost': 0.0,
                'file_results': [],
                'errors': []
            }
        
        # Step 5: Combine results
        total_cost = total_cleanup_cost + process_result.get('total_cost', 0.0)
        all_errors = []
        
        # Add cleanup errors
        for result in cleanup_results:
            if result.get('status') == 'error':
                all_errors.append(f"Cleanup - {result.get('error', 'Unknown error')}")
        
        # Add processing errors
        all_errors.extend(process_result.get('errors', []))
        
        logger.info(f"Incremental update completed:")
        logger.info(f"  Files processed: {process_result['files_processed']}")
        logger.info(f"  Files removed: {len(deleted_files)}")
        logger.info(f"  Total cost: ${total_cost:.4f}")
        
        return {
            'files_processed': process_result['files_processed'],
            'files_removed': len(deleted_files),
            'total_cost': total_cost,
            'cleanup_cost': total_cleanup_cost,
            'processing_cost': process_result.get('total_cost', 0.0),
            'cleanup_results': cleanup_results,
            'processing_results': process_result['file_results'],
            'errors': all_errors,
            'summary': {
                'changed_files_found': len(changed_files),
                'deleted_files_found': len(deleted_files),
                'successful_operations': process_result['files_processed'] + len([r for r in cleanup_results if r.get('status') == 'success']),
                'failed_operations': len(all_errors)
            }
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status.
        
        Returns:
            Dictionary with current system status and statistics
            
        Example:
            status = manager.get_status()
            print(f"System has {status['total_chunks']} chunks in index")
        """
        # Get file tracking status
        tracking_status = self.file_tracker.get_status()
        
        # Get FAISS builder statistics
        faiss_stats = self.faiss_builder.get_statistics()
        
        # Get chunks information
        chunks = self._load_chunks()
        
        # Check for pending operations
        changed_result = self.file_tracker.find_changed_files()
        deleted_result = self.file_tracker.find_deleted_files()
        
        pending_changes = changed_result.get('changed_files', 0) if changed_result['status'] == 'success' else 0
        pending_deletions = deleted_result.get('deleted_files', 0) if deleted_result['status'] == 'success' else 0
        
        return {
            'data_directory': str(self.data_dir),
            'output_directory': str(self.output_dir),
            'model': self.model,
            'total_chunks': len(chunks),
            'index_size': faiss_stats['index_size'],
            'metadata_entries': faiss_stats['metadata_entries'],
            'total_cost': faiss_stats['total_cost'],
            'files_tracked': tracking_status['total_tracked'],
            'current_files': tracking_status['current_files'],
            'pending_changes': pending_changes,
            'pending_deletions': pending_deletions,
            'files_exist': {
                'chunks': self.chunks_path.exists(),
                'index': self.index_path.exists(),
                'metadata': self.metadata_path.exists(),
                'tracking': tracking_status['tracking_file_exists']
            },
            'data_consistency': {
                'chunks_vs_metadata': len(chunks) == faiss_stats['metadata_entries'],
                'metadata_vs_index': faiss_stats['metadata_entries'] == faiss_stats['index_size']
            }
        }
    
    def validate_system(self) -> Dict[str, Any]:
        """
        Validate system health and data consistency.
        
        Returns:
            Validation report with issues and warnings
            
        Example:
            validation = manager.validate_system()
            if not validation['valid']:
                for issue in validation['issues']:
                    print(f"Issue: {issue}")
        """
        validator = SystemValidator()
        
        # Create standard validators
        validator.create_standard_validators(
            chunks_file=str(self.chunks_path),
            faiss_index=str(self.index_path),
            faiss_metadata=str(self.metadata_path),
            tracking_file=str(self.file_tracker.tracking_file),
            data_directory=str(self.data_dir)
        )
        
        # Add custom consistency validators
        def validate_data_consistency():
            chunks = self._load_chunks()
            faiss_stats = self.faiss_builder.get_statistics()
            
            issues = []
            warnings = []
            
            # Check chunks vs metadata count
            if len(chunks) != faiss_stats['metadata_entries']:
                issues.append(f"Chunks count mismatch: {len(chunks)} chunks vs {faiss_stats['metadata_entries']} metadata entries")
            
            # Check metadata vs index count
            if faiss_stats['metadata_entries'] != faiss_stats['index_size']:
                issues.append(f"Index size mismatch: {faiss_stats['index_size']} vectors vs {faiss_stats['metadata_entries']} metadata entries")
            
            # Check for pending operations
            status = self.get_status()
            if status['pending_changes'] > 0:
                warnings.append(f"{status['pending_changes']} files have pending changes")
            if status['pending_deletions'] > 0:
                warnings.append(f"{status['pending_deletions']} deleted files need cleanup")
            
            from .utils.system_validator import ValidationResult
            return ValidationResult(
                'data_consistency',
                len(issues) == 0,
                "Data consistency check",
                issues,
                warnings,
                {
                    'chunks_count': len(chunks),
                    'metadata_count': faiss_stats['metadata_entries'],
                    'index_size': faiss_stats['index_size']
                }
            )
        
        validator.add_validator('data_consistency', validate_data_consistency, required=True)
        
        # Run full validation
        return validator.validate_all()
    
    def estimate_cost(self, file_paths: Optional[List[Union[str, Path]]] = None) -> Dict[str, Any]:
        """
        Estimate processing cost for files.
        
        Args:
            file_paths: Specific files to estimate (all pending files if None)
            
        Returns:
            Cost estimation results
            
        Example:
            estimate = manager.estimate_cost()
            print(f"Estimated cost for pending files: ${estimate['total_estimated_cost']:.4f}")
        """
        if file_paths is None:
            # Estimate for pending files
            changed_result = self.file_tracker.find_changed_files()
            if changed_result['status'] == 'success':
                file_paths = [self.file_tracker.get_relative_path(f) for f in changed_result['files']]
            else:
                file_paths = []
        
        if not file_paths:
            return {
                'estimated_files': 0,
                'estimated_chunks': 0,
                'total_estimated_cost': 0.0
            }
        
        total_chunks = 0
        valid_files = 0
        
        for file_path in file_paths:
            try:
                # Resolve absolute path
                if not Path(file_path).is_absolute():
                    absolute_path = self.data_dir / file_path
                else:
                    absolute_path = Path(file_path)
                
                if absolute_path.exists():
                    # Do dry run of chunking
                    chunk_result = self.chunker.process_file(absolute_path)
                    if chunk_result['status'] == 'success':
                        total_chunks += chunk_result['chunks_created']
                        valid_files += 1
            except Exception as e:
                logger.warning(f"Could not estimate {file_path}: {e}")
        
        # Estimate embedding cost
        if total_chunks > 0:
            # Create dummy chunks for cost estimation
            dummy_texts = ['dummy text for cost estimation'] * total_chunks
            estimated_cost = self.faiss_builder.estimate_cost(dummy_texts)
        else:
            estimated_cost = 0.0
        
        return {
            'estimated_files': valid_files,
            'estimated_chunks': total_chunks,
            'total_estimated_cost': estimated_cost,
            'cost_per_chunk': estimated_cost / total_chunks if total_chunks > 0 else 0.0
        }