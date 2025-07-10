#!/usr/bin/env python3
"""
Unit tests for filename generation logic consistency.
"""

import sys
import os
import unittest
from pathlib import Path

# Add the app directory to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.data_fetcher.fetch_regulations import (
    generate_filename,
    extract_year_from_title,
    detect_program_type
)

class TestFilenameGeneration(unittest.TestCase):
    """Test cases for filename generation logic."""
    
    def test_mpfs_filename_generation(self):
        """Test MPFS filename generation with strict keyword matching."""
        test_cases = [
            {
                "doc": {
                    "document_number": "2024-06432",
                    "title": "Medicare Physician Fee Schedule; Calendar Year (CY) 2024 Payment Policies",
                    "type": "Proposed Rule"
                },
                "expected_filename": "2024_MPFS_proposed_2024-06432.xml"
            },
            {
                "doc": {
                    "document_number": "2023-06433",
                    "title": "CY 2023 Medicare Physician Fee Schedule Final Rule",
                    "type": "Rule"
                },
                "expected_filename": "2023_MPFS_final_2023-06433.xml"
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(doc=test_case["doc"]):
                doc = test_case["doc"]
                expected = test_case["expected_filename"]
                
                # Test program type detection
                has_program, program_type = detect_program_type(doc)
                self.assertTrue(has_program, f"Should detect MPFS program type for: {doc['title']}")
                self.assertEqual(program_type, "MPFS")
                
                # Test filename generation
                filename = generate_filename(doc, program_type)
                self.assertIsNotNone(filename, f"Should generate filename for: {doc['title']}")
                self.assertEqual(filename, expected, f"Expected {expected}, got {filename}")
    
    def test_hospice_filename_generation(self):
        """Test HOSPICE filename generation with different title formats."""
        test_cases = [
            {
                "doc": {
                    "document_number": "2024-06921",
                    "title": "Medicare Program; FY 2025 Hospice Wage Index and Payment Rate Update",
                    "type": "Proposed Rule"
                },
                "expected_filename": "2025_HOSPICE_proposed_2024-06921.xml"
            },
            {
                "doc": {
                    "document_number": "2023-06922",
                    "title": "Hospice Wage Index for Fiscal Year (FY) 2024",
                    "type": "Rule"
                },
                "expected_filename": "2024_HOSPICE_final_2023-06922.xml"
            },
            {
                "doc": {
                    "document_number": "2022-06923",
                    "title": "FY 2023 Hospice Payment System Update",
                    "type": "Proposed Rule"
                },
                "expected_filename": "2023_HOSPICE_proposed_2022-06923.xml"
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(doc=test_case["doc"]):
                doc = test_case["doc"]
                expected = test_case["expected_filename"]
                
                # Test program type detection
                has_program, program_type = detect_program_type(doc)
                self.assertTrue(has_program, f"Should detect HOSPICE program type for: {doc['title']}")
                self.assertEqual(program_type, "HOSPICE")
                
                # Test filename generation
                filename = generate_filename(doc, program_type)
                self.assertIsNotNone(filename, f"Should generate filename for: {doc['title']}")
                self.assertEqual(filename, expected, f"Expected {expected}, got {filename}")
    
    def test_snf_filename_generation(self):
        """Test SNF filename generation with strict keyword matching."""
        test_cases = [
            {
                "doc": {
                    "document_number": "2024-06435",
                    "title": "Skilled Nursing Facility Prospective Payment System and Consolidated Billing for SNF",
                    "type": "Rule"
                },
                "expected_filename": "2024_SNF_final_2024-06435.xml"
            },
            {
                "doc": {
                    "document_number": "2023-06436",
                    "title": "SNF Prospective Payment System Rate Update",
                    "type": "Proposed Rule"
                },
                "expected_filename": "2023_SNF_proposed_2023-06436.xml"
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(doc=test_case["doc"]):
                doc = test_case["doc"]
                expected = test_case["expected_filename"]
                
                # Test program type detection
                has_program, program_type = detect_program_type(doc)
                self.assertTrue(has_program, f"Should detect SNF program type for: {doc['title']}")
                self.assertEqual(program_type, "SNF")
                
                # Test filename generation
                filename = generate_filename(doc, program_type)
                self.assertIsNotNone(filename, f"Should generate filename for: {doc['title']}")
                self.assertEqual(filename, expected, f"Expected {expected}, got {filename}")
    
    def test_correction_document_handling(self):
        """Test that correction documents are properly handled."""
        doc = {
            "document_number": "2024-06431",
            "title": "Medicare Physician Fee Schedule; Calendar Year (CY) 2025; Correction",
            "type": "Rule"
        }
        
        # Test program type detection (should return False for correction documents)
        has_program, program_type = detect_program_type(doc)
        self.assertFalse(has_program, "Should not detect program type for correction documents")
        self.assertEqual(program_type, "")
    
    def test_missing_data_handling(self):
        """Test handling of documents with missing data."""
        # Test missing document number
        doc_no_number = {
            "title": "Medicare Physician Fee Schedule; Calendar Year (CY) 2025 Payment Policies",
            "type": "Rule"
        }
        
        filename = generate_filename(doc_no_number, "MPFS")
        self.assertIsNone(filename, "Should return None for missing document number")
        
        # Test missing document type
        doc_no_type = {
            "document_number": "2024-06431",
            "title": "Medicare Physician Fee Schedule; Calendar Year (CY) 2025 Payment Policies"
        }
        
        filename = generate_filename(doc_no_type, "MPFS")
        self.assertIsNone(filename, "Should return None for missing document type")
        
        # Test missing title (year extraction fails)
        doc_no_title = {
            "document_number": "2024-06431",
            "type": "Rule"
        }
        
        filename = generate_filename(doc_no_title, "MPFS")
        self.assertIsNone(filename, "Should return None when year extraction fails")
    
    def test_year_extraction_consistency(self):
        """Test that year extraction is consistent across different functions."""
        doc = {
            "document_number": "2024-06432",
            "title": "Medicare Physician Fee Schedule; Calendar Year (CY) 2024 Payment Policies",
            "type": "Proposed Rule"
        }
        
        # Test program type detection
        has_program, program_type = detect_program_type(doc)
        self.assertTrue(has_program)
        self.assertEqual(program_type, "MPFS")
        
        # Test year extraction
        issue_year = extract_year_from_title(doc, program_type)
        self.assertEqual(issue_year, "2024")
        
        # Test filename generation
        filename = generate_filename(doc, program_type)
        self.assertEqual(filename, "2024_MPFS_proposed_2024-06432.xml")
        
        # Verify consistency: filename should contain the extracted year
        self.assertIn(issue_year, filename)

if __name__ == '__main__':
    unittest.main(verbosity=2) 