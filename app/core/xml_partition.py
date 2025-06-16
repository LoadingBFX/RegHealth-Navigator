"""
XML Partitioner Module

This module handles the partitioning of large XML documents into logical sections
for efficient processing and analysis.

Expected XML Format:
    <document>
        <section id="section1">
            <title>Section Title</title>
            <content>...</content>
        </section>
        ...
    </document>
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any
import logging
from pathlib import Path
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class XMLPartitioner:
    def __init__(self, cache_dir: str = "data/cache"):
        """
        Initialize the XML partitioner.
        
        Args:
            cache_dir: Directory to store partitioned sections
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def partition(self, content: bytes) -> List[Dict[str, Any]]:
        """
        Partition XML content into logical sections.
        
        Args:
            content: Raw XML content as bytes
            
        Returns:
            List of section metadata including id, title, and path
            
        Raises:
            ValueError: If XML is malformed or missing required elements
            IOError: If cache operations fail
        """
        try:
            root = ET.fromstring(content)
            sections = []
            
            for section in root.findall(".//section"):
                section_id = section.get("id")
                if not section_id:
                    raise ValueError(f"Section missing required 'id' attribute")
                    
                title = section.find("title")
                if title is None:
                    raise ValueError(f"Section {section_id} missing required 'title' element")
                    
                # Save section content to cache
                section_path = self.cache_dir / f"{section_id}.xml"
                with open(section_path, "wb") as f:
                    f.write(ET.tostring(section, encoding="utf-8"))
                
                sections.append({
                    "id": section_id,
                    "title": title.text,
                    "path": str(section_path)
                })
                
            # Save section metadata
            metadata_path = self.cache_dir / "sections.json"
            with open(metadata_path, "w") as f:
                json.dump(sections, f, indent=2)
                
            logger.info(f"Partitioned document into {len(sections)} sections")
            return sections
            
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML format: {str(e)}")
        except IOError as e:
            raise IOError(f"Failed to cache section: {str(e)}")
            
    def get_section(self, section_id: str) -> bytes:
        """
        Retrieve a specific section's content from cache.
        
        Args:
            section_id: ID of the section to retrieve
            
        Returns:
            Raw XML content of the section
            
        Raises:
            FileNotFoundError: If section is not found in cache
        """
        section_path = self.cache_dir / f"{section_id}.xml"
        if not section_path.exists():
            raise FileNotFoundError(f"Section {section_id} not found in cache")
            
        return section_path.read_bytes() 