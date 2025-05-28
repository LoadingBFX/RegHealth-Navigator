"""
xml_structure_analysis.py

Script to analyze the structure of an XML file.

Usage:
    python scripts/xml_structure_analysis.py data/2025-06008.xml
"""
import sys
from lxml import etree
from collections import Counter

def analyze_structure(xml_path: str):
    """
    Analyze and print the tag structure and counts of an XML file.

    Args:
        xml_path (str): Path to the XML file.
    """
    tag_counter = Counter()
    for event, elem in etree.iterparse(xml_path, events=("start",)):
        tag_counter[elem.tag] += 1
    print("Tag counts:")
    for tag, count in tag_counter.most_common():
        print(f"{tag}: {count}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/xml_structure_analysis.py <xml_file>")
        sys.exit(1)
    analyze_structure(sys.argv[1]) 