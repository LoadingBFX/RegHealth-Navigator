"""
Document Processors - Abstract Base Classes

This module provides abstract base classes for different types of document
processors (summarizer, FAQ generator, comparison generator) to ensure
consistent interfaces and extensibility.

Author: Fanxing Bu
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DocumentProcessor(ABC):
    """
    Abstract base class for document processors.
    
    This class defines the common interface that all document processors
    must implement, ensuring consistency across different processing types.
    
    Attributes:
        processor_type: Type identifier for the processor
        cache_manager: Cache manager instance for storing results
    """
    
    def __init__(self, processor_type: str):
        """
        Initialize the document processor.
        
        Args:
            processor_type: Type identifier for the processor
        """
        self.processor_type = processor_type
        self.cache_manager = None  # Will be set by subclasses
    
    @abstractmethod
    def process(self, chunks_data: List[Dict], file_name: str, 
                force_regenerate: bool = False, **kwargs) -> str:
        """
        Process document chunks and return results.
        
        Args:
            chunks_data: List of document chunks to process
            file_name: Name of the document file
            force_regenerate: If True, ignore cache and regenerate results
            **kwargs: Additional arguments specific to the processor
            
        Returns:
            Processed result as string
        """
        pass
    
    @abstractmethod
    def get_cached_result(self, file_name: str) -> Optional[str]:
        """
        Retrieve cached result without processing.
        
        Args:
            file_name: Name of the document file
            
        Returns:
            Cached result if available, None otherwise
        """
        pass
    
    @abstractmethod
    def has_cached_result(self, file_name: str) -> bool:
        """
        Check if cached result exists for the given file.
        
        Args:
            file_name: Name of the document file
            
        Returns:
            True if cached result exists and is not expired, False otherwise
        """
        pass
    
    @abstractmethod
    def invalidate_cache(self, file_name: str) -> bool:
        """
        Invalidate cached result for a specific file.
        
        Args:
            file_name: Name of the document file
            
        Returns:
            True if successfully invalidated, False otherwise
        """
        pass
    
    @abstractmethod
    def get_metadata(self, file_name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for cached result.
        
        Args:
            file_name: Name of the document file
            
        Returns:
            Metadata dictionary if available, None otherwise
        """
        pass


class CachedDocumentProcessor(DocumentProcessor):
    """
    Base class for cached document processors.
    
    This class provides common caching functionality that can be inherited
    by specific processor implementations.
    
    Attributes:
        cache_type: Cache type enum value
        default_ttl_hours: Default time-to-live for cached results
    """
    
    def __init__(self, processor_type: str, cache_type, default_ttl_hours: int = 24):
        """
        Initialize the cached document processor.
        
        Args:
            processor_type: Type identifier for the processor
            cache_type: Cache type enum value
            default_ttl_hours: Default time-to-live for cached results in hours
        """
        super().__init__(processor_type)
        self.cache_type = cache_type
        self.default_ttl_hours = default_ttl_hours
    
    def get_cached_result(self, file_name: str) -> Optional[str]:
        """
        Retrieve cached result without processing.
        
        Args:
            file_name: Name of the document file
            
        Returns:
            Cached result if available, None otherwise
        """
        if not self.cache_manager:
            return None
        
        cached_data = self.cache_manager.get_cache(file_name, self.cache_type)
        if cached_data:
            return cached_data.get('result_text')
        return None
    
    def has_cached_result(self, file_name: str) -> bool:
        """
        Check if cached result exists for the given file.
        
        Args:
            file_name: Name of the document file
            
        Returns:
            True if cached result exists and is not expired, False otherwise
        """
        if not self.cache_manager:
            return False
        return self.cache_manager.has_cache(file_name, self.cache_type)
    
    def invalidate_cache(self, file_name: str) -> bool:
        """
        Invalidate cached result for a specific file.
        
        Args:
            file_name: Name of the document file
            
        Returns:
            True if successfully invalidated, False otherwise
        """
        if not self.cache_manager:
            return False
        return self.cache_manager.invalidate_cache(file_name, self.cache_type)
    
    def get_metadata(self, file_name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for cached result.
        
        Args:
            file_name: Name of the document file
            
        Returns:
            Metadata dictionary if available, None otherwise
        """
        if not self.cache_manager:
            return None
        return self.cache_manager.get_cache_metadata(file_name, self.cache_type)
    
    def _cache_result(self, file_name: str, result_text: str, 
                     chunks_count: int, ttl_hours: Optional[int] = None,
                     additional_metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Cache the processing result.
        
        Args:
            file_name: Name of the document file
            result_text: Processed result text
            chunks_count: Number of chunks processed
            ttl_hours: Time-to-live for the cached result
            additional_metadata: Additional metadata to store
            
        Returns:
            True if successfully cached, False otherwise
        """
        if not self.cache_manager:
            return False
        
        cache_content = {
            'result_text': result_text,
            'chunks_count': chunks_count,
            'file_name': file_name,
            'processor_type': self.processor_type
        }
        
        metadata = {
            'generator': self.__class__.__name__,
            'chunks_processed': chunks_count,
            'original_file': file_name,
            'processor_type': self.processor_type
        }
        
        if additional_metadata:
            metadata.update(additional_metadata)
        
        return self.cache_manager.set_cache(
            file_name=file_name,
            cache_type=self.cache_type,
            content=cache_content,
            ttl_hours=ttl_hours or self.default_ttl_hours,
            metadata=metadata
        )


# Placeholder classes for future implementation
class FAQGenerator(CachedDocumentProcessor):
    """
    Abstract FAQ generator class.
    
    This class will be implemented to generate frequently asked questions
    from document content.
    """
    
    def __init__(self, default_ttl_hours: int = 24):
        """
        Initialize the FAQ generator.
        
        Args:
            default_ttl_hours: Default time-to-live for cached FAQs in hours
        """
        from core.cache_manager import CacheType
        super().__init__("faq_generator", CacheType.FAQ, default_ttl_hours)
    
    def process(self, chunks_data: List[Dict], file_name: str, 
                force_regenerate: bool = False, **kwargs) -> str:
        """
        Generate FAQs from document chunks.
        
        Args:
            chunks_data: List of document chunks to process
            file_name: Name of the document file
            force_regenerate: If True, ignore cache and regenerate FAQs
            **kwargs: Additional arguments (e.g., num_questions, question_types)
            
        Returns:
            Generated FAQs as string
        """
        # TODO: Implement FAQ generation logic
        raise NotImplementedError("FAQ generation not yet implemented")


class ComparisonGenerator(CachedDocumentProcessor):
    """
    Abstract comparison generator class.
    
    This class will be implemented to generate comparison analyses
    between different documents or document versions.
    """
    
    def __init__(self, default_ttl_hours: int = 24):
        """
        Initialize the comparison generator.
        
        Args:
            default_ttl_hours: Default time-to-live for cached comparisons in hours
        """
        from core.cache_manager import CacheType
        super().__init__("comparison_generator", CacheType.COMPARISON, default_ttl_hours)
    
    def process(self, chunks_data: List[Dict], file_name: str, 
                force_regenerate: bool = False, **kwargs) -> str:
        """
        Generate comparison analysis from document chunks.
        
        Args:
            chunks_data: List of document chunks to process
            file_name: Name of the document file
            force_regenerate: If True, ignore cache and regenerate comparison
            **kwargs: Additional arguments (e.g., comparison_type, baseline_document)
            
        Returns:
            Generated comparison analysis as string
        """
        # TODO: Implement comparison generation logic
        raise NotImplementedError("Comparison generation not yet implemented")


# Factory function for creating processors
def create_processor(processor_type: str, **kwargs) -> DocumentProcessor:
    """
    Factory function to create document processors.
    
    Args:
        processor_type: Type of processor to create ('summary', 'faq', 'comparison')
        **kwargs: Additional arguments for processor initialization
        
    Returns:
        DocumentProcessor instance
        
    Raises:
        ValueError: If processor_type is not supported
    """
    if processor_type == 'summary':
        from core.cached_summarizer import CachedSummarizer
        return CachedSummarizer(**kwargs)
    elif processor_type == 'faq':
        return FAQGenerator(**kwargs)
    elif processor_type == 'comparison':
        return ComparisonGenerator(**kwargs)
    else:
        raise ValueError(f"Unsupported processor type: {processor_type}")


# Utility function to get all available processor types
def get_available_processors() -> List[str]:
    """
    Get list of available processor types.
    
    Returns:
        List of available processor type names
    """
    return ['summary', 'faq', 'comparison'] 