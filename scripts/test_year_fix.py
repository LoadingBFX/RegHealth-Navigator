#!/usr/bin/env python3
"""
Test script to verify the year naming fix.

This script checks:
1. XML file naming consistency
2. Processed files mapping
3. Chunks file references
4. FAISS metadata references
"""

import os
import json
from pathlib import Path
import re

def check_xml_files(data_dir: str):
    """Check XML file naming consistency."""
    print("Checking XML file naming...")
    
    issues = []
    for category_dir in ['MPFS', 'HOSPICE', 'SNF']:
        category_path = os.path.join(data_dir, category_dir)
        if not os.path.exists(category_path):
            continue
            
        print(f"\n  {category_dir}:")
        for filename in os.listdir(category_path):
            if filename.endswith('.xml'):
                # Check if filename follows expected pattern
                pattern = r'^(\d{4})_([A-Z]+)_([a-z]+)_\d{4}-\d+\.xml$'
                match = re.match(pattern, filename)
                
                if match:
                    year = match.group(1)
                    file_type = match.group(2)
                    rule_type = match.group(3)
                    
                    # Check if year is in expected range (2024-2026)
                    if year in ['2024', '2025', '2026']:
                        print(f"    ✓ {filename}")
                    else:
                        print(f"    ✗ {filename} (unexpected year: {year})")
                        issues.append(f"Unexpected year {year} in {filename}")
                else:
                    print(f"    ✗ {filename} (doesn't match pattern)")
                    issues.append(f"Pattern mismatch in {filename}")
    
    return issues

def check_processed_files(processed_files_path: str):
    """Check processed_files.json consistency."""
    print("\nChecking processed_files.json...")
    
    if not os.path.exists(processed_files_path):
        print("  ✗ File not found")
        return ["processed_files.json not found"]
    
    issues = []
    with open(processed_files_path, 'r') as f:
        processed_files = json.load(f)
    
    print(f"  Found {len(processed_files)} processed files")
    
    # Get project root directory for file existence check
    project_root = Path(processed_files_path).parent.parent
    
    for file_path, file_info in processed_files.items():
        # Check if file exists in data directory
        full_path = project_root / "data" / file_path
        if not os.path.exists(full_path):
            print(f"    ✗ {file_path} (file not found)")
            issues.append(f"File not found: {file_path}")
        else:
            print(f"    ✓ {file_path}")
            
        # Check if path follows expected pattern
        if not file_path.endswith('.xml'):
            print(f"    ✗ {file_path} (not an XML file)")
            issues.append(f"Not an XML file: {file_path}")
    
    return issues

def check_chunks_file(chunks_path: str):
    """Check chunks.json file references."""
    print("\nChecking chunks.json...")
    
    if not os.path.exists(chunks_path):
        print("  ✗ File not found")
        return ["chunks.json not found"]
    
    issues = []
    chunk_count = 0
    file_references = set()
    
    with open(chunks_path, 'r') as f:
        for line in f:
            chunk_count += 1
            # Look for file paths in the line
            if '"file_path"' in line:
                # Extract file path from JSON
                match = re.search(r'"file_path":\s*"([^"]+)"', line)
                if match:
                    file_path = match.group(1)
                    file_references.add(file_path)
    
    print(f"  Found {chunk_count} chunks")
    print(f"  Found {len(file_references)} unique file references")
    
    for file_path in sorted(file_references):
        if not os.path.exists(file_path):
            print(f"    ✗ {file_path} (file not found)")
            issues.append(f"File not found in chunks: {file_path}")
        else:
            print(f"    ✓ {file_path}")
    
    return issues

def check_faiss_metadata(faiss_metadata_path: str):
    """Check faiss_metadata.json file references."""
    print("\nChecking faiss_metadata.json...")
    
    if not os.path.exists(faiss_metadata_path):
        print("  ✗ File not found")
        return ["faiss_metadata.json not found"]
    
    issues = []
    metadata_count = 0
    file_references = set()
    
    with open(faiss_metadata_path, 'r') as f:
        for line in f:
            metadata_count += 1
            # Look for file paths in the line
            if '"file_path"' in line:
                # Extract file path from JSON
                match = re.search(r'"file_path":\s*"([^"]+)"', line)
                if match:
                    file_path = match.group(1)
                    file_references.add(file_path)
    
    print(f"  Found {metadata_count} metadata entries")
    print(f"  Found {len(file_references)} unique file references")
    
    for file_path in sorted(file_references):
        if not os.path.exists(file_path):
            print(f"    ✗ {file_path} (file not found)")
            issues.append(f"File not found in metadata: {file_path}")
        else:
            print(f"    ✓ {file_path}")
    
    return issues

def main():
    """Main test function."""
    print("="*60)
    print("YEAR NAMING FIX VERIFICATION")
    print("="*60)
    
    # Get project root directory
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    rag_data_dir = project_root / "rag_data"
    
    print(f"Project root: {project_root}")
    print(f"Data directory: {data_dir}")
    print(f"RAG data directory: {rag_data_dir}")
    
    all_issues = []
    
    # Check XML files
    xml_issues = check_xml_files(str(data_dir))
    all_issues.extend(xml_issues)
    
    # Check processed files
    processed_files_path = rag_data_dir / "processed_files.json"
    processed_issues = check_processed_files(str(processed_files_path))
    all_issues.extend(processed_issues)
    
    # Check chunks file
    chunks_path = rag_data_dir / "chunks.json"
    chunks_issues = check_chunks_file(str(chunks_path))
    all_issues.extend(chunks_issues)
    
    # Check FAISS metadata
    faiss_metadata_path = rag_data_dir / "faiss_metadata.json"
    metadata_issues = check_faiss_metadata(str(faiss_metadata_path))
    all_issues.extend(metadata_issues)
    
    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    if all_issues:
        print(f"❌ Found {len(all_issues)} issues:")
        for issue in all_issues:
            print(f"  - {issue}")
        print("\nPlease fix these issues before proceeding.")
    else:
        print("✅ All checks passed! The year naming fix appears to be successful.")
        print("\nNext steps:")
        print("1. Test the search functionality")
        print("2. Verify search results are correct")
        print("3. If everything works, you can remove the .backup files")

if __name__ == "__main__":
    main() 