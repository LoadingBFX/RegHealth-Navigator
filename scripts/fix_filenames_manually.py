#!/usr/bin/env python3
"""
Manually fix filenames to keep doc ID unchanged but correct the year.
"""

import os
import shutil
from pathlib import Path

# Mapping of current wrong names to correct names (keeping doc ID)
CORRECT_NAMES = {
    # MPFS - extracted year: 2025, 2024
    "2025_MPFS_final_2025-2025.xml": "2025_MPFS_final_2025-08676.xml",  # was 2026_MPFS_final_2026-08676.xml
    "2024_MPFS_final_2024-2024.xml": "2024_MPFS_final_2024-02705.xml",  # was 2025_MPFS_final_2025-02705.xml
    "2025_MPFS_proposed_2025-2025.xml": "2025_MPFS_proposed_2025-14828.xml",  # was 2025_MPFS_proposed_2025-14828.xml
    "2024_MPFS_final_2024-2024.xml": "2024_MPFS_final_2024-24184.xml",  # was 2024_MPFS_final_2024-24184.xml
    "2025_MPFS_final_2025-2025.xml": "2025_MPFS_final_2025-25382.xml",  # was 2025_MPFS_final_2025-25382.xml
    "2024_MPFS_proposed_2024-2024.xml": "2024_MPFS_proposed_2024-14624.xml",  # was 2024_MPFS_proposed_2024-14624.xml
    
    # HOSPICE - extracted year: 2024, 2025, 2026
    "2024_HOSPICE_final_2024-2024.xml": "2024_HOSPICE_final_2024-16116.xml",  # was 2024_HOSPICE_final_2024-16116.xml
    "2025_HOSPICE_final_2025-2025.xml": "2025_HOSPICE_final_2025-16910.xml",  # was 2025_HOSPICE_final_2025-16910.xml
    "2025_HOSPICE_final_2025-2025.xml": "2025_HOSPICE_final_2025-22495.xml",  # was 2025_HOSPICE_final_2025-22495.xml
    "2025_HOSPICE_proposed_2025-2025.xml": "2025_HOSPICE_proposed_2025-06921.xml",  # was 2025_HOSPICE_proposed_2025-06921.xml
    "2026_HOSPICE_proposed_2026-2026.xml": "2026_HOSPICE_proposed_2026-06317.xml",  # was 2026_HOSPICE_proposed_2026-06317.xml
    
    # SNF - extracted year: 2024, 2025, 2026
    "2024_SNF_final_2024-2024.xml": "2024_SNF_final_2024-07522.xml",  # was 2025_SNF_final_2025-07522.xml
    "2025_SNF_proposed_2025-2025.xml": "2025_SNF_proposed_2025-06812.xml",  # was 2025_SNF_proposed_2025-06812.xml
    "2025_SNF_final_2025-2025.xml": "2025_SNF_final_2025-22504.xml",  # was 2025_SNF_final_2025-22504.xml
    "2024_SNF_final_2024-2024.xml": "2024_SNF_final_2024-16249.xml",  # was 2024_SNF_final_2024-16249.xml
    "2026_SNF_proposed_2026-2026.xml": "2026_SNF_proposed_2026-06348.xml",  # was 2026_SNF_proposed_2026-06348.xml
    "2025_SNF_final_2025-2025.xml": "2025_SNF_final_2025-16907.xml",  # was 2025_SNF_final_2025-16907.xml
    "2024_SNF_final_2024-2024.xml": "2024_SNF_final_2024-22050.xml",  # was 2024_SNF_final_2024-22050.xml
}

def fix_filenames():
    """Fix filenames to keep doc ID unchanged but correct the year."""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    
    print("Fixing filenames to keep doc ID unchanged...")
    
    for wrong_name, correct_name in CORRECT_NAMES.items():
        category = correct_name.split('_')[1]
        wrong_path = data_dir / category / wrong_name
        correct_path = data_dir / category / correct_name
        
        if wrong_path.exists():
            print(f"  Fixing: {wrong_name} -> {correct_name}")
            shutil.move(str(wrong_path), str(correct_path))
        else:
            print(f"  Warning: {wrong_name} not found")

if __name__ == "__main__":
    fix_filenames() 