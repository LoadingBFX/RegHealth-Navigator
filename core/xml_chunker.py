"""
xml_chunker.py

Module for chunking a section of XML into smaller text chunks.

Example expected input:
    section_xml: str (XML string for a section)

Example output:
    List[dict] (each dict: text, location, metadata)

>>> chunk_section('<Section>...</Section>')
[
    {'text': '...', 'location': '1.1', 'metadata': {...}},
    {'text': '...', 'location': '1.2', 'metadata': {...}}
]
"""
from typing import List, Dict

def chunk_section(section_xml: str) -> List[Dict]:
    """
    Chunk a section XML string into smaller text chunks.

    Args:
        section_xml (str): XML string for a section.

    Returns:
        List[dict]: Each dict contains:
            - 'text': str
            - 'location': str (e.g., section/subsection id)
            - 'metadata': dict
    """
    pass 