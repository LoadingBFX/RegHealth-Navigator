"""
xml_token_count.py

Script to count words and tokens in an XML file.

Usage:
    python scripts/xml_token_count.py data/2025-06008.xml
"""
import sys
from lxml import etree

def count_tokens(xml_path: str):
    """
    Count and print the number of words and tokens in an XML file.

    Args:
        xml_path (str): Path to the XML file.
    """
    word_count = 0
    token_count = 0
    for event, elem in etree.iterparse(xml_path, events=("end",)):
        if elem.text:
            words = elem.text.split()
            word_count += len(words)
            token_count += len(words)  # Simple whitespace tokenization
    print(f"Words: {word_count}")
    print(f"Tokens: {token_count}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/xml_token_count.py <xml_file>")
        sys.exit(1)
    count_tokens(sys.argv[1]) 