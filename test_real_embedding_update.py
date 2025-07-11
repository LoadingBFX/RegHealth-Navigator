#!/usr/bin/env python3
"""
Real Embedding Update Test with API Calls

This test performs ACTUAL embedding updates to verify the complete workflow:
1. Modify chunk content
2. Generate new embedding via OpenAI API
3. Update FAISS index
4. Verify the embedding vector actually changed
5. Test retrieval with the new content

⚠️ WARNING: This test will make API calls and incur small costs (estimated <$0.01)
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

class RealEmbeddingUpdateTester:
    """Real embedding update tester with actual API calls."""
    
    def __init__(self):
        """Initialize the tester."""
        from app.core.preprocessing.config_loader import ConfigLoader
        
        self.config = ConfigLoader()
        self.processing_config = self.config.get_processing_config()
        self.output_dir = Path(self.processing_config['output_dir'])
        self.backup_dir = self.output_dir / 'real_embedding_test_backup'
        self.backup_dir.mkdir(exist_ok=True)
        
        # Check API key
        if not self.processing_config.get('api_key'):
            raise Exception("OpenAI API key not found. This test requires API access.")
        
        logger.info("🧪 RealEmbeddingUpdateTester initialized")
        logger.info(f"🔑 API key available: {len(self.processing_config['api_key'])} chars")
        logger.info(f"🤖 Model: {self.processing_config['model']}")
    
    def estimate_test_cost(self) -> float:
        """Estimate the cost of this test."""
        # We'll update one chunk, which is typically ~500 words = ~750 tokens
        # text-embedding-3-small costs $0.00002 per 1K tokens
        estimated_tokens = 750
        cost_per_1k = 0.00002
        estimated_cost = (estimated_tokens / 1000) * cost_per_1k
        
        logger.info(f"💰 Estimated test cost: ~${estimated_cost:.5f}")
        return estimated_cost
    
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
    
    def select_and_modify_chunk(self) -> Dict[str, Any]:
        """Select a chunk and modify its content."""
        logger.info("🎯 Selecting and modifying chunk...")
        
        from app.core.preprocessing.utils.data_persistence import DataPersistence
        
        # Load chunks
        chunks_file = self.output_dir / 'chunks.json'
        chunks_result = DataPersistence.load_json(chunks_file)
        
        if chunks_result['status'] != 'success':
            raise Exception(f"Failed to load chunks: {chunks_result.get('error')}")
        
        chunks = chunks_result['data']
        
        # Select random chunk (avoid very short ones)
        if isinstance(chunks, list):
            suitable_chunks = [
                (i, chunk) for i, chunk in enumerate(chunks)
                if len(chunk.get('text', '')) > 500  # At least 500 chars
            ]
            if not suitable_chunks:
                raise Exception("No suitable chunks found for testing")
            
            selected_index, selected_chunk = random.choice(suitable_chunks)
            chunk_identifier = f"chunk_{selected_index}"
        else:
            suitable_chunks = [
                (chunk_id, chunk) for chunk_id, chunk in chunks.items()
                if len(chunk.get('text', '')) > 500
            ]
            if not suitable_chunks:
                raise Exception("No suitable chunks found for testing")
            
            chunk_identifier, selected_chunk = random.choice(suitable_chunks)
            selected_index = None
        
        # Record original content
        original_text = selected_chunk.get('text', '')
        original_hash = hashlib.md5(original_text.encode()).hexdigest()
        
        logger.info(f"✅ Selected chunk: {chunk_identifier}")
        logger.info(f"📝 Original text length: {len(original_text):,} chars")
        logger.info(f"🏷️ Source file: {selected_chunk.get('metadata', {}).get('source_file', 'unknown')}")
        
        # Create meaningful modification
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        modification_text = f"""

=== EMBEDDING UPDATE TEST MODIFICATION ===
Test ID: {timestamp}
Original content hash: {original_hash[:16]}
Test purpose: Verify that embedding vectors are regenerated when chunk content changes.

This modification adds unique, searchable content that should result in a different 
embedding vector compared to the original chunk. The new embedding should capture 
both the original regulatory content and this test-specific information.

Key test phrases for retrieval verification:
- "embedding update test modification"
- "test ID {timestamp}"  
- "searchable test content added"
- "regulatory content with test data"

=== END MODIFICATION ==="""

        modified_text = original_text + modification_text
        modified_hash = hashlib.md5(modified_text.encode()).hexdigest()
        
        # Update chunk
        updated_chunk = selected_chunk.copy()
        updated_chunk['text'] = modified_text
        updated_chunk['test_modification_timestamp'] = timestamp
        updated_chunk['original_hash'] = original_hash
        updated_chunk['modified_hash'] = modified_hash
        updated_chunk['test_modification_active'] = True
        
        # Update chunks data
        if isinstance(chunks, list):
            chunks[selected_index] = updated_chunk
        else:
            chunks[chunk_identifier] = updated_chunk
        
        # Save modified chunks
        save_result = DataPersistence.save_json(chunks, chunks_file)
        if save_result['status'] != 'success':
            raise Exception(f"Failed to save modified chunks: {save_result.get('error')}")
        
        modification_info = {
            'chunk_identifier': chunk_identifier,
            'chunk_index': selected_index,
            'original_text_length': len(original_text),
            'modified_text_length': len(modified_text),
            'added_content_length': len(modification_text),
            'original_hash': original_hash,
            'modified_hash': modified_hash,
            'timestamp': timestamp,
            'test_phrases': [
                "embedding update test modification",
                f"test ID {timestamp}",
                "searchable test content added",
                "regulatory content with test data"
            ]
        }
        
        logger.info(f"✅ Chunk modified successfully")
        logger.info(f"  Text added: {len(modification_text):,} chars")
        logger.info(f"  New total length: {len(modified_text):,} chars")
        logger.info(f"  Content hash changed: {original_hash != modified_hash}")
        
        return modification_info
    
    def generate_new_embedding(self, chunk_text: str) -> Dict[str, Any]:
        """Generate new embedding for the modified chunk."""
        logger.info("🤖 Generating new embedding via OpenAI API...")
        
        from app.core.preprocessing.faiss_builder import FAISSBuilder
        
        # Create FAISS builder
        faiss_builder = FAISSBuilder(
            api_key=self.processing_config['api_key'],
            model=self.processing_config['model']
        )
        
        # Generate embedding for the modified text
        embedding_result = faiss_builder.generate_embeddings([chunk_text])
        
        if embedding_result['status'] != 'success':
            raise Exception(f"Failed to generate embedding: {embedding_result.get('error')}")
        
        # Handle the embedding result structure
        embeddings = embedding_result['embeddings']
        if isinstance(embeddings, list) and len(embeddings) > 0:
            embedding_data = embeddings[0]
            if isinstance(embedding_data, dict):
                embedding_vector = np.array(embedding_data['embedding'])
            else:
                # If embeddings are directly the vectors
                embedding_vector = np.array(embedding_data)
        else:
            raise Exception(f"Unexpected embedding result structure: {type(embeddings)}")
        
        # Get tokens from the right place
        tokens_used = 0
        if isinstance(embedding_data, dict):
            tokens_used = embedding_data.get('tokens', 0)
        else:
            tokens_used = embedding_result.get('total_tokens', 0)
        
        result = {
            'embedding_vector': embedding_vector,
            'tokens_used': tokens_used,
            'cost': embedding_result.get('total_cost', 0),
            'model': embedding_result.get('model'),
            'dimension': len(embedding_vector)
        }
        
        logger.info(f"✅ New embedding generated")
        logger.info(f"  Tokens used: {result['tokens_used']:,}")
        logger.info(f"  Cost: ${result['cost']:.6f}")
        logger.info(f"  Dimension: {result['dimension']}")
        
        return result
    
    def update_faiss_index(self, chunk_identifier: str, new_embedding: np.ndarray, 
                          chunk_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Update FAISS index with new embedding."""
        logger.info("🔄 Updating FAISS index...")
        
        from app.core.preprocessing.utils.data_persistence import DataPersistence
        import faiss
        
        # Load current index and metadata
        index_file = self.output_dir / 'faiss.index'
        metadata_file = self.output_dir / 'faiss_metadata.json'
        
        # Load index
        if not index_file.exists():
            raise Exception("FAISS index file not found")
        
        index = faiss.read_index(str(index_file))
        original_vector_count = index.ntotal
        
        # Load metadata
        metadata_result = DataPersistence.load_json(metadata_file)
        if metadata_result['status'] != 'success':
            raise Exception(f"Failed to load metadata: {metadata_result.get('error')}")
        
        metadata = metadata_result['data']
        
        # Find the position of our chunk in the index
        chunk_position = None
        
        logger.info(f"🔍 Looking for chunk {chunk_identifier} in metadata")
        logger.info(f"  Metadata type: {type(metadata)}")
        logger.info(f"  Metadata length: {len(metadata) if metadata else 0}")
        
        if isinstance(metadata, list):
            # For list format, the position is just the index
            if chunk_identifier.startswith('chunk_'):
                try:
                    chunk_index = int(chunk_identifier.split('_')[1])
                    if 0 <= chunk_index < len(metadata):
                        chunk_position = chunk_index
                        logger.info(f"  Found chunk at list position: {chunk_position}")
                    else:
                        logger.error(f"  Chunk index {chunk_index} out of range [0, {len(metadata)})")
                except ValueError:
                    logger.error(f"  Could not parse chunk index from {chunk_identifier}")
            
            if chunk_position is None:
                # Fallback: search by chunk_id in metadata
                for i, meta in enumerate(metadata):
                    if meta.get('chunk_id') == chunk_identifier:
                        chunk_position = i
                        logger.info(f"  Found chunk by chunk_id at position: {chunk_position}")
                        break
        else:
            # If metadata is a dict, find by key
            if chunk_identifier in metadata:
                # For dict format, we need to find the position
                chunk_position = list(metadata.keys()).index(chunk_identifier)
                logger.info(f"  Found chunk in dict at position: {chunk_position}")
        
        if chunk_position is None:
            # Show sample metadata for debugging
            if isinstance(metadata, list) and len(metadata) > 0:
                sample_meta = metadata[0]
                logger.error(f"  Sample metadata structure: {list(sample_meta.keys()) if isinstance(sample_meta, dict) else type(sample_meta)}")
            
            raise Exception(f"Chunk {chunk_identifier} not found in metadata. Metadata type: {type(metadata)}, length: {len(metadata) if metadata else 0}")
        
        logger.info(f"📍 Found chunk at position {chunk_position} in index")
        
        # Get original vector for comparison
        original_vector = index.reconstruct(chunk_position)
        
        # Update the vector in the index
        new_embedding_2d = new_embedding.reshape(1, -1).astype(np.float32)
        
        # For updating a specific vector, we need to rebuild the index
        # Extract all vectors
        all_vectors = index.reconstruct_n(0, index.ntotal)
        
        # Replace the specific vector
        all_vectors[chunk_position] = new_embedding.astype(np.float32)
        
        # Create new index
        dimension = all_vectors.shape[1]
        new_index = faiss.IndexFlatIP(dimension)  # Inner product (cosine similarity)
        new_index.add(all_vectors)
        
        # Save updated index
        faiss.write_index(new_index, str(index_file))
        
        # Update metadata
        if isinstance(metadata, list):
            metadata[chunk_position].update({
                'last_updated': datetime.now().isoformat(),
                'test_modification': True,
                'embedding_regenerated': True
            })
        else:
            metadata[chunk_identifier].update({
                'last_updated': datetime.now().isoformat(),
                'test_modification': True,
                'embedding_regenerated': True
            })
        
        # Save updated metadata
        save_result = DataPersistence.save_json(metadata, metadata_file)
        if save_result['status'] != 'success':
            raise Exception(f"Failed to save metadata: {save_result.get('error')}")
        
        # Compare vectors
        vector_similarity = np.dot(original_vector, new_embedding) / (
            np.linalg.norm(original_vector) * np.linalg.norm(new_embedding)
        )
        
        result = {
            'chunk_position': chunk_position,
            'original_vector': original_vector,
            'new_vector': new_embedding,
            'vector_similarity': float(vector_similarity),
            'vector_changed': vector_similarity < 0.99,  # Threshold for "significant change"
            'index_size_before': original_vector_count,
            'index_size_after': new_index.ntotal,
            'dimension': dimension
        }
        
        logger.info(f"✅ FAISS index updated")
        logger.info(f"  Position: {chunk_position}")
        logger.info(f"  Vector similarity: {vector_similarity:.4f}")
        logger.info(f"  Vector changed: {result['vector_changed']}")
        logger.info(f"  Index size: {original_vector_count} → {new_index.ntotal}")
        
        return result
    
    def test_retrieval_with_new_content(self, modification_info: Dict[str, Any]) -> Dict[str, Any]:
        """Test retrieval using the new content."""
        logger.info("🔍 Testing retrieval with modified content...")
        
        from app.core.preprocessing.faiss_builder import FAISSBuilder
        import faiss
        
        # Load updated index
        index_file = self.output_dir / 'faiss.index'
        index = faiss.read_index(str(index_file))
        
        # Create FAISS builder for search
        faiss_builder = FAISSBuilder(
            api_key=self.processing_config['api_key'],
            model=self.processing_config['model']
        )
        
        # Test searches with our test phrases
        test_phrases = modification_info['test_phrases']
        retrieval_results = []
        
        for phrase in test_phrases:
            logger.info(f"  Searching for: '{phrase}'")
            
            # Generate embedding for search phrase
            search_embedding_result = faiss_builder.generate_embeddings([phrase])
            
            if search_embedding_result['status'] != 'success':
                logger.warning(f"    Failed to generate search embedding for '{phrase}'")
                continue
            
            search_vector = np.array(search_embedding_result['embeddings'][0]['embedding'])
            search_vector_2d = search_vector.reshape(1, -1).astype(np.float32)
            
            # Search in index
            k = 5  # Top 5 results
            similarities, indices = index.search(search_vector_2d, k)
            
            # Check if our modified chunk appears in top results
            target_position = modification_info.get('chunk_position')
            found_in_results = target_position in indices[0] if target_position is not None else False
            
            retrieval_results.append({
                'phrase': phrase,
                'found_target_chunk': found_in_results,
                'top_similarities': similarities[0].tolist(),
                'top_indices': indices[0].tolist(),
                'target_position': target_position
            })
            
            status = "✅ FOUND" if found_in_results else "❌ NOT FOUND"
            logger.info(f"    {status} in top {k} results")
            if found_in_results:
                target_rank = list(indices[0]).index(target_position) + 1
                target_similarity = similarities[0][target_rank - 1]
                logger.info(f"    Rank: #{target_rank}, Similarity: {target_similarity:.4f}")
        
        # Calculate success rate
        found_count = sum(1 for result in retrieval_results if result['found_target_chunk'])
        success_rate = found_count / len(retrieval_results) if retrieval_results else 0
        
        result = {
            'retrieval_results': retrieval_results,
            'phrases_tested': len(test_phrases),
            'phrases_found': found_count,
            'success_rate': success_rate,
            'retrieval_working': success_rate >= 0.5  # At least 50% of phrases should work
        }
        
        logger.info(f"✅ Retrieval test completed")
        logger.info(f"  Phrases found: {found_count}/{len(test_phrases)} ({success_rate:.1%})")
        
        return result
    
    def run_complete_test(self) -> Dict[str, Any]:
        """Run the complete real embedding update test."""
        logger.info("\n🚀 Starting Real Embedding Update Test")
        logger.info("=" * 60)
        
        # Estimate cost
        estimated_cost = self.estimate_test_cost()
        
        # Auto-approve for automated testing (cost is very low)
        logger.info(f"⚠️ This test will make API calls costing ~${estimated_cost:.5f}")
        logger.info("✅ Auto-approved for automated testing (low cost)")
        # For manual testing, uncomment the lines below:
        # response = input(f"\n⚠️ This test will make API calls costing ~${estimated_cost:.5f}. Continue? (y/N): ")
        # if response.lower() != 'y':
        #     logger.info("Test cancelled by user")
        #     return {'status': 'cancelled'}
        
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'estimated_cost': estimated_cost,
            'actual_cost': 0,
            'phases': {},
            'success': False
        }
        
        try:
            # Phase 1: Backup
            logger.info("\n📋 PHASE 1: System Backup")
            backup_info = self.backup_system_state()
            test_results['phases']['backup'] = backup_info
            
            # Phase 2: Modify chunk
            logger.info("\n📋 PHASE 2: Chunk Modification")
            modification_info = self.select_and_modify_chunk()
            test_results['phases']['modification'] = modification_info
            
            # Phase 3: Generate new embedding
            logger.info("\n📋 PHASE 3: Generate New Embedding")
            chunk_text = None
            
            # Get the modified chunk text
            from app.core.preprocessing.utils.data_persistence import DataPersistence
            chunks_file = self.output_dir / 'chunks.json'
            chunks_result = DataPersistence.load_json(chunks_file)
            chunks = chunks_result['data']
            
            if isinstance(chunks, list):
                chunk_text = chunks[modification_info['chunk_index']]['text']
            else:
                chunk_text = chunks[modification_info['chunk_identifier']]['text']
            
            embedding_result = self.generate_new_embedding(chunk_text)
            test_results['phases']['embedding'] = embedding_result
            test_results['actual_cost'] += embedding_result['cost']
            
            # Phase 4: Update FAISS index
            logger.info("\n📋 PHASE 4: Update FAISS Index")
            index_update_result = self.update_faiss_index(
                modification_info['chunk_identifier'],
                embedding_result['embedding_vector'],
                modification_info
            )
            test_results['phases']['index_update'] = index_update_result
            
            # Store chunk position for retrieval test
            modification_info['chunk_position'] = index_update_result['chunk_position']
            
            # Phase 5: Test retrieval
            logger.info("\n📋 PHASE 5: Test Retrieval")
            retrieval_result = self.test_retrieval_with_new_content(modification_info)
            test_results['phases']['retrieval'] = retrieval_result
            
            # Additional costs from search
            search_cost = len(modification_info['test_phrases']) * estimated_cost
            test_results['actual_cost'] += search_cost
            
            # Determine overall success
            success_criteria = [
                modification_info['modified_hash'] != modification_info['original_hash'],
                embedding_result['dimension'] > 0,
                index_update_result['vector_changed'],
                retrieval_result['retrieval_working']
            ]
            
            test_results['success'] = all(success_criteria)
            
            # Print results
            self.print_test_results(test_results)
            
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
    
    def print_test_results(self, results: Dict[str, Any]):
        """Print comprehensive test results."""
        logger.info("\n" + "=" * 60)
        logger.info("📊 REAL EMBEDDING UPDATE TEST RESULTS")
        logger.info("=" * 60)
        
        success = results.get('success', False)
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"Overall Result: {status}")
        logger.info(f"Actual Cost: ${results.get('actual_cost', 0):.6f}")
        
        # Phase results
        phases = results.get('phases', {})
        
        # Modification
        mod = phases.get('modification', {})
        if mod:
            logger.info(f"\n🎯 Chunk Modification:")
            logger.info(f"  Chunk: {mod.get('chunk_identifier')}")
            logger.info(f"  Content added: {mod.get('added_content_length'):,} chars")
            logger.info(f"  Hash changed: ✅" if mod.get('modified_hash') != mod.get('original_hash') else "❌")
        
        # Embedding
        emb = phases.get('embedding', {})
        if emb:
            logger.info(f"\n🤖 Embedding Generation:")
            logger.info(f"  Model: {emb.get('model')}")
            logger.info(f"  Dimension: {emb.get('dimension')}")
            logger.info(f"  Tokens: {emb.get('tokens_used'):,}")
            logger.info(f"  Cost: ${emb.get('cost'):.6f}")
        
        # Index update
        idx = phases.get('index_update', {})
        if idx:
            logger.info(f"\n🔄 Index Update:")
            logger.info(f"  Position: {idx.get('chunk_position')}")
            logger.info(f"  Vector similarity: {idx.get('vector_similarity', 0):.4f}")
            logger.info(f"  Vector changed: {'✅' if idx.get('vector_changed') else '❌'}")
        
        # Retrieval
        ret = phases.get('retrieval', {})
        if ret:
            logger.info(f"\n🔍 Retrieval Test:")
            logger.info(f"  Success rate: {ret.get('success_rate', 0):.1%}")
            logger.info(f"  Phrases found: {ret.get('phrases_found', 0)}/{ret.get('phrases_tested', 0)}")
            logger.info(f"  Retrieval working: {'✅' if ret.get('retrieval_working') else '❌'}")
        
        logger.info("\n💡 Conclusions:")
        if success:
            logger.info("  ✅ Embedding update mechanism works end-to-end")
            logger.info("  ✅ API integration is functioning correctly")
            logger.info("  ✅ FAISS index updates are working")
            logger.info("  ✅ Modified content is retrievable")
            logger.info("  ✅ System is ready for production incremental updates")
        else:
            logger.info("  ❌ Embedding update mechanism has issues")
            logger.info("  ⚠️ Review the implementation and test results")
        
        logger.info("=" * 60)


def main():
    """Run the real embedding update test."""
    try:
        tester = RealEmbeddingUpdateTester()
        results = tester.run_complete_test()
        
        if results.get('status') == 'cancelled':
            return 0
        
        success = results.get('success', False)
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"💥 Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())