#!/usr/bin/env python3
"""Debug deletion mechanism."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'app'))

from app.core.preprocessing.incremental_manager import IncrementalManager

def debug_deletion():
    """Debug deletion mechanism step by step."""
    print("🔍 Debugging Deletion Mechanism")
    print("=" * 50)
    
    # Initialize manager
    manager = IncrementalManager('data', 'rag_data')
    
    # Check current state
    chunks = manager._load_chunks()
    print(f"📊 Current state:")
    print(f"  Chunks loaded: {len(chunks):,}")
    print(f"  Index vectors: {manager.faiss_builder.index.ntotal if manager.faiss_builder.index else 0:,}")
    print(f"  Metadata entries: {len(manager.faiss_builder.metadata):,}")
    
    # Show data consistency
    if manager.faiss_builder.index and manager.faiss_builder.metadata:
        index_size = manager.faiss_builder.index.ntotal
        metadata_size = len(manager.faiss_builder.metadata)
        chunks_size = len(chunks)
        
        print(f"\n🔍 Data consistency check:")
        print(f"  Chunks: {chunks_size:,}")
        print(f"  Index vectors: {index_size:,}")
        print(f"  Metadata entries: {metadata_size:,}")
        print(f"  Chunks vs Index: {'✅' if chunks_size == index_size else '❌'}")
        print(f"  Index vs Metadata: {'✅' if index_size == metadata_size else '❌'}")
        
        if index_size != metadata_size:
            print(f"  ⚠️ Index-metadata mismatch detected!")
            print(f"     This will trigger fallback to full rebuild")
    
    # Test the simple solution: just run the original test with current data
    print(f"\n🧪 Now testing deletion with current implementation...")
    
    # Find a small file
    file_counts = {}
    for chunk in chunks:
        source_file = chunk.get('metadata', {}).get('source_file', 'UNKNOWN')
        file_counts[source_file] = file_counts.get(source_file, 0) + 1
    
    # Get smallest real file
    real_files = [(f, c) for f, c in file_counts.items() if f != 'UNKNOWN' and f.endswith('.xml')]
    if not real_files:
        print("❌ No XML files found in chunks")
        return
    
    smallest_file, chunk_count = min(real_files, key=lambda x: x[1])
    print(f"  Target file: {smallest_file}")
    print(f"  Chunks to remove: {chunk_count:,}")
    
    # Try the deletion
    try:
        result = manager.remove_file(f'MPFS/{smallest_file}')
        print(f"\n✅ Deletion result:")
        print(f"  Status: {result.get('status')}")
        print(f"  Chunks removed: {result.get('chunks_removed', 0):,}")
        print(f"  Rebuild cost: ${result.get('rebuild_cost', 0):.4f}")
        print(f"  Fallback used: {result.get('fallback_rebuild', False)}")
        
        if result.get('fallback_rebuild'):
            print(f"  ⚠️ Used fallback rebuild (not efficient)")
        elif result.get('rebuild_cost', 0) == 0:
            print(f"  ✅ Efficient deletion successful!")
        
    except Exception as e:
        print(f"❌ Deletion failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_deletion()