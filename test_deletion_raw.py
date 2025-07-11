#!/usr/bin/env python3
"""Test deletion without decorators to see raw errors."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'app'))

from app.core.preprocessing.incremental_manager import IncrementalManager

def test_raw_deletion():
    """Test deletion mechanism bypassing decorators."""
    print("🔍 Testing Raw Deletion")
    print("=" * 30)
    
    # Initialize manager
    manager = IncrementalManager('data', 'rag_data')
    
    # Get chunks and find a small file
    chunks = manager._load_chunks()
    file_counts = {}
    for chunk in chunks:
        source_file = chunk.get('metadata', {}).get('source_file', 'UNKNOWN')
        file_counts[source_file] = file_counts.get(source_file, 0) + 1
    
    # Get smallest real file
    real_files = [(f, c) for f, c in file_counts.items() if f != 'UNKNOWN' and f.endswith('.xml')]
    smallest_file, chunk_count = min(real_files, key=lambda x: x[1])
    
    print(f"Target: {smallest_file} ({chunk_count} chunks)")
    print(f"Before: {len(chunks)} chunks, {manager.faiss_builder.index.ntotal} vectors")
    
    # Simulate what remove_file does but without decorators
    try:
        # Step 1: Remove chunks for this file
        filtered_chunks, chunks_removed = manager._remove_file_chunks(chunks, smallest_file)
        print(f"Filtered chunks: {len(filtered_chunks)} (removed {chunks_removed})")
        
        # Step 2: Save updated chunks
        save_result = manager._save_chunks(filtered_chunks)
        print(f"Save result: {save_result['status']}")
        
        # Step 3: Try to reorganize index directly
        print("Attempting reorganization...")
        reorganize_result = manager._rebuild_index_by_reorganization(chunks, filtered_chunks, chunks_removed)
        print(f"Reorganization result: {reorganize_result}")
        
    except Exception as e:
        print(f"❌ Raw error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_raw_deletion()