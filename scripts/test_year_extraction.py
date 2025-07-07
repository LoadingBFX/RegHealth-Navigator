#!/usr/bin/env python3
"""
Test script to verify year extraction from XML content.
"""

import os
import re
from pathlib import Path

def extract_year_from_xml(xml_path: str, category: str):
    """Extract target year from XML content using category-specific patterns."""
    try:
        with open(xml_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if category == 'SNF':
            match = re.search(r'Federal Fiscal Year\s*(\d{4})', content, re.IGNORECASE)
            if match:
                return match.group(1), 'Federal Fiscal Year'
        elif category == 'HOSPICE':
            match = re.search(r'FY\s*(\d{4})', content, re.IGNORECASE)
            if match:
                return match.group(1), 'FY'
        elif category == 'MPFS':
            match = re.search(r'CY\s*(\d{4})', content, re.IGNORECASE)
            if match:
                return match.group(1), 'CY'
        return None, None
    except Exception as e:
        print(f"Error reading {xml_path}: {e}")
        return None, None

def main():
    """Test year extraction on all XML files by category."""
    print("Testing year extraction from XML content by category...")
    
    # Get project root directory
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    
    print(f"Data directory: {data_dir}")
    
    for category_dir in ['MPFS', 'HOSPICE', 'SNF']:
        category_path = data_dir / category_dir
        if not category_path.exists():
            continue
            
        print(f"\n{category_dir}:")
        
        for filename in os.listdir(category_path):
            if filename.endswith('.xml'):
                xml_path = category_path / filename
                extracted_year, source = extract_year_from_xml(str(xml_path), category_dir)
                
                if extracted_year:
                    print(f"  ✓ {filename} -> {source} {extracted_year}")
                else:
                    print(f"  ✗ {filename} -> No year found")

if __name__ == "__main__":
    main() 