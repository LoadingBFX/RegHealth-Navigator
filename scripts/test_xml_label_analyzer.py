#!/usr/bin/env python3
"""
test_xml_label_analyzer.py

Unit tests for the XML label analyzer functionality.

Author: Fanxing Bu
Date: 2024-12-19
"""

import unittest
import tempfile
import os
from pathlib import Path
import xml.etree.ElementTree as ET
from analyze_xml_labels import XMLLabelAnalyzer

class TestXMLLabelAnalyzer(unittest.TestCase):
    """Test cases for XMLLabelAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = Path(self.temp_dir) / "test_data"
        self.test_data_dir.mkdir()
        
        # Create test XML files
        self.create_test_xml_files()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_test_xml_files(self):
        """Create test XML files with known structures."""
        # Create HOSPICE folder
        hospice_dir = self.test_data_dir / "HOSPICE"
        hospice_dir.mkdir()
        
        # Test file 1 - basic structure
        hospice_xml1 = """<?xml version="1.0"?>
<RULE>
    <PREAMB>
        <AGENCY>Test Agency</AGENCY>
        <SUBJECT>Test Subject</SUBJECT>
        <P>Test paragraph</P>
    </PREAMB>
    <SUPLINF>
        <HD>Test Header</HD>
        <P>More content</P>
    </SUPLINF>
</RULE>"""
        
        with open(hospice_dir / "test_hospice1.xml", "w") as f:
            f.write(hospice_xml1)
        
        # Test file 2 - different structure
        hospice_xml2 = """<?xml version="1.0"?>
<RULE>
    <PREAMB>
        <AGENCY>Test Agency</AGENCY>
        <SUBJECT>Test Subject</SUBJECT>
        <FTNT>Footnote content</FTNT>
    </PREAMB>
    <SUPLINF>
        <HD>Test Header</HD>
        <SECTION>Test Section</SECTION>
    </SUPLINF>
</RULE>"""
        
        with open(hospice_dir / "test_hospice2.xml", "w") as f:
            f.write(hospice_xml2)
        
        # Create MPFS folder with different labels
        mpfs_dir = self.test_data_dir / "MPFS"
        mpfs_dir.mkdir()
        
        mpfs_xml = """<?xml version="1.0"?>
<RULE>
    <PREAMB>
        <AGENCY>Test Agency</AGENCY>
        <SUBJECT>Test Subject</SUBJECT>
        <P>Test paragraph</P>
        <APPENDIX>Test Appendix</APPENDIX>
    </PREAMB>
    <SUPLINF>
        <HD>Test Header</HD>
        <CONTENTS>Table of Contents</CONTENTS>
    </SUPLINF>
</RULE>"""
        
        with open(mpfs_dir / "test_mpfs.xml", "w") as f:
            f.write(mpfs_xml)
        
        # Create SNF folder
        snf_dir = self.test_data_dir / "SNF"
        snf_dir.mkdir()
        
        snf_xml = """<?xml version="1.0"?>
<RULE>
    <PREAMB>
        <AGENCY>Test Agency</AGENCY>
        <SUBJECT>Test Subject</SUBJECT>
        <P>Test paragraph</P>
    </PREAMB>
    <SUPLINF>
        <HD>Test Header</HD>
        <P>More content</P>
    </SUPLINF>
</RULE>"""
        
        with open(snf_dir / "test_snf.xml", "w") as f:
            f.write(snf_xml)
    
    def test_extract_xml_labels(self):
        """Test extracting XML labels from a single file."""
        analyzer = XMLLabelAnalyzer(str(self.test_data_dir))
        test_file = self.test_data_dir / "HOSPICE" / "test_hospice1.xml"
        
        labels = analyzer.extract_xml_labels(test_file)
        expected_labels = {"RULE", "PREAMB", "AGENCY", "SUBJECT", "P", "SUPLINF", "HD"}
        
        self.assertEqual(labels, expected_labels)
    
    def test_analyze_folder(self):
        """Test analyzing a folder of XML files."""
        analyzer = XMLLabelAnalyzer(str(self.test_data_dir))
        result = analyzer.analyze_folder("HOSPICE")
        
        self.assertEqual(result["folder_name"], "HOSPICE")
        self.assertEqual(result["file_count"], 2)
        self.assertIn("test_hospice1.xml", result["file_labels"])
        self.assertIn("test_hospice2.xml", result["file_labels"])
        
        # Check that all expected labels are found
        all_labels = result["all_labels"]
        expected_labels = {"RULE", "PREAMB", "AGENCY", "SUBJECT", "P", "SUPLINF", "HD", "FTNT", "SECTION"}
        self.assertEqual(all_labels, expected_labels)
    
    def test_compare_folders(self):
        """Test comparing labels across folders."""
        analyzer = XMLLabelAnalyzer(str(self.test_data_dir))
        results = analyzer.compare_folders()
        
        # Check that all folders were analyzed
        self.assertIn("HOSPICE", results["folder_results"])
        self.assertIn("MPFS", results["folder_results"])
        self.assertIn("SNF", results["folder_results"])
        
        # Check that MPFS has unique labels
        unique_per_folder = results["unique_per_folder"]
        self.assertIn("MPFS", unique_per_folder)
        mpfs_unique = unique_per_folder["MPFS"]
        self.assertIn("APPENDIX", mpfs_unique)
        self.assertIn("CONTENTS", mpfs_unique)
        
        # Check consistency
        consistency = results["consistency_check"]
        self.assertFalse(consistency["label_sets_are_equal"])  # Should be different due to MPFS unique labels
    
    def test_common_labels(self):
        """Test finding common labels across folders."""
        analyzer = XMLLabelAnalyzer(str(self.test_data_dir))
        results = analyzer.compare_folders()
        
        common_labels = results["common_across_folders"]
        expected_common = {"RULE", "PREAMB", "AGENCY", "SUBJECT", "P", "SUPLINF", "HD"}
        
        self.assertEqual(common_labels, expected_common)
    
    def test_empty_folder(self):
        """Test handling of empty folder."""
        analyzer = XMLLabelAnalyzer(str(self.test_data_dir))
        
        # Create empty folder
        empty_dir = self.test_data_dir / "EMPTY"
        empty_dir.mkdir()
        
        result = analyzer.analyze_folder("EMPTY")
        self.assertEqual(result, {})  # Should return empty dict for empty folder
    
    def test_nonexistent_folder(self):
        """Test handling of nonexistent folder."""
        analyzer = XMLLabelAnalyzer(str(self.test_data_dir))
        result = analyzer.analyze_folder("NONEXISTENT")
        self.assertEqual(result, {})  # Should return empty dict for nonexistent folder

def run_tests():
    """Run all tests."""
    unittest.main(verbosity=2)

if __name__ == "__main__":
    run_tests() 