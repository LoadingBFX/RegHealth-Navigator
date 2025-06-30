"""
init_processed_files.py

Script to initialize the processed_files.json tracking file based on existing chunks.json.
This is needed when migrating from the old processing system to the incremental system.
"""
import json
import os
import hashlib
import sys
from pathlib import Path

# Add the app directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

def get_file_hash(file_path: Path) -> str:
    """Get SHA256 hash of file content."""
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def init_processed_files():
    """Initialize processed_files.json based on existing chunks.json."""
    input_dir = Path(config.docs_data_path)
    output_folder = config.build_faiss_output_folder
    chunks_path = os.path.join(output_folder, "chunks.json")
    processed_files_path = os.path.join(output_folder, "processed_files.json")
    
    print(f"📁 Loading existing chunks from {chunks_path}")
    
    if not os.path.exists(chunks_path):
        print("❌ chunks.json not found. Please run xml_chunker.py first.")
        return
    
    # Load existing chunks
    with open(chunks_path, "r") as f:
        chunks = json.load(f)
    
    print(f"📊 Found {len(chunks)} chunks in existing database")
    
    # Group chunks by source file
    files_chunks = {}
    for chunk in chunks:
        full_path = chunk["metadata"].get("full_path")
        if full_path:
            files_chunks[full_path] = files_chunks.get(full_path, 0) + 1
    
    print(f"📄 Found {len(files_chunks)} source files")
    
    # Create processed files tracking
    processed_files = {}
    
    for full_path, chunk_count in files_chunks.items():
        file_path = Path(full_path)
        
        if not file_path.exists():
            print(f"⚠️ File not found: {full_path}")
            continue
        
        # Calculate relative path from input directory
        try:
            relative_path = file_path.relative_to(input_dir)
            file_key = str(relative_path)
        except ValueError:
            print(f"⚠️ File not in input directory: {full_path}")
            continue
        
        # Get file hash
        try:
            file_hash = get_file_hash(file_path)
        except Exception as e:
            print(f"⚠️ Error reading file {full_path}: {e}")
            continue
        
        # Get file modification time
        try:
            mtime = file_path.stat().st_mtime
        except Exception as e:
            print(f"⚠️ Error getting file stats for {full_path}: {e}")
            mtime = 0
        
        processed_files[file_key] = {
            "hash": file_hash,
            "processed_at": str(mtime),
            "chunks_count": chunk_count,
            "full_path": str(full_path)
        }
        
        print(f"✅ Tracked: {file_key} ({chunk_count} chunks)")
    
    # Save processed files tracking
    os.makedirs(output_folder, exist_ok=True)
    with open(processed_files_path, "w") as f:
        json.dump(processed_files, f, indent=2)
    
    print(f"📦 Saved processed files tracking to {processed_files_path}")
    print(f"✅ Initialized tracking for {len(processed_files)} files")

if __name__ == "__main__":
    init_processed_files() 