#!/usr/bin/env python3
"""
Test Efficient Deletion Mechanism

Test that file deletion uses efficient reorganization instead of full rebuild.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'app'))

from app.core.preprocessing.incremental_manager import IncrementalManager

def test_efficient_deletion():
    """Test efficient deletion mechanism."""
    print("🧪 Testing Efficient Deletion Mechanism")
    print("=" * 50)
    
    # Initialize manager
    manager = IncrementalManager('data', 'rag_data')
    
    # Get initial status
    chunks = manager._load_chunks()
    initial_chunk_count = len(chunks)
    initial_vector_count = manager.faiss_builder.index.ntotal if manager.faiss_builder.index else 0
    
    print(f"🔍 Initial status:")
    print(f"  Total chunks: {initial_chunk_count:,}")
    print(f"  Index vectors: {initial_vector_count:,}")
    
    # Find files and their chunk counts
    file_counts = {}
    for chunk in chunks:
        source_file = chunk.get('metadata', {}).get('source_file', 'UNKNOWN')
        file_counts[source_file] = file_counts.get(source_file, 0) + 1
    
    # Show available files
    print("\n📁 Available files:")
    sorted_files = sorted(file_counts.items(), key=lambda x: x[1])
    for filename, count in sorted_files[:5]:  # Show first 5
        print(f"  {filename}: {count:,} chunks")
    
    # Test with smallest real file (not UNKNOWN)
    test_file = None
    chunk_count = 0
    for filename, count in sorted_files:
        if filename != 'UNKNOWN' and filename.endswith('.xml'):
            test_file = filename
            chunk_count = count
            break
    
    if not test_file:
        print("❌ No suitable test file found")
        return
    
    print(f"\n🎯 Testing deletion of: {test_file}")
    print(f"  Chunks to remove: {chunk_count:,}")
    
    # Perform deletion using efficient method
    print("\n🗑️ Performing efficient deletion...")
    result = manager.remove_file(f'MPFS/{test_file}')
    
    if result['status'] == 'success':
        print("\n✅ Deletion completed:")
        chunks_removed = result.get('chunks_removed', 0)
        embeddings_removed = result.get('embeddings_removed', 0) 
        rebuild_cost = result.get('rebuild_cost', 0)
        remaining_chunks = result.get('remaining_chunks', 0)
        
        print(f"  Chunks removed: {chunks_removed:,}")
        print(f"  Embeddings removed: {embeddings_removed:,}")
        print(f"  Rebuild cost: ${rebuild_cost:.4f}")
        print(f"  Remaining chunks: {remaining_chunks:,}")
        
        print("\n🔍 After deletion:")
        final_chunks = manager._load_chunks()
        final_chunk_count = len(final_chunks)
        final_vector_count = manager.faiss_builder.index.ntotal if manager.faiss_builder.index else 0
        
        print(f"  Total chunks: {final_chunk_count:,}")
        print(f"  Index vectors: {final_vector_count:,}")
        print(f"  Chunk difference: {initial_chunk_count - final_chunk_count:,}")
        print(f"  Vector difference: {initial_vector_count - final_vector_count:,}")
        
        # Verify efficiency
        if rebuild_cost == 0.0:
            print("\n🎉 SUCCESS: Efficient deletion confirmed!")
            print("  ✅ No API calls made (cost = $0)")
            print("  ✅ Only reorganized existing vectors")
            print("  ✅ No embeddings regenerated")
        else:
            print(f"\n⚠️  WARNING: Cost was ${rebuild_cost:.4f} (should be $0)")
        
        # Verify data consistency  
        expected_remaining = initial_chunk_count - chunk_count
        if final_chunk_count == expected_remaining:
            print("  ✅ Chunk count is correct")
        else:
            print(f"  ❌ Chunk count mismatch: expected {expected_remaining}, got {final_chunk_count}")
            
    else:
        print(f"❌ Deletion failed: {result.get('error')}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_efficient_deletion()