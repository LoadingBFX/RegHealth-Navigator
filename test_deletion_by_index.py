#!/usr/bin/env python3
"""
Deletion by Index Test

Since chunks don't have source_file information, this test will:
1. Delete chunks by index range (simulating file deletion)
2. Remove corresponding embeddings from FAISS index
3. Verify data consistency after deletion
4. Test the core deletion mechanism

This tests the fundamental deletion capability that would be used
when source file information is properly tracked.
"""

import os
import sys
import json
import random
import shutil
import logging
import hashlib
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add paths
sys.path.append(str(Path(__file__).parent / 'app' / 'core' / 'preprocessing'))
sys.path.append(str(Path(__file__).parent / 'app'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeletionByIndexTester:
    """Test deletion functionality by index range."""
    
    def __init__(self):
        """Initialize the tester."""
        from app.core.preprocessing.config_loader import ConfigLoader
        
        self.config = ConfigLoader()
        self.processing_config = self.config.get_processing_config()
        self.output_dir = Path(self.processing_config['output_dir'])
        self.backup_dir = self.output_dir / 'deletion_index_test_backup'
        self.backup_dir.mkdir(exist_ok=True)
        
        logger.info("🧪 DeletionByIndexTester initialized")
        logger.info(f"📁 Output directory: {self.output_dir}")
    
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
    
    def get_system_baseline(self) -> Dict[str, Any]:
        """Get baseline system state before deletion."""
        logger.info("📊 Getting system baseline...")
        
        from app.core.preprocessing.utils.data_persistence import DataPersistence
        import faiss
        
        baseline = {
            'timestamp': datetime.now().isoformat()
        }
        
        # Load chunks
        chunks_file = self.output_dir / 'chunks.json'
        chunks_result = DataPersistence.load_json(chunks_file)
        
        if chunks_result['status'] != 'success':
            raise Exception(f"Failed to load chunks: {chunks_result.get('error')}")
        
        chunks = chunks_result['data']
        baseline['chunks_count'] = len(chunks)
        baseline['chunks_type'] = 'list' if isinstance(chunks, list) else 'dict'
        
        # Load FAISS index
        index_file = self.output_dir / 'faiss.index'
        if index_file.exists():
            index = faiss.read_index(str(index_file))
            baseline['faiss_vectors'] = index.ntotal
            baseline['faiss_dimension'] = index.d
        
        # Load metadata
        metadata_file = self.output_dir / 'faiss_metadata.json'
        if metadata_file.exists():
            metadata_result = DataPersistence.load_json(metadata_file)
            if metadata_result['status'] == 'success':
                metadata = metadata_result['data']
                baseline['metadata_count'] = len(metadata)
        
        # File sizes
        baseline['file_sizes'] = {}
        for filename in ['chunks.json', 'faiss.index', 'faiss_metadata.json']:
            file_path = self.output_dir / filename
            if file_path.exists():
                baseline['file_sizes'][filename] = file_path.stat().st_size
        
        logger.info(f"📊 Baseline established:")
        logger.info(f"  Chunks: {baseline['chunks_count']:,}")
        logger.info(f"  FAISS vectors: {baseline.get('faiss_vectors', 0):,}")
        logger.info(f"  Metadata entries: {baseline.get('metadata_count', 0):,}")
        
        return baseline
    
    def select_deletion_range(self, baseline: Dict[str, Any]) -> Dict[str, Any]:
        """Select a range of chunks to delete for testing."""
        logger.info("🎯 Selecting deletion range...")
        
        total_chunks = baseline['chunks_count']
        
        # Select a small but meaningful range for testing
        # We'll delete about 1-2% of chunks, minimum 10, maximum 100
        deletion_size = max(10, min(100, total_chunks // 50))
        
        # Select a random starting position, avoiding the very beginning and end
        safe_margin = deletion_size
        start_pos = random.randint(safe_margin, total_chunks - deletion_size - safe_margin)
        end_pos = start_pos + deletion_size - 1
        
        deletion_range = {
            'start_index': start_pos,
            'end_index': end_pos,
            'deletion_size': deletion_size,
            'indices_to_delete': list(range(start_pos, end_pos + 1))
        }
        
        logger.info(f"✅ Selected deletion range:")
        logger.info(f"  Start index: {start_pos}")
        logger.info(f"  End index: {end_pos}")
        logger.info(f"  Chunks to delete: {deletion_size}")
        logger.info(f"  Percentage: {(deletion_size/total_chunks)*100:.2f}%")
        
        return deletion_range
    
    def analyze_chunks_to_delete(self, deletion_range: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the chunks that will be deleted."""
        logger.info("🔍 Analyzing chunks to be deleted...")
        
        from app.core.preprocessing.utils.data_persistence import DataPersistence
        
        # Load chunks
        chunks_file = self.output_dir / 'chunks.json'
        chunks_result = DataPersistence.load_json(chunks_file)
        chunks = chunks_result['data']
        
        indices_to_delete = deletion_range['indices_to_delete']
        
        analysis = {
            'chunk_samples': [],
            'text_lengths': [],
            'total_text_length': 0,
            'section_headers': [],
            'metadata_samples': []
        }
        
        # Analyze the chunks to be deleted
        for i, idx in enumerate(indices_to_delete[:5]):  # Sample first 5
            if idx < len(chunks):
                chunk = chunks[idx]
                text_length = len(chunk.get('text', ''))
                
                analysis['chunk_samples'].append({
                    'index': idx,
                    'text_length': text_length,
                    'section_header': chunk.get('section_header', 'N/A'),
                    'has_metadata': 'metadata' in chunk
                })
                
                analysis['text_lengths'].append(text_length)
        
        # Calculate statistics for all chunks to be deleted
        for idx in indices_to_delete:
            if idx < len(chunks):
                chunk = chunks[idx]
                text_length = len(chunk.get('text', ''))
                analysis['total_text_length'] += text_length
                
                section_header = chunk.get('section_header', '')
                if section_header:
                    analysis['section_headers'].append(section_header)
        
        # Statistics
        if analysis['text_lengths']:
            analysis['text_stats'] = {
                'min_length': min(analysis['text_lengths']),
                'max_length': max(analysis['text_lengths']),
                'avg_length': sum(analysis['text_lengths']) // len(analysis['text_lengths']),
                'total_length': analysis['total_text_length']
            }
        
        logger.info(f"📊 Chunks to delete analysis:")
        logger.info(f"  Sample chunks: {len(analysis['chunk_samples'])}")
        logger.info(f"  Total text: {analysis['total_text_length']:,} characters")
        
        if analysis.get('text_stats'):
            stats = analysis['text_stats']
            logger.info(f"  Text lengths: {stats['min_length']}-{stats['max_length']} chars (avg: {stats['avg_length']})")
        
        logger.info(f"  Sample section headers: {analysis['section_headers'][:3]}")
        
        return analysis
    
    def perform_deletion(self, baseline: Dict[str, Any], 
                        deletion_range: Dict[str, Any],
                        chunk_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Perform the actual deletion."""
        logger.info("🗑️ Performing deletion...")
        
        from app.core.preprocessing.utils.data_persistence import DataPersistence
        import faiss
        
        indices_to_delete = deletion_range['indices_to_delete']
        
        deletion_results = {
            'start_time': datetime.now().isoformat(),
            'chunks_deleted': 0,
            'vectors_deleted': 0,
            'metadata_updated': False,
            'index_rebuilt': False,
            'errors': []
        }
        
        try:
            # Step 1: Load all data
            logger.info("📥 Loading current data...")
            
            chunks_file = self.output_dir / 'chunks.json'
            chunks_result = DataPersistence.load_json(chunks_file)
            chunks = chunks_result['data']
            
            index_file = self.output_dir / 'faiss.index'
            metadata_file = self.output_dir / 'faiss_metadata.json'
            
            index = faiss.read_index(str(index_file))
            metadata_result = DataPersistence.load_json(metadata_file)
            metadata = metadata_result['data']
            
            original_count = len(chunks)
            logger.info(f"  Original chunks: {original_count}")
            logger.info(f"  Original vectors: {index.ntotal}")
            
            # Step 2: Delete chunks (in reverse order to maintain indices)
            logger.info("🗑️ Deleting chunks...")
            
            sorted_indices = sorted(indices_to_delete, reverse=True)
            
            for idx in sorted_indices:
                if 0 <= idx < len(chunks):
                    del chunks[idx]
                    deletion_results['chunks_deleted'] += 1
            
            # Save updated chunks
            save_result = DataPersistence.save_json(chunks, chunks_file)
            if save_result['status'] != 'success':
                raise Exception(f"Failed to save chunks: {save_result.get('error')}")
            
            logger.info(f"✅ Deleted {deletion_results['chunks_deleted']} chunks")
            
            # Step 3: Rebuild FAISS index
            logger.info("🔄 Rebuilding FAISS index...")
            
            remaining_chunk_count = len(chunks)
            
            if remaining_chunk_count > 0:
                # Get vectors for remaining chunks
                remaining_indices = []
                for i in range(original_count):
                    if i not in indices_to_delete:
                        remaining_indices.append(i)
                
                remaining_vectors = []
                remaining_metadata = []
                
                for i in remaining_indices:
                    if i < index.ntotal:
                        vector = index.reconstruct(i)
                        remaining_vectors.append(vector)
                        
                        if isinstance(metadata, list) and i < len(metadata):
                            remaining_metadata.append(metadata[i])
                
                # Create new index
                if remaining_vectors:
                    remaining_vectors_array = np.vstack(remaining_vectors).astype(np.float32)
                    dimension = remaining_vectors_array.shape[1]
                    
                    new_index = faiss.IndexFlatIP(dimension)
                    new_index.add(remaining_vectors_array)
                    
                    # Save new index
                    faiss.write_index(new_index, str(index_file))
                    
                    # Save updated metadata
                    save_metadata_result = DataPersistence.save_json(remaining_metadata, metadata_file)
                    if save_metadata_result['status'] == 'success':
                        deletion_results['metadata_updated'] = True
                    
                    deletion_results['vectors_deleted'] = len(indices_to_delete)
                    deletion_results['index_rebuilt'] = True
                    
                    logger.info(f"✅ Index rebuilt: {index.ntotal} → {new_index.ntotal} vectors")
                else:
                    logger.warning("⚠️ No remaining vectors")
            else:
                logger.warning("⚠️ No remaining chunks")
            
            deletion_results['end_time'] = datetime.now().isoformat()
            deletion_results['success'] = True
            
            logger.info("🎉 Deletion completed successfully!")
            
            return deletion_results
            
        except Exception as e:
            error_msg = f"Deletion failed: {e}"
            logger.error(f"❌ {error_msg}")
            deletion_results['errors'].append(error_msg)
            deletion_results['success'] = False
            return deletion_results
    
    def verify_deletion(self, baseline: Dict[str, Any],
                       deletion_range: Dict[str, Any],
                       deletion_results: Dict[str, Any]) -> Dict[str, Any]:
        """Verify deletion was successful."""
        logger.info("🔍 Verifying deletion...")
        
        from app.core.preprocessing.utils.data_persistence import DataPersistence
        import faiss
        
        verification = {
            'chunks_verification': {},
            'faiss_verification': {},
            'metadata_verification': {},
            'consistency_verification': {},
            'overall_success': False
        }
        
        try:
            # Get current state
            current_baseline = self.get_system_baseline()
            
            # Verify chunk counts
            original_chunks = baseline['chunks_count']
            deleted_chunks = deletion_results['chunks_deleted']
            expected_chunks = original_chunks - deleted_chunks
            actual_chunks = current_baseline['chunks_count']
            
            verification['chunks_verification'] = {
                'original_count': original_chunks,
                'deleted_count': deleted_chunks,
                'expected_remaining': expected_chunks,
                'actual_remaining': actual_chunks,
                'count_correct': actual_chunks == expected_chunks
            }
            
            # Verify FAISS vectors
            original_vectors = baseline.get('faiss_vectors', 0)
            expected_vectors = original_vectors - deleted_chunks
            actual_vectors = current_baseline.get('faiss_vectors', 0)
            
            verification['faiss_verification'] = {
                'original_vectors': original_vectors,
                'expected_vectors': expected_vectors,
                'actual_vectors': actual_vectors,
                'vector_count_correct': actual_vectors == expected_vectors
            }
            
            # Verify metadata
            original_metadata = baseline.get('metadata_count', 0)
            expected_metadata = original_metadata - deleted_chunks
            actual_metadata = current_baseline.get('metadata_count', 0)
            
            verification['metadata_verification'] = {
                'original_metadata': original_metadata,
                'expected_metadata': expected_metadata,
                'actual_metadata': actual_metadata,
                'metadata_count_correct': actual_metadata == expected_metadata
            }
            
            # Overall consistency
            chunks_ok = verification['chunks_verification']['count_correct']
            vectors_ok = verification['faiss_verification']['vector_count_correct']
            metadata_ok = verification['metadata_verification']['metadata_count_correct']
            
            verification['consistency_verification'] = {
                'chunks_consistent': chunks_ok,
                'vectors_consistent': vectors_ok,
                'metadata_consistent': metadata_ok,
                'all_consistent': chunks_ok and vectors_ok and metadata_ok
            }
            
            verification['overall_success'] = verification['consistency_verification']['all_consistent']
            
            # Log results
            logger.info(f"📊 Verification Results:")
            logger.info(f"  Chunks: {original_chunks} → {actual_chunks} (expected: {expected_chunks}) {'✅' if chunks_ok else '❌'}")
            logger.info(f"  Vectors: {original_vectors} → {actual_vectors} (expected: {expected_vectors}) {'✅' if vectors_ok else '❌'}")
            logger.info(f"  Metadata: {original_metadata} → {actual_metadata} (expected: {expected_metadata}) {'✅' if metadata_ok else '❌'}")
            
            if verification['overall_success']:
                logger.info("✅ Deletion verification PASSED")
            else:
                logger.error("❌ Deletion verification FAILED")
            
            return verification
            
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            verification['error'] = str(e)
            return verification
    
    def test_index_functionality(self) -> Dict[str, Any]:
        """Test that the FAISS index still works after deletion."""
        logger.info("🔍 Testing index functionality...")
        
        try:
            import faiss
            
            index_file = self.output_dir / 'faiss.index'
            if not index_file.exists():
                return {'functional': False, 'error': 'Index file not found'}
            
            index = faiss.read_index(str(index_file))
            
            if index.ntotal == 0:
                return {'functional': False, 'error': 'Index is empty'}
            
            # Test search functionality
            # Get a random vector from the index to use as query
            test_vector_idx = random.randint(0, index.ntotal - 1)
            test_vector = index.reconstruct(test_vector_idx)
            test_vector_2d = test_vector.reshape(1, -1)
            
            # Perform search
            k = min(5, index.ntotal)
            similarities, indices = index.search(test_vector_2d, k)
            
            # Verify search worked
            search_successful = (
                len(similarities[0]) == k and
                len(indices[0]) == k and
                indices[0][0] == test_vector_idx  # Should find itself first
            )
            
            functionality_test = {
                'functional': search_successful,
                'index_size': index.ntotal,
                'search_k': k,
                'top_similarity': float(similarities[0][0]) if len(similarities[0]) > 0 else 0,
                'found_self': indices[0][0] == test_vector_idx if len(indices[0]) > 0 else False
            }
            
            logger.info(f"📊 Index functionality test:")
            logger.info(f"  Index size: {index.ntotal}")
            logger.info(f"  Search successful: {'✅' if search_successful else '❌'}")
            logger.info(f"  Top similarity: {functionality_test['top_similarity']:.4f}")
            
            return functionality_test
            
        except Exception as e:
            logger.error(f"❌ Index functionality test failed: {e}")
            return {'functional': False, 'error': str(e)}
    
    def run_complete_deletion_test(self) -> Dict[str, Any]:
        """Run complete deletion test."""
        logger.info("\n🚀 Starting Complete Deletion by Index Test")
        logger.info("=" * 60)
        
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'test_type': 'deletion_by_index',
            'success': False,
            'phases': {}
        }
        
        try:
            # Phase 1: Backup
            logger.info("\n📋 PHASE 1: System Backup")
            backup_info = self.backup_system_state()
            test_results['phases']['backup'] = backup_info
            
            # Phase 2: Baseline
            logger.info("\n📋 PHASE 2: Baseline Analysis")
            baseline = self.get_system_baseline()
            test_results['phases']['baseline'] = baseline
            
            # Phase 3: Select deletion range
            logger.info("\n📋 PHASE 3: Deletion Range Selection")
            deletion_range = self.select_deletion_range(baseline)
            test_results['phases']['deletion_range'] = deletion_range
            
            # Phase 4: Analyze chunks
            logger.info("\n📋 PHASE 4: Chunk Analysis")
            chunk_analysis = self.analyze_chunks_to_delete(deletion_range)
            test_results['phases']['chunk_analysis'] = chunk_analysis
            
            # Phase 5: Perform deletion
            logger.info("\n📋 PHASE 5: Deletion Execution")
            deletion_results = self.perform_deletion(baseline, deletion_range, chunk_analysis)
            test_results['phases']['deletion'] = deletion_results
            
            # Phase 6: Verify deletion
            logger.info("\n📋 PHASE 6: Deletion Verification")
            verification_results = self.verify_deletion(baseline, deletion_range, deletion_results)
            test_results['phases']['verification'] = verification_results
            
            # Phase 7: Test functionality
            logger.info("\n📋 PHASE 7: Index Functionality Test")
            functionality_results = self.test_index_functionality()
            test_results['phases']['functionality'] = functionality_results
            
            # Determine overall success
            deletion_success = deletion_results.get('success', False)
            verification_success = verification_results.get('overall_success', False)
            functionality_success = functionality_results.get('functional', False)
            
            test_results['success'] = deletion_success and verification_success and functionality_success
            
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
        logger.info("\n" + "=" * 60)
        logger.info("📊 DELETION BY INDEX TEST SUMMARY")
        logger.info("=" * 60)
        
        success = results.get('success', False)
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"Overall Result: {status}")
        
        phases = results.get('phases', {})
        
        # Baseline
        baseline = phases.get('baseline', {})
        if baseline:
            logger.info(f"\n📊 Baseline:")
            logger.info(f"  Original chunks: {baseline.get('chunks_count', 0):,}")
            logger.info(f"  Original vectors: {baseline.get('faiss_vectors', 0):,}")
            logger.info(f"  Original metadata: {baseline.get('metadata_count', 0):,}")
        
        # Deletion range
        deletion_range = phases.get('deletion_range', {})
        if deletion_range:
            logger.info(f"\n🎯 Deletion Range:")
            logger.info(f"  Start index: {deletion_range.get('start_index', 0)}")
            logger.info(f"  End index: {deletion_range.get('end_index', 0)}")
            logger.info(f"  Chunks deleted: {deletion_range.get('deletion_size', 0)}")
        
        # Deletion results
        deletion = phases.get('deletion', {})
        if deletion:
            logger.info(f"\n🗑️ Deletion Results:")
            logger.info(f"  Chunks deleted: {deletion.get('chunks_deleted', 0)}")
            logger.info(f"  Vectors deleted: {deletion.get('vectors_deleted', 0)}")
            logger.info(f"  Index rebuilt: {'✅' if deletion.get('index_rebuilt') else '❌'}")
        
        # Verification
        verification = phases.get('verification', {})
        if verification:
            logger.info(f"\n🔍 Verification:")
            consistency = verification.get('consistency_verification', {})
            for check, result in consistency.items():
                if check != 'all_consistent':
                    status = "✅" if result else "❌"
                    logger.info(f"  {status} {check.replace('_', ' ').title()}")
        
        # Functionality
        functionality = phases.get('functionality', {})
        if functionality:
            logger.info(f"\n⚙️ Index Functionality:")
            logger.info(f"  Functional: {'✅' if functionality.get('functional') else '❌'}")
            logger.info(f"  Final index size: {functionality.get('index_size', 0):,}")
        
        if success:
            logger.info(f"\n💡 Deletion Test Conclusions:")
            logger.info(f"  ✅ Core deletion mechanism works correctly")
            logger.info(f"  ✅ FAISS index rebuilding is functional")
            logger.info(f"  ✅ Data consistency maintained across components")
            logger.info(f"  ✅ Index remains searchable after deletion")
            logger.info(f"  ✅ Deletion system is ready for file-based implementation")
        else:
            logger.info(f"\n⚠️ Deletion Test Issues:")
            logger.info(f"  ❌ Review deletion implementation")
            logger.info(f"  ❌ Check data consistency")
        
        logger.info("=" * 60)


def main():
    """Run deletion by index test."""
    try:
        tester = DeletionByIndexTester()
        results = tester.run_complete_deletion_test()
        
        success = results.get('success', False)
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"💥 Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())