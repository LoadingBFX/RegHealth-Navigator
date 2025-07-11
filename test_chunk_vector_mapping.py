#!/usr/bin/env python3
"""Test chunk to vector mapping to understand the inconsistency."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'app'))

from app.core.preprocessing.incremental_manager import IncrementalManager

def analyze_chunk_vector_mapping():
    """Analyze the relationship between chunks and vectors."""
    print("🔍 Analyzing Chunk-Vector Mapping")
    print("=" * 40)
    
    # Initialize manager
    manager = IncrementalManager('data', 'rag_data')
    
    # Get all data
    chunks = manager._load_chunks()
    metadata = manager.faiss_builder.metadata
    index_size = manager.faiss_builder.index.ntotal if manager.faiss_builder.index else 0
    
    print(f"📊 Data counts:")
    print(f"  Chunks: {len(chunks):,}")
    print(f"  Metadata: {len(metadata):,}")
    print(f"  Index vectors: {index_size:,}")
    
    # Analyze file distribution in chunks vs metadata
    chunk_files = {}
    metadata_files = {}
    
    for chunk in chunks:
        source_file = chunk.get('metadata', {}).get('source_file', 'UNKNOWN')
        chunk_files[source_file] = chunk_files.get(source_file, 0) + 1
    
    for meta in metadata:
        source_file = meta.get('metadata', {}).get('source_file', 'UNKNOWN')
        metadata_files[source_file] = metadata_files.get(source_file, 0) + 1
    
    print(f"\n📁 File distribution comparison:")
    all_files = set(chunk_files.keys()) | set(metadata_files.keys())
    
    for filename in sorted(all_files):
        chunk_count = chunk_files.get(filename, 0)
        meta_count = metadata_files.get(filename, 0)
        status = "✅" if chunk_count == meta_count else "❌"
        print(f"  {status} {filename}: {chunk_count} chunks, {meta_count} vectors")
    
    # Test with a file that has mismatched counts
    mismatched_files = [(f, chunk_files.get(f, 0), metadata_files.get(f, 0)) 
                       for f in all_files 
                       if chunk_files.get(f, 0) != metadata_files.get(f, 0)]
    
    if mismatched_files:
        print(f"\n⚠️  Files with chunk-vector mismatches:")
        for filename, chunk_count, meta_count in mismatched_files:
            print(f"  {filename}: {chunk_count} chunks vs {meta_count} vectors (diff: {chunk_count - meta_count})")
    
    # Find a file that exists in both chunks and metadata
    matched_files = [(f, c) for f, c in chunk_files.items() 
                    if f in metadata_files and f != 'UNKNOWN' and f.endswith('.xml')]
    
    if matched_files:
        test_file, test_count = min(matched_files, key=lambda x: x[1])
        print(f"\n🎯 Testing with matched file: {test_file} ({test_count} entries in both)")
        
        # Test deletion
        try:
            print("Simulating deletion...")
            filtered_chunks, removed_chunks = manager._remove_file_chunks(chunks, test_file)
            
            # Check what would happen to metadata
            removed_metadata_count = 0
            for meta in metadata:
                if meta.get('metadata', {}).get('source_file') == test_file:
                    removed_metadata_count += 1
            
            print(f"  Would remove {removed_chunks} chunks")
            print(f"  Would remove {removed_metadata_count} metadata entries")
            
            if removed_chunks == removed_metadata_count and removed_chunks > 0:
                print(f"  ✅ This file should work for efficient deletion")
            else:
                print(f"  ❌ Mismatch would cause issues")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
    else:
        print("\n❌ No suitable files found for testing")

if __name__ == "__main__":
    analyze_chunk_vector_mapping()