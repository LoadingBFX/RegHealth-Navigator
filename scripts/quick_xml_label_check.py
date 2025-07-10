#!/usr/bin/env python3
"""
quick_xml_label_check.py

Quick script to check XML label consistency across data folders.
Provides a concise summary of whether different types use the same XML labels.

Author: Fanxing Bu
Date: 2024-12-19
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Set
import sys

def extract_labels_from_file(xml_path: Path) -> Set[str]:
    """Extract all XML labels from a single file."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        return {elem.tag for elem in root.iter()}
    except Exception as e:
        print(f"Error processing {xml_path}: {e}")
        return set()

def analyze_folder_labels(folder_path: Path) -> Set[str]:
    """Analyze all XML files in a folder and return all unique labels."""
    if not folder_path.exists():
        print(f"Folder {folder_path} does not exist")
        return set()
    
    xml_files = list(folder_path.glob("*.xml"))
    if not xml_files:
        print(f"No XML files found in {folder_path}")
        return set()
    
    all_labels = set()
    for xml_file in xml_files:
        labels = extract_labels_from_file(xml_file)
        all_labels.update(labels)
    
    return all_labels

def main():
    """Main function for quick XML label check."""
    data_dir = Path("data")
    folder_types = ["HOSPICE", "MPFS", "SNF"]
    
    print("=" * 60)
    print("QUICK XML LABEL CONSISTENCY CHECK")
    print("=" * 60)
    
    # Analyze each folder
    folder_labels = {}
    for folder_type in folder_types:
        folder_path = data_dir / folder_type
        print(f"\nAnalyzing {folder_type}...")
        
        labels = analyze_folder_labels(folder_path)
        folder_labels[folder_type] = labels
        print(f"  Found {len(labels)} unique XML labels")
    
    # Compare labels
    print("\n" + "=" * 60)
    print("COMPARISON RESULTS:")
    print("=" * 60)
    
    if not folder_labels:
        print("No data to compare")
        return
    
    # Find common labels across all folders
    common_labels = set.intersection(*folder_labels.values())
    print(f"\nCommon labels across all folders: {len(common_labels)}")
    
    # Check if all folders have the same label set
    all_labels_union = set.union(*folder_labels.values())
    is_consistent = len(common_labels) == len(all_labels_union)
    
    print(f"All folders use same label set: {'✅ YES' if is_consistent else '❌ NO'}")
    
    if not is_consistent:
        print("\nDifferences found:")
        for folder_type, labels in folder_labels.items():
            other_labels = set.union(*[l for f, l in folder_labels.items() if f != folder_type])
            unique_labels = labels - other_labels
            if unique_labels:
                print(f"  {folder_type} unique labels: {sorted(unique_labels)}")
    
    # Show label counts
    print(f"\nLabel counts per folder:")
    for folder_type, labels in folder_labels.items():
        print(f"  {folder_type}: {len(labels)} labels")
    
    # Show common labels
    if common_labels:
        print(f"\nCommon labels ({len(common_labels)}):")
        for label in sorted(common_labels):
            print(f"  - {label}")

if __name__ == "__main__":
    main() 