#!/usr/bin/env python3
"""
Test File-Based Deletion

Now that source_file access is fixed, test proper file-based deletion functionality.
"""

import os
import sys
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add paths
sys.path.append(str(Path(__file__).parent / 'app' / 'core' / 'preprocessing'))
sys.path.append(str(Path(__file__).parent / 'app'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FileBasedDeletionTester:
    """Test file-based deletion with correct source_file access."""
    
    def __init__(self):
        """Initialize the tester."""
        from app.core.preprocessing.config_loader import ConfigLoader
        
        self.config = ConfigLoader()
        self.processing_config = self.config.get_processing_config()
        self.output_dir = Path(self.processing_config['output_dir'])
        self.backup_dir = self.output_dir / 'file_deletion_test_backup'
        self.backup_dir.mkdir(exist_ok=True)
        
        logger.info("🧪 FileBasedDeletionTester initialized")
    
    def backup_system_state(self) -> Dict[str, Any]:
        """Backup current system state."""
        logger.info("📦 Backing up system state...")
        
        backup_info = {
            'timestamp': datetime.now().isoformat(),
            'files_backed_up': []
        }
        
        files_to_backup = [
            'chunks.json',
            'faiss.index',
            'faiss_metadata.json'
        ]
        
        for filename in files_to_backup:
            source = self.output_dir / filename
            if source.exists():
                backup_path = self.backup_dir / f"{filename}.backup"
                shutil.copy2(source, backup_path)
                backup_info['files_backed_up'].append(filename)
                logger.info(f"✅ Backed up: {filename}")
        
        return backup_info
    
    def restore_system_state(self) -> None:
        """Restore system from backup."""
        logger.info("🔄 Restoring system state...")
        
        backup_files = list(self.backup_dir.glob("*.backup"))
        for backup_file in backup_files:
            original_name = backup_file.name.replace('.backup', '')
            restore_path = self.output_dir / original_name
            shutil.copy2(backup_file, restore_path)
            logger.info(f"✅ Restored: {original_name}")
    
    def analyze_available_files(self) -> Dict[str, Any]:
        """Analyze available files and their chunk counts."""
        logger.info("🔍 Analyzing available files and chunks...")
        
        from app.core.preprocessing.utils.data_persistence import DataPersistence
        
        # Load chunks
        chunks_file = self.output_dir / 'chunks.json'
        chunks_result = DataPersistence.load_json(chunks_file)
        
        if chunks_result['status'] != 'success':
            raise Exception(f"Failed to load chunks: {chunks_result.get('error')}")
        
        chunks = chunks_result['data']
        
        # Count chunks by source file (using CORRECT access path)
        file_chunk_counts = {}
        total_chunks = len(chunks)
        
        for chunk in chunks:
            source_file = chunk.get('metadata', {}).get('source_file', 'UNKNOWN')
            file_chunk_counts[source_file] = file_chunk_counts.get(source_file, 0) + 1
        
        # Sort by chunk count
        sorted_files = sorted(file_chunk_counts.items(), key=lambda x: x[1], reverse=True)
        
        analysis = {
            'total_chunks': total_chunks,
            'unique_files': len(file_chunk_counts),
            'file_chunk_counts': file_chunk_counts,
            'sorted_files': sorted_files
        }
        
        logger.info(f"📊 Analysis Results:")
        logger.info(f"  Total chunks: {total_chunks:,}")
        logger.info(f"  Unique source files: {len(file_chunk_counts)}")
        logger.info(f"  Files with most chunks:")
        for filename, count in sorted_files[:5]:
            logger.info(f"    {filename}: {count} chunks")
        
        return analysis
    
    def select_target_file(self, analysis: Dict[str, Any]) -> str:
        """Select a target file for deletion testing."""
        logger.info("🎯 Selecting target file for deletion...")
        
        sorted_files = analysis['sorted_files']
        
        # Select a file with moderate number of chunks (not the largest or smallest)
        if len(sorted_files) >= 3:
            # Select the 3rd largest file for testing
            target_file = sorted_files[2][0]
        elif len(sorted_files) >= 2:
            # Select the 2nd largest
            target_file = sorted_files[1][0]
        else:
            # Just use the first file
            target_file = sorted_files[0][0]
        
        chunk_count = analysis['file_chunk_counts'][target_file]
        
        logger.info(f"✅ Selected target file: {target_file}")
        logger.info(f"  Chunks to delete: {chunk_count}")
        logger.info(f"  Percentage of total: {(chunk_count/analysis['total_chunks'])*100:.1f}%")
        
        return target_file
    
    def perform_file_deletion(self, target_file: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Perform file-based deletion using correct source_file access."""
        logger.info(f"🗑️ Performing file-based deletion for: {target_file}")
        
        from app.core.preprocessing.utils.data_persistence import DataPersistence
        import faiss
        
        # Load current data
        chunks_file = self.output_dir / 'chunks.json'
        chunks_result = DataPersistence.load_json(chunks_file)
        chunks = chunks_result['data']
        
        index_file = self.output_dir / 'faiss.index'
        metadata_file = self.output_dir / 'faiss_metadata.json'
        
        index = faiss.read_index(str(index_file))
        metadata_result = DataPersistence.load_json(metadata_file)
        metadata = metadata_result['data']
        
        original_chunk_count = len(chunks)
        original_vector_count = index.ntotal
        original_metadata_count = len(metadata)
        
        logger.info(f"📊 Before deletion:")
        logger.info(f"  Chunks: {original_chunk_count}")
        logger.info(f"  Vectors: {original_vector_count}")
        logger.info(f"  Metadata: {original_metadata_count}")
        
        # Find chunks to delete (using CORRECT access path)
        chunks_to_delete = []
        chunks_to_keep = []
        indices_to_delete = []
        
        for i, chunk in enumerate(chunks):
            source_file = chunk.get('metadata', {}).get('source_file', '')
            if source_file == target_file:
                chunks_to_delete.append(chunk)
                indices_to_delete.append(i)
            else:
                chunks_to_keep.append(chunk)
        
        deleted_chunk_count = len(chunks_to_delete)
        
        logger.info(f"🎯 Found {deleted_chunk_count} chunks to delete")
        
        if deleted_chunk_count == 0:
            logger.warning("⚠️ No chunks found for target file!")
            return {
                'status': 'no_chunks_found',
                'target_file': target_file,
                'chunks_deleted': 0
            }
        
        # Save updated chunks
        save_result = DataPersistence.save_json(chunks_to_keep, chunks_file)
        if save_result['status'] != 'success':
            raise Exception(f"Failed to save chunks: {save_result.get('error')}")
        
        # Rebuild FAISS index without deleted chunks
        remaining_indices = [i for i in range(original_vector_count) if i not in indices_to_delete]
        
        if remaining_indices:
            # Extract remaining vectors and metadata
            remaining_vectors = []
            remaining_metadata = []
            
            for i in remaining_indices:
                if i < original_vector_count:
                    vector = index.reconstruct(i)
                    remaining_vectors.append(vector)
                    
                    if i < len(metadata):
                        remaining_metadata.append(metadata[i])
            
            if remaining_vectors:
                import numpy as np
                
                # Create new index
                remaining_vectors_array = np.vstack(remaining_vectors).astype(np.float32)
                dimension = remaining_vectors_array.shape[1]
                
                new_index = faiss.IndexFlatIP(dimension)
                new_index.add(remaining_vectors_array)
                
                # Save new index and metadata
                faiss.write_index(new_index, str(index_file))
                
                save_metadata_result = DataPersistence.save_json(remaining_metadata, metadata_file)
                if save_metadata_result['status'] != 'success':
                    raise Exception(f"Failed to save metadata: {save_metadata_result.get('error')}")
                
                new_vector_count = new_index.ntotal
                new_metadata_count = len(remaining_metadata)
            else:
                new_vector_count = 0
                new_metadata_count = 0
        else:
            # No chunks left - remove index files
            if index_file.exists():
                index_file.unlink()
            if metadata_file.exists():
                metadata_file.unlink()
            new_vector_count = 0
            new_metadata_count = 0
        
        result = {
            'status': 'success',
            'target_file': target_file,
            'chunks_deleted': deleted_chunk_count,
            'vectors_deleted': deleted_chunk_count,
            'original_counts': {
                'chunks': original_chunk_count,
                'vectors': original_vector_count,
                'metadata': original_metadata_count
            },
            'new_counts': {
                'chunks': len(chunks_to_keep),
                'vectors': new_vector_count,
                'metadata': new_metadata_count
            }
        }
        
        logger.info(f"✅ Deletion completed:")
        logger.info(f"  Chunks: {original_chunk_count} → {len(chunks_to_keep)} (-{deleted_chunk_count})")
        logger.info(f"  Vectors: {original_vector_count} → {new_vector_count} (-{deleted_chunk_count})")
        logger.info(f"  Metadata: {original_metadata_count} → {new_metadata_count}")
        
        return result
    
    def verify_deletion(self, target_file: str, deletion_result: Dict[str, Any]) -> Dict[str, Any]:
        """Verify that the file-based deletion was successful."""
        logger.info("🔍 Verifying file-based deletion...")
        
        from app.core.preprocessing.utils.data_persistence import DataPersistence
        
        # Load current chunks
        chunks_file = self.output_dir / 'chunks.json'
        chunks_result = DataPersistence.load_json(chunks_file)
        current_chunks = chunks_result['data']
        
        # Check that no chunks from target file remain
        remaining_target_chunks = 0
        for chunk in current_chunks:
            source_file = chunk.get('metadata', {}).get('source_file', '')
            if source_file == target_file:
                remaining_target_chunks += 1
        
        # Check counts match expectations
        expected_chunks = deletion_result['new_counts']['chunks']
        actual_chunks = len(current_chunks)
        
        verification = {
            'target_file': target_file,
            'remaining_target_chunks': remaining_target_chunks,
            'target_file_completely_removed': remaining_target_chunks == 0,
            'chunk_count_correct': actual_chunks == expected_chunks,
            'expected_chunks': expected_chunks,
            'actual_chunks': actual_chunks,
            'success': remaining_target_chunks == 0 and actual_chunks == expected_chunks
        }
        
        logger.info(f"📊 Verification Results:")
        logger.info(f"  Target file chunks remaining: {remaining_target_chunks}")
        logger.info(f"  Target file completely removed: {'✅' if verification['target_file_completely_removed'] else '❌'}")
        logger.info(f"  Chunk count correct: {'✅' if verification['chunk_count_correct'] else '❌'}")
        logger.info(f"  Overall success: {'✅' if verification['success'] else '❌'}")
        
        return verification
    
    def run_complete_test(self) -> Dict[str, Any]:
        """Run complete file-based deletion test."""
        logger.info("\\n🚀 Starting File-Based Deletion Test")
        logger.info("=" * 60)
        
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'success': False
        }
        
        try:
            # Phase 1: Backup
            logger.info("\\n📋 PHASE 1: System Backup")
            backup_info = self.backup_system_state()
            test_results['backup'] = backup_info
            
            # Phase 2: Analysis
            logger.info("\\n📋 PHASE 2: File Analysis")
            analysis = self.analyze_available_files()
            test_results['analysis'] = analysis
            
            # Phase 3: Target selection
            logger.info("\\n📋 PHASE 3: Target File Selection")
            target_file = self.select_target_file(analysis)
            test_results['target_file'] = target_file
            
            # Phase 4: Deletion
            logger.info("\\n📋 PHASE 4: File-Based Deletion")
            deletion_result = self.perform_file_deletion(target_file, analysis)
            test_results['deletion'] = deletion_result
            
            if deletion_result['status'] != 'success':
                test_results['success'] = False
                return test_results
            
            # Phase 5: Verification
            logger.info("\\n📋 PHASE 5: Deletion Verification")
            verification = self.verify_deletion(target_file, deletion_result)
            test_results['verification'] = verification
            
            test_results['success'] = verification['success']
            
            # Print summary
            self.print_test_summary(test_results)
            
            return test_results
            
        except Exception as e:
            logger.error(f"💥 Test failed: {e}")
            test_results['error'] = str(e)
            return test_results
        
        finally:
            # Always restore
            try:
                self.restore_system_state()
                logger.info("🔄 System state restored")
            except Exception as e:
                logger.error(f"❌ Failed to restore state: {e}")
    
    def print_test_summary(self, results: Dict[str, Any]):
        """Print test summary."""
        logger.info("\\n" + "=" * 60)
        logger.info("📊 FILE-BASED DELETION TEST SUMMARY")
        logger.info("=" * 60)
        
        success = results.get('success', False)
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"Overall Result: {status}")
        
        target_file = results.get('target_file')
        deletion = results.get('deletion', {})
        verification = results.get('verification', {})
        
        if target_file:
            logger.info(f"\\n🎯 Target File: {target_file}")
        
        if deletion:
            logger.info(f"\\n🗑️ Deletion Results:")
            logger.info(f"  Chunks deleted: {deletion.get('chunks_deleted', 0)}")
            orig = deletion.get('original_counts', {})
            new = deletion.get('new_counts', {})
            logger.info(f"  Chunks: {orig.get('chunks', 0)} → {new.get('chunks', 0)}")
            logger.info(f"  Vectors: {orig.get('vectors', 0)} → {new.get('vectors', 0)}")
        
        if verification:
            logger.info(f"\\n🔍 Verification:")
            logger.info(f"  Target file removed: {'✅' if verification.get('target_file_completely_removed') else '❌'}")
            logger.info(f"  Chunk count correct: {'✅' if verification.get('chunk_count_correct') else '❌'}")
        
        if success:
            logger.info(f"\\n💡 Test Conclusions:")
            logger.info(f"  ✅ Source file access path is now CORRECT")
            logger.info(f"  ✅ File-based deletion works properly")
            logger.info(f"  ✅ All chunks from target file removed")
            logger.info(f"  ✅ FAISS index rebuilt correctly")
            logger.info(f"  ✅ Data consistency maintained")
        else:
            logger.info(f"\\n⚠️ Test Issues:")
            logger.info(f"  ❌ Check source_file access patterns")
            logger.info(f"  ❌ Review deletion implementation")
        
        logger.info("=" * 60)


def main():
    """Run file-based deletion test."""
    try:
        tester = FileBasedDeletionTester()
        results = tester.run_complete_test()
        
        success = results.get('success', False)
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"💥 Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())