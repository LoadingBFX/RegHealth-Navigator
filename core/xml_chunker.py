"""
XML Chunker Module

This module handles the chunking of XML sections into smaller, manageable pieces
for processing by LLMs and other downstream components.

Expected Section Format:
    <section id="section1">
        <title>Section Title</title>
        <content>
            <paragraph>...</paragraph>
            <paragraph>...</paragraph>
        </content>
    </section>
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any
import logging
from pathlib import Path
import json
from .xml_partition import XMLPartitioner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class XMLChunker:
    def __init__(self, chunk_size: int = 1000, overlap: int = 100, cache_dir: str = "data/cache"):
        """
        Initialize the XML chunker.
        
        Args:
            chunk_size: Maximum number of characters per chunk
            overlap: Number of characters to overlap between chunks
            cache_dir: Directory to store chunked sections
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.cache_dir = Path(cache_dir) / "chunks"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.partitioner = XMLPartitioner()
        
    def chunk_section(self, section_id: str) -> List[Dict[str, Any]]:
        """
        Chunk a section into smaller pieces.
        
        Args:
            section_id: ID of the section to chunk
            
        Returns:
            List of chunks with metadata
            
        Raises:
            FileNotFoundError: If section is not found
            ValueError: If section content is invalid
        """
        try:
            # Get section content
            section_content = self.partitioner.get_section(section_id)
            root = ET.fromstring(section_content)
            
            # Extract text content
            content = root.find("content")
            if content is None:
                raise ValueError(f"Section {section_id} missing required 'content' element")
                
            # Collect all text nodes
            text_nodes = []
            for elem in content.iter():
                if elem.text and elem.text.strip():
                    text_nodes.append({
                        "tag": elem.tag,
                        "text": elem.text.strip(),
                        "attributes": elem.attrib
                    })
            
            # Create chunks
            chunks = []
            current_chunk = []
            current_size = 0
            
            for node in text_nodes:
                node_size = len(node["text"])
                
                if current_size + node_size > self.chunk_size and current_chunk:
                    # Save current chunk
                    chunk_id = f"{section_id}_chunk_{len(chunks)}"
                    chunk_path = self.cache_dir / f"{chunk_id}.json"
                    
                    chunk_data = {
                        "id": chunk_id,
                        "section_id": section_id,
                        "nodes": current_chunk,
                        "size": current_size
                    }
                    
                    with open(chunk_path, "w") as f:
                        json.dump(chunk_data, f, indent=2)
                        
                    chunks.append(chunk_data)
                    
                    # Start new chunk with overlap
                    overlap_nodes = current_chunk[-self.overlap:] if self.overlap > 0 else []
                    current_chunk = overlap_nodes
                    current_size = sum(len(n["text"]) for n in overlap_nodes)
                
                current_chunk.append(node)
                current_size += node_size
            
            # Save final chunk if any
            if current_chunk:
                chunk_id = f"{section_id}_chunk_{len(chunks)}"
                chunk_path = self.cache_dir / f"{chunk_id}.json"
                
                chunk_data = {
                    "id": chunk_id,
                    "section_id": section_id,
                    "nodes": current_chunk,
                    "size": current_size
                }
                
                with open(chunk_path, "w") as f:
                    json.dump(chunk_data, f, indent=2)
                    
                chunks.append(chunk_data)
            
            logger.info(f"Created {len(chunks)} chunks for section {section_id}")
            return chunks
            
        except ET.ParseError as e:
            raise ValueError(f"Invalid section content: {str(e)}")
        except IOError as e:
            raise IOError(f"Failed to cache chunks: {str(e)}")
            
    def get_chunk(self, chunk_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific chunk from cache.
        
        Args:
            chunk_id: ID of the chunk to retrieve
            
        Returns:
            Chunk data with nodes and metadata
            
        Raises:
            FileNotFoundError: If chunk is not found in cache
        """
        chunk_path = self.cache_dir / f"{chunk_id}.json"
        if not chunk_path.exists():
            raise FileNotFoundError(f"Chunk {chunk_id} not found in cache")
            
        with open(chunk_path) as f:
            return json.load(f) 