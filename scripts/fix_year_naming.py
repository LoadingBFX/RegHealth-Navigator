#!/usr/bin/env python3
"""
Fix year naming in XML files and corresponding processed results.

This script corrects the year naming convention where:
- 2023 files should be 2024 (actual year 2024)
- 2024 files should be 2025 (actual year 2025)  
- 2025 files should be 2026 (actual year 2026)

The script will:
1. Rename XML files in data/ directories
2. Update processed_files.json with new file paths
3. Update chunks.json with new file paths
4. Update faiss_metadata.json with new file paths
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import re

# Year mapping: old_year -> new_year
YEAR_MAPPING = {
    "2023": "2024",
    "2024": "2025", 
    "2025": "2026"
}

def get_new_filename(old_filename: str) -> str:
    """
    Convert old filename to new filename with corrected year.
    
    Args:
        old_filename: Original filename (e.g., "2023_MPFS_final_2023-14624.xml")
        
    Returns:
        New filename with corrected year (e.g., "2024_MPFS_final_2024-14624.xml")
    """
    # Extract year from filename pattern: YYYY_TYPE_TYPE_YYYY-XXXXX.xml
    pattern = r'^(\d{4})_([A-Z]+)_([a-z]+)_\d{4}-\d+\.xml$'
    match = re.match(pattern, old_filename)
    
    if not match:
        print(f"Warning: Could not parse filename pattern: {old_filename}")
        return old_filename
    
    old_year = match.group(1)
    file_type = match.group(2)
    rule_type = match.group(3)
    
    # Get new year from mapping
    if old_year in YEAR_MAPPING:
        new_year = YEAR_MAPPING[old_year]
        # Create new filename with corrected year
        new_filename = f"{new_year}_{file_type}_{rule_type}_{new_year}-{old_filename.split('-')[1]}"
        return new_filename
    else:
        print(f"Warning: No mapping found for year {old_year} in {old_filename}")
        return old_filename

def rename_xml_files(data_dir: str) -> Dict[str, str]:
    """
    Rename XML files in data directory and return mapping of old to new paths.
    
    Args:
        data_dir: Path to data directory
        
    Returns:
        Dictionary mapping old file paths to new file paths
    """
    file_mapping = {}
    
    for category_dir in ['MPFS', 'HOSPICE', 'SNF']:
        category_path = os.path.join(data_dir, category_dir)
        if not os.path.exists(category_path):
            continue
            
        print(f"\nProcessing {category_dir} directory...")
        
        for filename in os.listdir(category_path):
            if filename.endswith('.xml'):
                old_path = os.path.join(category_path, filename)
                new_filename = get_new_filename(filename)
                new_path = os.path.join(category_path, new_filename)
                
                if old_path != new_path:
                    print(f"  Renaming: {filename} -> {new_filename}")
                    try:
                        shutil.move(old_path, new_path)
                        file_mapping[old_path] = new_path
                    except Exception as e:
                        print(f"  Error renaming {filename}: {e}")
                else:
                    print(f"  No change needed: {filename}")
    
    return file_mapping

def update_processed_files(processed_files_path: str, file_mapping: Dict[str, str]):
    """
    Update processed_files.json with new file paths.
    
    Args:
        processed_files_path: Path to processed_files.json
        file_mapping: Mapping of old to new file paths
    """
    if not os.path.exists(processed_files_path):
        print(f"Warning: {processed_files_path} not found")
        return
        
    print(f"\nUpdating {processed_files_path}...")
    
    with open(processed_files_path, 'r') as f:
        processed_files = json.load(f)
    
    updated_files = {}
    changes_made = 0
    
    for old_path, file_info in processed_files.items():
        # Convert relative path to absolute for comparison
        old_abs_path = os.path.abspath(old_path)
        
        # Find corresponding new path
        new_path = None
        for old_file_path, new_file_path in file_mapping.items():
            if old_file_path == old_abs_path:
                # Convert back to relative path
                new_path = os.path.relpath(new_file_path, os.path.dirname(processed_files_path))
                break
        
        if new_path:
            print(f"  Updating: {old_path} -> {new_path}")
            updated_files[new_path] = file_info
            changes_made += 1
        else:
            updated_files[old_path] = file_info
    
    if changes_made > 0:
        # Backup original file
        backup_path = processed_files_path + '.backup'
        shutil.copy2(processed_files_path, backup_path)
        print(f"  Backup created: {backup_path}")
        
        # Write updated file
        with open(processed_files_path, 'w') as f:
            json.dump(updated_files, f, indent=2)
        print(f"  Updated {changes_made} entries")
    else:
        print("  No changes needed")

def update_chunks_file(chunks_path: str, file_mapping: Dict[str, str]):
    """
    Update chunks.json with new file paths.
    
    Args:
        chunks_path: Path to chunks.json
        file_mapping: Mapping of old to new file paths
    """
    if not os.path.exists(chunks_path):
        print(f"Warning: {chunks_path} not found")
        return
        
    print(f"\nUpdating {chunks_path}...")
    
    # This file might be large, so we'll process it line by line
    backup_path = chunks_path + '.backup'
    shutil.copy2(chunks_path, backup_path)
    print(f"  Backup created: {backup_path}")
    
    changes_made = 0
    temp_path = chunks_path + '.tmp'
    
    with open(chunks_path, 'r') as infile, open(temp_path, 'w') as outfile:
        for line in infile:
            # Look for file paths in the JSON line
            for old_file_path, new_file_path in file_mapping.items():
                old_relative_path = os.path.relpath(old_file_path, os.path.dirname(chunks_path))
                new_relative_path = os.path.relpath(new_file_path, os.path.dirname(chunks_path))
                
                if old_relative_path in line:
                    line = line.replace(old_relative_path, new_relative_path)
                    changes_made += 1
                    print(f"  Updated chunk reference: {old_relative_path} -> {new_relative_path}")
            
            outfile.write(line)
    
    # Replace original with updated file
    shutil.move(temp_path, chunks_path)
    print(f"  Updated {changes_made} chunk references")

def update_faiss_metadata(faiss_metadata_path: str, file_mapping: Dict[str, str]):
    """
    Update faiss_metadata.json with new file paths.
    
    Args:
        faiss_metadata_path: Path to faiss_metadata.json
        file_mapping: Mapping of old to new file paths
    """
    if not os.path.exists(faiss_metadata_path):
        print(f"Warning: {faiss_metadata_path} not found")
        return
        
    print(f"\nUpdating {faiss_metadata_path}...")
    
    # This file might be large, so we'll process it line by line
    backup_path = faiss_metadata_path + '.backup'
    shutil.copy2(faiss_metadata_path, backup_path)
    print(f"  Backup created: {backup_path}")
    
    changes_made = 0
    temp_path = faiss_metadata_path + '.tmp'
    
    with open(faiss_metadata_path, 'r') as infile, open(temp_path, 'w') as outfile:
        for line in infile:
            # Look for file paths in the JSON line
            for old_file_path, new_file_path in file_mapping.items():
                old_relative_path = os.path.relpath(old_file_path, os.path.dirname(faiss_metadata_path))
                new_relative_path = os.path.relpath(new_file_path, os.path.dirname(faiss_metadata_path))
                
                if old_relative_path in line:
                    line = line.replace(old_relative_path, new_relative_path)
                    changes_made += 1
                    print(f"  Updated metadata reference: {old_relative_path} -> {new_relative_path}")
            
            outfile.write(line)
    
    # Replace original with updated file
    shutil.move(temp_path, faiss_metadata_path)
    print(f"  Updated {changes_made} metadata references")

def main():
    """Main function to execute the year naming fix."""
    print("Starting year naming fix...")
    print("Year mapping:")
    for old_year, new_year in YEAR_MAPPING.items():
        print(f"  {old_year} -> {new_year}")
    
    # Get project root directory
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    rag_data_dir = project_root / "rag_data"
    
    print(f"\nProject root: {project_root}")
    print(f"Data directory: {data_dir}")
    print(f"RAG data directory: {rag_data_dir}")
    
    # Step 1: Rename XML files
    print("\n" + "="*50)
    print("STEP 1: Renaming XML files")
    print("="*50)
    file_mapping = rename_xml_files(str(data_dir))
    
    if not file_mapping:
        print("No files were renamed. Exiting.")
        return
    
    print(f"\nRenamed {len(file_mapping)} files:")
    for old_path, new_path in file_mapping.items():
        print(f"  {os.path.basename(old_path)} -> {os.path.basename(new_path)}")
    
    # Step 2: Update processed files
    print("\n" + "="*50)
    print("STEP 2: Updating processed files")
    print("="*50)
    processed_files_path = rag_data_dir / "processed_files.json"
    update_processed_files(str(processed_files_path), file_mapping)
    
    # Step 3: Update chunks file
    print("\n" + "="*50)
    print("STEP 3: Updating chunks file")
    print("="*50)
    chunks_path = rag_data_dir / "chunks.json"
    update_chunks_file(str(chunks_path), file_mapping)
    
    # Step 4: Update FAISS metadata
    print("\n" + "="*50)
    print("STEP 4: Updating FAISS metadata")
    print("="*50)
    faiss_metadata_path = rag_data_dir / "faiss_metadata.json"
    update_faiss_metadata(str(faiss_metadata_path), file_mapping)
    
    print("\n" + "="*50)
    print("Year naming fix completed!")
    print("="*50)
    print("\nSummary:")
    print(f"- Renamed {len(file_mapping)} XML files")
    print("- Updated processed_files.json")
    print("- Updated chunks.json") 
    print("- Updated faiss_metadata.json")
    print("\nBackup files created with .backup extension")
    print("\nNext steps:")
    print("1. Verify the changes look correct")
    print("2. Test the search functionality")
    print("3. If everything works, you can remove the .backup files")

if __name__ == "__main__":
    main() 