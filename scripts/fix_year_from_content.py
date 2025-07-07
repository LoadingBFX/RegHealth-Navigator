#!/usr/bin/env python3
"""
Fix year naming by extracting the correct year from XML content.

This script:
1. Extracts the target year from XML content (SUBJECT field) using regex (CY XXXX)
2. Renames files by replacing the year in filename but keeping doc ID unchanged
3. Updates processed_files.json, chunks.json, and faiss_metadata.json accordingly
"""

import os
import json
import shutil
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional

def extract_year_from_xml(xml_path: str, category: str) -> Optional[str]:
    """
    Extract target year from XML content using category-specific patterns.
    
    Args:
        xml_path: Path to XML file
        category: One of 'MPFS', 'HOSPICE', 'SNF'
    Returns:
        Extracted year (e.g., "2024") or None if not found
    """
    try:
        with open(xml_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if category == 'SNF':
            # Federal Fiscal Year XXXX
            match = re.search(r'Federal Fiscal Year\s*(\d{4})', content, re.IGNORECASE)
            if match:
                return match.group(1)
        elif category == 'HOSPICE':
            # FY XXXX
            match = re.search(r'FY\s*(\d{4})', content, re.IGNORECASE)
            if match:
                return match.group(1)
        elif category == 'MPFS':
            # CY XXXX
            match = re.search(r'CY\s*(\d{4})', content, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    except Exception as e:
        print(f"Error reading {xml_path}: {e}")
        return None

def get_new_filename(old_filename: str, target_year: str) -> str:
    """
    Generate new filename with corrected year but keeping doc ID unchanged.
    
    Args:
        old_filename: Original filename (e.g., "2023_MPFS_final_2023-24184.xml")
        target_year: Target year from XML content (e.g., "2024")
        
    Returns:
        New filename (e.g., "2024_MPFS_final_2024-24184.xml")
    """
    # Parse filename pattern: YYYY_TYPE_TYPE_YYYY-XXXXX.xml
    pattern = r'^(\d{4})_([A-Z]+)_([a-z]+)_(\d{4})-(\d+)\.xml$'
    match = re.match(pattern, old_filename)
    
    if not match:
        print(f"Warning: Could not parse filename pattern: {old_filename}")
        return old_filename
    
    old_year1 = match.group(1)  # First year in filename
    file_type = match.group(2)
    rule_type = match.group(3)
    old_year2 = match.group(4)  # Second year in filename
    doc_id = match.group(5)     # Document ID
    
    # Create new filename with target year but keeping doc ID unchanged
    new_filename = f"{target_year}_{file_type}_{rule_type}_{target_year}-{doc_id}.xml"
    return new_filename

def rename_xml_files_with_content_analysis(data_dir: str) -> Dict[str, str]:
    """
    Rename XML files based on year extracted from content.
    
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
                
                # Extract target year from XML content
                target_year = extract_year_from_xml(old_path, category_dir)
                
                if target_year is None:
                    print(f"  Warning: Could not extract year from {filename} for {category_dir}, skipping")
                    continue
                
                # Generate new filename
                new_filename = get_new_filename(filename, target_year)
                new_path = os.path.join(category_path, new_filename)
                
                if old_path != new_path:
                    print(f"  Renaming: {filename} -> {new_filename} (target year: {target_year})")
                    try:
                        shutil.move(old_path, new_path)
                        file_mapping[old_path] = new_path
                    except Exception as e:
                        print(f"  Error renaming {filename}: {e}")
                else:
                    print(f"  No change needed: {filename} (already correct year: {target_year})")
    
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
        backup_path = processed_files_path + '.backup3'
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
    backup_path = chunks_path + '.backup3'
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
    backup_path = faiss_metadata_path + '.backup3'
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
    """Main function to execute the year naming fix based on content analysis."""
    print("Starting year naming fix based on XML content analysis...")
    
    # Get project root directory
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    rag_data_dir = project_root / "rag_data"
    
    print(f"\nProject root: {project_root}")
    print(f"Data directory: {data_dir}")
    print(f"RAG data directory: {rag_data_dir}")
    
    # Step 1: Rename XML files based on content analysis
    print("\n" + "="*60)
    print("STEP 1: Analyzing XML content and renaming files")
    print("="*60)
    file_mapping = rename_xml_files_with_content_analysis(str(data_dir))
    
    if not file_mapping:
        print("No files were renamed. Exiting.")
        return
    
    print(f"\nRenamed {len(file_mapping)} files:")
    for old_path, new_path in file_mapping.items():
        print(f"  {os.path.basename(old_path)} -> {os.path.basename(new_path)}")
    
    # Step 2: Update processed files
    print("\n" + "="*60)
    print("STEP 2: Updating processed files")
    print("="*60)
    processed_files_path = rag_data_dir / "processed_files.json"
    update_processed_files(str(processed_files_path), file_mapping)
    
    # Step 3: Update chunks file
    print("\n" + "="*60)
    print("STEP 3: Updating chunks file")
    print("="*60)
    chunks_path = rag_data_dir / "chunks.json"
    update_chunks_file(str(chunks_path), file_mapping)
    
    # Step 4: Update FAISS metadata
    print("\n" + "="*60)
    print("STEP 4: Updating FAISS metadata")
    print("="*60)
    faiss_metadata_path = rag_data_dir / "faiss_metadata.json"
    update_faiss_metadata(str(faiss_metadata_path), file_mapping)
    
    print("\n" + "="*60)
    print("Year naming fix completed!")
    print("="*60)
    print("\nSummary:")
    print(f"- Renamed {len(file_mapping)} XML files based on content analysis")
    print("- Updated processed_files.json")
    print("- Updated chunks.json") 
    print("- Updated faiss_metadata.json")
    print("\nBackup files created with .backup3 extension")
    print("\nNext steps:")
    print("1. Verify the changes look correct")
    print("2. Test the search functionality")
    print("3. If everything works, you can remove the .backup files")

if __name__ == "__main__":
    main() 