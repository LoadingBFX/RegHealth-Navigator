"""
Cached Document Summarizer

This module provides a cached version of the document summarizer that integrates
with the cache manager to store and retrieve summary results, improving performance
and reducing API costs.

Author: Fanxing Bu
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Add the app directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.summarizer import generate_report
from core.cache_manager import get_cache_manager, CacheType
from core.document_processors import CachedDocumentProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CachedSummarizer(CachedDocumentProcessor):
    """
    Cached version of the document summarizer.
    
    This class wraps the original summarizer functionality and adds caching
    capabilities to store and retrieve summary results, reducing API calls
    and improving performance for repeated requests.
    
    Attributes:
        cache_manager: Instance of DocumentCacheManager
        default_ttl_hours: Default time-to-live for cached summaries
    """
    
    def __init__(self, default_ttl_hours: int = 24):
        """
        Initialize the cached summarizer.
        
        Args:
            default_ttl_hours: Default time-to-live for cached summaries in hours
        """
        super().__init__("summary_generator", CacheType.SUMMARY, default_ttl_hours)
        self.cache_manager = get_cache_manager()
        logger.info("CachedSummarizer initialized")
    
    def process(self, chunks_data: List[Dict], file_name: str, 
                force_regenerate: bool = False, **kwargs) -> str:
        """
        Process document chunks and generate summary with caching support.
        
        This method first checks if a cached summary exists for the given
        document. If found and not expired, it returns the cached result.
        Otherwise, it generates a new summary using the original summarizer
        and caches the result for future use.
        
        Args:
            chunks_data: List of document chunks to summarize
            file_name: Name of the document file
            force_regenerate: If True, ignore cache and regenerate summary
            **kwargs: Additional arguments (e.g., ttl_hours)
            
        Returns:
            Generated summary text
            
        Example:
            >>> summarizer = CachedSummarizer()
            >>> summary = summarizer.process(chunks, "2024_MPFS_final_2024-25382.xml")
            >>> print(summary)
            "Business Intelligence Report: CY 2024 MPFS Final Rule..."
        """
        return self.generate_cached_summary(chunks_data, file_name, force_regenerate, **kwargs)
    
    def generate_cached_summary(self, chunks_data: List[Dict], file_name: str, 
                               force_regenerate: bool = False, 
                               ttl_hours: Optional[int] = None) -> str:
        """
        Generate a summary with caching support.
        
        This method first checks if a cached summary exists for the given
        document. If found and not expired, it returns the cached result.
        Otherwise, it generates a new summary using the original summarizer
        and caches the result for future use.
        
        Args:
            chunks_data: List of document chunks to summarize
            file_name: Name of the document file
            force_regenerate: If True, ignore cache and regenerate summary
            ttl_hours: Time-to-live for the cached summary (uses default if None)
            
        Returns:
            Generated summary text
        """
        if not chunks_data:
            logger.warning("No chunks data provided for summarization")
            return "No content to summarize."
        
        # Check cache first (unless force_regenerate is True)
        if not force_regenerate:
            cached_summary = self.get_cached_result(file_name)
            if cached_summary:
                logger.info(f"Returning cached summary for {file_name}")
                return cached_summary
        
        # Generate new summary
        logger.info(f"Generating new summary for {file_name}")
        try:
            summary_text = generate_report(chunks_data, file_name)
            
            if summary_text and not summary_text.startswith("Error:"):
                # Cache the successful result
                success = self._cache_result(
                    file_name=file_name,
                    result_text=summary_text,
                    chunks_count=len(chunks_data),
                    ttl_hours=ttl_hours,
                    additional_metadata={'original_file': file_name}
                )
                
                if success:
                    logger.info(f"Successfully cached summary for {file_name}")
                else:
                    logger.warning(f"Failed to cache summary for {file_name}")
                
                return summary_text
            else:
                logger.error(f"Failed to generate summary for {file_name}: {summary_text}")
                return summary_text
                
        except Exception as e:
            logger.error(f"Exception during summary generation for {file_name}: {e}")
            return f"Error generating summary: {str(e)}"
    
    def get_cached_summary(self, file_name: str) -> Optional[str]:
        """
        Retrieve a cached summary without generating a new one.
        
        Args:
            file_name: Name of the document file
            
        Returns:
            Cached summary text if available, None otherwise
        """
        return self.get_cached_result(file_name)
    
    def has_cached_summary(self, file_name: str) -> bool:
        """
        Check if a cached summary exists for the given file.
        
        Args:
            file_name: Name of the document file
            
        Returns:
            True if cached summary exists and is not expired, False otherwise
        """
        return self.has_cached_result(file_name)
    
    def invalidate_summary_cache(self, file_name: str) -> bool:
        """
        Invalidate the cached summary for a specific file.
        
        Args:
            file_name: Name of the document file
            
        Returns:
            True if successfully invalidated, False otherwise
        """
        return self.invalidate_cache(file_name)
    
    def get_summary_metadata(self, file_name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a cached summary.
        
        Args:
            file_name: Name of the document file
            
        Returns:
            Metadata dictionary if available, None otherwise
        """
        return self.get_metadata(file_name)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for summaries.
        
        Returns:
            Dictionary containing cache statistics
        """
        if self.cache_manager:
            return self.cache_manager.get_cache_stats()
        return {}


# Convenience functions for backward compatibility
def generate_cached_report(chunks_data: List[Dict], file_name: str, 
                          force_regenerate: bool = False) -> str:
    """
    Generate a cached report using the default summarizer instance.
    
    This is a convenience function that creates a CachedSummarizer instance
    and calls process on it.
    
    Args:
        chunks_data: List of document chunks to summarize
        file_name: Name of the document file
        force_regenerate: If True, ignore cache and regenerate summary
        
    Returns:
        Generated summary text
    """
    summarizer = CachedSummarizer()
    return summarizer.process(chunks_data, file_name, force_regenerate)


def get_cached_summary(file_name: str) -> Optional[str]:
    """
    Get a cached summary for the given file.
    
    Args:
        file_name: Name of the document file
        
    Returns:
        Cached summary text if available, None otherwise
    """
    summarizer = CachedSummarizer()
    return summarizer.get_cached_summary(file_name)


def has_cached_summary(file_name: str) -> bool:
    """
    Check if a cached summary exists for the given file.
    
    Args:
        file_name: Name of the document file
        
    Returns:
        True if cached summary exists and is not expired, False otherwise
    """
    summarizer = CachedSummarizer()
    return summarizer.has_cached_summary(file_name)


# Main execution block for testing
if __name__ == "__main__":
    import json
    
    # Test the cached summarizer
    CHUNKS_FILE_PATH = Path("rag_data/faiss_metadata.json")
    
    if not CHUNKS_FILE_PATH.exists():
        print(f"❌ Chunks file not found: {CHUNKS_FILE_PATH}")
        exit(1)
    
    try:
        with open(CHUNKS_FILE_PATH, 'r', encoding='utf-8') as f:
            all_loaded_chunks = json.load(f)
        print(f"✅ Successfully loaded {len(all_loaded_chunks)} chunks.")
    except Exception as e:
        print(f"❌ Error loading chunks file: {e}")
        exit(1)
    
    # Group chunks by source file
    chunks_by_source_file: Dict[str, List[Dict]] = {}
    for chunk in all_loaded_chunks:
        source_file = chunk.get('metadata', {}).get('source_file', 'unknown_document.xml')
        chunks_by_source_file.setdefault(source_file, []).append(chunk)
    
    if not chunks_by_source_file:
        print("⚠️ No processable documents found in the chunks file.")
        exit(0)
    
    # Display available documents
    source_files_list = sorted(list(chunks_by_source_file.keys()))
    print("\n--- Available Documents for Cached Summarization ---")
    for i, file_name in enumerate(source_files_list):
        print(f"  [{i + 1}] {file_name}")
    
    # Get user selection
    selected_index = -1
    while selected_index == -1:
        try:
            choice = input(f"\nPlease enter the number of the document to process (1-{len(source_files_list)}): ")
            if 1 <= int(choice) <= len(source_files_list):
                selected_index = int(choice) - 1
            else:
                print(f"❌ Invalid number.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
    
    selected_file = source_files_list[selected_index]
    chunks_for_selected_file = chunks_by_source_file[selected_file]
    
    # Test cached summarizer
    print(f"\n--- Testing Cached Summarizer for: {selected_file} ---")
    
    summarizer = CachedSummarizer()
    
    # Check if cache exists
    if summarizer.has_cached_summary(selected_file):
        print("✅ Cached summary found!")
        cached_summary = summarizer.get_cached_summary(selected_file)
        print(f"Cached summary length: {len(cached_summary) if cached_summary else 0} characters")
        
        # Show metadata
        metadata = summarizer.get_summary_metadata(selected_file)
        if metadata:
            print(f"Cache metadata: {metadata}")
    else:
        print("❌ No cached summary found.")
    
    # Generate summary (will use cache if available)
    print("\n🔄 Generating summary (will use cache if available)...")
    summary_result = summarizer.process(chunks_for_selected_file, selected_file)
    
    print("\n" + "="*80)
    print("SUMMARY RESULT:")
    print("="*80)
    print(summary_result)
    print("="*80)
    
    # Show cache stats
    stats = summarizer.get_cache_stats()
    print(f"\nCache Statistics: {stats}")
    
    print(f"\n✅ Cached summarizer test completed for {selected_file}") 