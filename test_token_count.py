#!/usr/bin/env python3

import json
import sys
import os

# Add the current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from incremental_faiss import IncrementalFAISS
except ImportError:
    print("Error: Could not import IncrementalFAISS")
    sys.exit(1)

def test_token_counting():
    """Test token counting with actual data"""
    print("=== Token Counting Test ===")
    
    # Initialize the FAISS updater
    faiss_updater = IncrementalFAISS()
    
    # Load chunks
    chunks_file = "../../rag_data/chunks.json"
    with open(chunks_file, "r") as f:
        chunks = json.load(f)
    
    # Find MPFS 2024-14828 chunks
    mpfs_chunks = [c for c in chunks if '2024-14828' in c.get('metadata', {}).get('source_file', '')]
    
    print(f"Found {len(mpfs_chunks)} chunks for MPFS 2024-14828")
    
    if not mpfs_chunks:
        print("No chunks found!")
        return
    
    # Test token counting on first few chunks
    print("\nTesting token counting on first 5 chunks:")
    total_tokens = 0
    for i, chunk in enumerate(mpfs_chunks[:5]):
        text = chunk['text']
        tokens = faiss_updater.count_tokens(text)
        total_tokens += tokens
        print(f"Chunk {i+1}: {len(text)} chars, {tokens} tokens, ratio: {tokens/len(text):.3f}")
    
    print(f"\nFirst 5 chunks total: {total_tokens} tokens")
    
    # Calculate total tokens for all chunks
    print("\nCalculating total tokens for all chunks...")
    all_tokens = sum(faiss_updater.count_tokens(chunk['text']) for chunk in mpfs_chunks)
    print(f"Total tokens for all {len(mpfs_chunks)} chunks: {all_tokens:,}")
    
    # Compare with reported value
    reported_tokens = 14109286
    print(f"Reported tokens: {reported_tokens:,}")
    print(f"Difference: {abs(all_tokens - reported_tokens):,}")
    print(f"Match: {abs(all_tokens - reported_tokens) < 1000}")
    
    # Calculate cost
    estimated_cost = all_tokens / 1000 * 0.0001
    print(f"\nEstimated cost: ${estimated_cost:.4f}")

if __name__ == "__main__":
    test_token_counting() 