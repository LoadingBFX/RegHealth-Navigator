#!/usr/bin/env python3
"""Test final deletion mechanism with proper expectations."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'app'))

from app.core.preprocessing.incremental_manager import IncrementalManager

def test_final_deletion():
    """Test deletion mechanism with proper expectations."""
    print("🧪 Testing Final Deletion Mechanism")
    print("=" * 50)
    
    # Initialize manager
    manager = IncrementalManager('data', 'rag_data')
    
    # Check data consistency first
    chunks = manager._load_chunks()
    metadata = manager.faiss_builder.metadata
    index_size = manager.faiss_builder.index.ntotal if manager.faiss_builder.index else 0
    
    print(f"📊 Initial state:")
    print(f"  Chunks: {len(chunks):,}")
    print(f"  Metadata: {len(metadata):,}") 
    print(f"  Index vectors: {index_size:,}")
    
    chunks_meta_consistent = len(chunks) == len(metadata)
    meta_index_consistent = len(metadata) == index_size
    
    print(f"\n🔍 Data consistency:")
    print(f"  Chunks ↔ Metadata: {'✅' if chunks_meta_consistent else '❌'}")
    print(f"  Metadata ↔ Index: {'✅' if meta_index_consistent else '❌'}")
    
    if chunks_meta_consistent and meta_index_consistent:
        print("  ✅ Data is consistent - efficient deletion should work")
        expected_efficient = True
    else:
        print("  ⚠️ Data inconsistent - will use fallback rebuild")
        expected_efficient = False
    
    # Find a file to test with
    file_counts = {}
    for chunk in chunks:
        source_file = chunk.get('metadata', {}).get('source_file', 'UNKNOWN')
        file_counts[source_file] = file_counts.get(source_file, 0) + 1
    
    # Get smallest real file with chunks
    real_files = [(f, c) for f, c in file_counts.items() 
                 if f != 'UNKNOWN' and f.endswith('.xml') and c > 0]
    
    if not real_files:
        print("❌ No suitable files found for testing")
        return
    
    test_file, chunk_count = min(real_files, key=lambda x: x[1])
    print(f"\n🎯 Testing deletion of: {test_file}")
    print(f"  Chunks to remove: {chunk_count:,}")
    
    # Perform deletion
    print(f"\n🗑️ Performing deletion...")
    result = manager.remove_file(f'MPFS/{test_file}')
    
    if result['status'] == 'success':
        print(f"\n✅ Deletion completed successfully:")
        print(f"  Chunks removed: {result.get('chunks_removed', 0):,}")
        print(f"  Embeddings removed: {result.get('embeddings_removed', 0):,}")
        rebuild_cost = result.get('rebuild_cost', 0)
        print(f"  Rebuild cost: ${rebuild_cost:.4f}")
        
        fallback_used = rebuild_cost > 0
        print(f"  Fallback rebuild: {'Yes' if fallback_used else 'No'}")
        
        # Check if behavior matched expectations
        if expected_efficient and not fallback_used:
            print(f"\n🎉 SUCCESS: Efficient deletion worked as expected!")
            print(f"  ✅ No API costs incurred")
            print(f"  ✅ Only reorganized existing vectors")
        elif not expected_efficient and fallback_used:
            print(f"\n✅ SUCCESS: Fallback rebuild worked as expected!")
            print(f"  ✅ System detected inconsistency correctly")
            print(f"  ✅ Used full rebuild to maintain data integrity")
            print(f"  💰 Cost: ${rebuild_cost:.4f} (necessary for consistency)")
        else:
            print(f"\n⚠️ Unexpected behavior:")
            print(f"  Expected efficient: {expected_efficient}")
            print(f"  Actually efficient: {not fallback_used}")
        
        # Verify final state
        final_chunks = manager._load_chunks()
        final_metadata = manager.faiss_builder.metadata
        final_index_size = manager.faiss_builder.index.ntotal if manager.faiss_builder.index else 0
        
        print(f"\n🔍 Final state:")
        print(f"  Chunks: {len(final_chunks):,}")
        print(f"  Metadata: {len(final_metadata):,}")
        print(f"  Index vectors: {final_index_size:,}")
        
        final_consistent = (len(final_chunks) == len(final_metadata) == final_index_size)
        print(f"  Data consistent: {'✅' if final_consistent else '❌'}")
        
        if final_consistent:
            print(f"\n🎉 PERFECT: System now has consistent data!")
            print(f"  ✅ Future deletions will be efficient")
            print(f"  ✅ No more fallback rebuilds needed")
        
    else:
        print(f"❌ Deletion failed: {result.get('error')}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_final_deletion()