#!/usr/bin/env python3
"""
analyze_xml_labels.py

Script to analyze XML files in the data directory and compare XML label types 
across different folders (HOSPICE, MPFS, SNF) to check for consistency.

Author: Fanxing Bu
Date: 2024-12-19
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Set, List, Tuple
import json
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class XMLLabelAnalyzer:
    """Analyzer for XML labels across different document types."""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the analyzer.
        
        Args:
            data_dir: Path to the data directory containing XML files
        """
        self.data_dir = Path(data_dir)
        self.folder_types = ["HOSPICE", "MPFS", "SNF"]
        self.results = {}
        
    def extract_xml_labels(self, xml_file_path: Path) -> Set[str]:
        """
        Extract all XML labels (tag names) from an XML file.
        
        Args:
            xml_file_path: Path to the XML file
            
        Returns:
            Set of XML label names found in the file
        """
        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            # Collect all unique tag names
            labels = set()
            for elem in root.iter():
                labels.add(elem.tag)
                
            return labels
            
        except ET.ParseError as e:
            logger.error(f"Error parsing XML file {xml_file_path}: {e}")
            return set()
        except Exception as e:
            logger.error(f"Unexpected error processing {xml_file_path}: {e}")
            return set()
    
    def analyze_folder(self, folder_name: str) -> Dict:
        """
        Analyze all XML files in a specific folder.
        
        Args:
            folder_name: Name of the folder to analyze
            
        Returns:
            Dictionary containing analysis results for the folder
        """
        folder_path = self.data_dir / folder_name
        
        if not folder_path.exists():
            logger.warning(f"Folder {folder_path} does not exist")
            return {}
        
        xml_files = list(folder_path.glob("*.xml"))
        logger.info(f"Found {len(xml_files)} XML files in {folder_name}")
        
        if not xml_files:
            logger.warning(f"No XML files found in {folder_name}")
            return {}
        
        # Analyze each file
        file_labels = {}
        all_labels = set()
        
        for xml_file in xml_files:
            logger.info(f"Processing {xml_file.name}")
            labels = self.extract_xml_labels(xml_file)
            file_labels[xml_file.name] = labels
            all_labels.update(labels)
        
        # Find common labels across all files in this folder
        if file_labels:
            common_labels = set.intersection(*file_labels.values())
        else:
            common_labels = set()
        
        return {
            "folder_name": folder_name,
            "file_count": len(xml_files),
            "file_labels": file_labels,
            "all_labels": all_labels,
            "common_labels": common_labels,
            "unique_labels_per_file": {name: len(labels) for name, labels in file_labels.items()}
        }
    
    def compare_folders(self) -> Dict:
        """
        Compare XML labels across all folders.
        
        Returns:
            Dictionary containing comparison results
        """
        logger.info("Starting XML label analysis across all folders...")
        
        # Analyze each folder
        folder_results = {}
        for folder_type in self.folder_types:
            logger.info(f"Analyzing folder: {folder_type}")
            folder_results[folder_type] = self.analyze_folder(folder_type)
        
        # Compare labels across folders
        all_folder_labels = {}
        for folder_type, result in folder_results.items():
            if result:  # Only include folders that were successfully analyzed
                all_folder_labels[folder_type] = result["all_labels"]
        
        # Find common labels across all folders
        if all_folder_labels:
            common_across_folders = set.intersection(*all_folder_labels.values())
        else:
            common_across_folders = set()
        
        # Find unique labels per folder
        unique_per_folder = {}
        for folder_type, labels in all_folder_labels.items():
            other_labels = set.union(*[l for f, l in all_folder_labels.items() if f != folder_type])
            unique_per_folder[folder_type] = labels - other_labels
        
        # Check for consistency
        consistency_check = {
            "all_folders_have_same_labels": len(common_across_folders) == len(set.union(*all_folder_labels.values())) if all_folder_labels else False,
            "label_sets_are_equal": len(set(map(frozenset, all_folder_labels.values()))) == 1 if all_folder_labels else False
        }
        
        comparison_results = {
            "folder_results": folder_results,
            "all_folder_labels": all_folder_labels,
            "common_across_folders": common_across_folders,
            "unique_per_folder": unique_per_folder,
            "consistency_check": consistency_check
        }
        
        return comparison_results
    
    def generate_report(self, results: Dict) -> str:
        """
        Generate a comprehensive report of the analysis.
        
        Args:
            results: Analysis results from compare_folders()
            
        Returns:
            Formatted report string
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("XML LABEL ANALYSIS REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Analysis Date: {os.popen('date').read().strip()}")
        report_lines.append("")
        
        # Summary statistics
        report_lines.append("SUMMARY STATISTICS:")
        report_lines.append("-" * 40)
        
        folder_results = results["folder_results"]
        for folder_type, result in folder_results.items():
            if result:
                report_lines.append(f"{folder_type}:")
                report_lines.append(f"  - Files processed: {result['file_count']}")
                report_lines.append(f"  - Total unique labels: {len(result['all_labels'])}")
                report_lines.append(f"  - Common labels across files: {len(result['common_labels'])}")
                report_lines.append("")
        
        # Consistency check
        consistency = results["consistency_check"]
        report_lines.append("CONSISTENCY ANALYSIS:")
        report_lines.append("-" * 40)
        report_lines.append(f"All folders have same label set: {consistency['all_folders_have_same_labels']}")
        report_lines.append(f"Label sets are exactly equal: {consistency['label_sets_are_equal']}")
        report_lines.append("")
        
        # Common labels across all folders
        common_labels = results["common_across_folders"]
        report_lines.append(f"COMMON LABELS ACROSS ALL FOLDERS ({len(common_labels)}):")
        report_lines.append("-" * 40)
        for label in sorted(common_labels):
            report_lines.append(f"  - {label}")
        report_lines.append("")
        
        # Unique labels per folder
        unique_per_folder = results["unique_per_folder"]
        report_lines.append("UNIQUE LABELS PER FOLDER:")
        report_lines.append("-" * 40)
        for folder_type, unique_labels in unique_per_folder.items():
            report_lines.append(f"{folder_type} ({len(unique_labels)} unique labels):")
            for label in sorted(unique_labels):
                report_lines.append(f"  - {label}")
            report_lines.append("")
        
        # Detailed breakdown per folder
        report_lines.append("DETAILED BREAKDOWN PER FOLDER:")
        report_lines.append("-" * 40)
        
        for folder_type, result in folder_results.items():
            if result:
                report_lines.append(f"{folder_type.upper()} FOLDER:")
                report_lines.append(f"  Total labels: {len(result['all_labels'])}")
                report_lines.append(f"  Labels: {', '.join(sorted(result['all_labels']))}")
                report_lines.append("")
                
                # File-level details
                report_lines.append("  File-level details:")
                for filename, labels in result["file_labels"].items():
                    report_lines.append(f"    {filename}: {len(labels)} labels")
                report_lines.append("")
        
        return "\n".join(report_lines)
    
    def save_results(self, results: Dict, output_file: str = "xml_label_analysis_results.json"):
        """
        Save analysis results to a JSON file.
        
        Args:
            results: Analysis results from compare_folders()
            output_file: Output file path
        """
        # Convert sets to lists for JSON serialization
        def convert_sets_to_lists(obj):
            if isinstance(obj, set):
                return sorted(list(obj))
            elif isinstance(obj, dict):
                return {k: convert_sets_to_lists(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_sets_to_lists(item) for item in obj]
            else:
                return obj
        
        json_results = convert_sets_to_lists(results)
        
        with open(output_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        logger.info(f"Results saved to {output_file}")
    
    def run_analysis(self) -> Tuple[Dict, str]:
        """
        Run the complete analysis.
        
        Returns:
            Tuple of (results_dict, report_string)
        """
        logger.info("Starting XML label analysis...")
        
        # Perform the analysis
        results = self.compare_folders()
        
        # Generate report
        report = self.generate_report(results)
        
        # Save results
        self.save_results(results)
        
        logger.info("Analysis completed successfully!")
        
        return results, report


def main():
    """Main function to run the XML label analysis."""
    analyzer = XMLLabelAnalyzer()
    results, report = analyzer.run_analysis()
    
    # Print the report
    print(report)
    
    # Print summary to console
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    
    consistency = results["consistency_check"]
    if consistency["label_sets_are_equal"]:
        print("✅ All folders use the same XML label set - CONSISTENT")
    else:
        print("❌ Folders have different XML label sets - INCONSISTENT")
        
        # Show differences
        all_folder_labels = results["all_folder_labels"]
        if len(all_folder_labels) > 1:
            print("\nDifferences found:")
            for folder_type, labels in all_folder_labels.items():
                other_labels = set.union(*[l for f, l in all_folder_labels.items() if f != folder_type])
                unique_labels = labels - other_labels
                if unique_labels:
                    print(f"  {folder_type} unique labels: {sorted(unique_labels)}")


if __name__ == "__main__":
    main() 