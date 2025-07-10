"""
Preprocessing Package

This package contains all document preprocessing functionality including:
- XML chunking and processing
- FAISS index building and management  
- Incremental updates and CRUD operations
- Pipeline orchestration for automated workflows

The package is organized into modular components for better maintainability
and testing capabilities.
"""

from .xml_chunker import XMLChunker
from .faiss_builder import FAISSBuilder
from .incremental_manager import IncrementalManager
from .pipeline import ProcessingPipeline, AutoUpdatePipeline

__all__ = [
    'XMLChunker',
    'FAISSBuilder', 
    'IncrementalManager',
    'ProcessingPipeline',
    'AutoUpdatePipeline'
]