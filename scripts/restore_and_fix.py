#!/usr/bin/env python3
"""
Restore original filenames and then rename with correct logic.
"""

import os
import shutil
from pathlib import Path

# Original filename mapping (before the wrong rename)
ORIGINAL_NAMES = {
    # MPFS
    "2025_MPFS_final_2025-2025.xml": "2026_MPFS_final_2026-08676.xml",
    "2024_MPFS_final_2024-2024.xml": "2025_MPFS_final_2025-02705.xml", 
    "2025_MPFS_proposed_2025-2025.xml": "2025_MPFS_proposed_2025-14828.xml",
    "2024_MPFS_final_2024-2024.xml": "2024_MPFS_final_2024-24184.xml",
    "2025_MPFS_final_2025-2025.xml": "2025_MPFS_final_2025-25382.xml",
    "2024_MPFS_proposed_2024-2024.xml": "2024_MPFS_proposed_2024-14624.xml",
    
    # HOSPICE
    "2024_HOSPICE_final_2024-2024.xml": "2024_HOSPICE_final_2024-16116.xml",
    "2025_HOSPICE_final_2025-2025.xml": "2025_HOSPICE_final_2025-16910.xml",
    "2025_HOSPICE_final_2025-2025.xml": "2025_HOSPICE_final_2025-22495.xml",
    "2025_HOSPICE_proposed_2025-2025.xml": "2025_HOSPICE_proposed_2025-06921.xml",
    "2026_HOSPICE_proposed_2026-2026.xml": "2026_HOSPICE_proposed_2026-06317.xml",
    
    # SNF
    "2024_SNF_final_2024-2024.xml": "2025_SNF_final_2025-07522.xml",
    "2025_SNF_proposed_2025-2025.xml": "2025_SNF_proposed_2025-06812.xml",
    "2025_SNF_final_2025-2025.xml": "2025_SNF_final_2025-22504.xml",
    "2024_SNF_final_2024-2024.xml": "2024_SNF_final_2024-16249.xml",
    "2026_SNF_proposed_2026-2026.xml": "2026_SNF_proposed_2026-06348.xml",
    "2025_SNF_final_2025-2025.xml": "2025_SNF_final_2025-16907.xml",
    "2024_SNF_final_2024-2024.xml": "2024_SNF_final_2024-22050.xml",
}

def restore_original_names():
    """Restore original filenames."""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    
    print("Restoring original filenames...")
    
    for wrong_name, original_name in ORIGINAL_NAMES.items():
        category = original_name.split('_')[1]
        wrong_path = data_dir / category / wrong_name
        original_path = data_dir / category / original_name
        
        if wrong_path.exists():
            print(f"  Restoring: {wrong_name} -> {original_name}")
            shutil.move(str(wrong_path), str(original_path))
        else:
            print(f"  Warning: {wrong_name} not found")

if __name__ == "__main__":
    restore_original_names() 