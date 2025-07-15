#!/usr/bin/env python3
"""
Fix processed_files.json to match the renamed XML files.

This script updates the file paths in processed_files.json to match
the corrected year naming convention.
"""

import os
import json
import shutil
from pathlib import Path
import re

# Year mapping: old_year -> new_year
YEAR_MAPPING = {
    "2023": "2024",
    "2024": "2025", 
    "2025": "2026"
}

def get_new_file_path(old_file_path: str) -> str:
    """
    Convert old file path to new file path with corrected year.
    
    Args:
        old_file_path: Original file path (e.g., "MPFS/2023_MPFS_final_2023-24184.xml")
        
    Returns:
        New file path with corrected year (e.g., "MPFS/2024_MPFS_final_2024-24184.xml")
    """
    # Extract components from path: CATEGORY/YYYY_TYPE_TYPE_YYYY-XXXXX.xml
    pattern = r'^([A-Z]+)/(\d{4})_([A-Z]+)_([a-z]+)_\d{4}-\d+\.xml$'
    match = re.match(pattern, old_file_path)
    
    if not match:
        print(f"Warning: Could not parse file path pattern: {old_file_path}")
        return old_file_path
    
    category = match.group(1)
    old_year = match.group(2)
    file_type = match.group(3)
    rule_type = match.group(4)
    
    # Get new year from mapping
    if old_year in YEAR_MAPPING:
        new_year = YEAR_MAPPING[old_year]
        # Create new file path with corrected year
        new_file_path = f"{category}/{new_year}_{file_type}_{rule_type}_{new_year}-{old_file_path.split('-')[1]}"
        return new_file_path
    else:
        print(f"Warning: No mapping found for year {old_year} in {old_file_path}")
        return old_file_path

def main():
    """Main function to fix processed_files.json."""
    print("Fixing processed_files.json...")
    print("Year mapping:")
    for old_year, new_year in YEAR_MAPPING.items():
        print(f"  {old_year} -> {new_year}")
    
    # Get project root directory
    project_root = Path(__file__).parent.parent
    processed_files_path = project_root / "rag_data" / "processed_files.json"
    
    if not os.path.exists(processed_files_path):
        print(f"Error: {processed_files_path} not found")
        return
    
    print(f"\nProcessing: {processed_files_path}")
    
    # Load current processed files
    with open(processed_files_path, 'r') as f:
        processed_files = json.load(f)
    
    print(f"Found {len(processed_files)} processed files")
    
    # Create backup
    backup_path = str(processed_files_path) + '.backup2'
    shutil.copy2(processed_files_path, backup_path)
    print(f"Backup created: {backup_path}")
    
    # Update file paths
    updated_files = {}
    changes_made = 0
    
    for old_path, file_info in processed_files.items():
        new_path = get_new_file_path(old_path)
        
        if old_path != new_path:
            print(f"  Updating: {old_path} -> {new_path}")
            updated_files[new_path] = file_info
            changes_made += 1
        else:
            updated_files[old_path] = file_info
    
    if changes_made > 0:
        # Write updated file
        with open(processed_files_path, 'w') as f:
            json.dump(updated_files, f, indent=2)
        print(f"\nUpdated {changes_made} file paths")
    else:
        print("\nNo changes needed")
    
    print("\nVerification:")
    # Check if all files exist
    missing_files = []
    for file_path in updated_files.keys():
        full_path = project_root / "data" / file_path
        if not os.path.exists(full_path):
            missing_files.append(file_path)
            print(f"  ✗ {file_path} (file not found)")
        else:
            print(f"  ✓ {file_path}")
    
    if missing_files:
        print(f"\nWarning: {len(missing_files)} files are missing")
    else:
        print("\n✅ All files found!")

if __name__ == "__main__":
    main() 