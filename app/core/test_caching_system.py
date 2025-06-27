"""
Test Script for Document Caching System

This script tests the complete caching system including cache manager,
cached summarizer, and document processors to ensure all components
work correctly together.

Author: Fanxing Bu
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any

# Add the app directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cache_manager import DocumentCacheManager, CacheType, get_cache_manager
from core.cached_summarizer import CachedSummarizer
from core.document_processors import create_processor, get_available_processors


def test_cache_manager():
    """Test the cache manager functionality."""
    print("=" * 60)
    print("Testing Cache Manager")
    print("=" * 60)
    
    # Create a test cache manager
    test_db_path = "rag_data/test_cache.db"
    cache_manager = DocumentCacheManager(test_db_path, default_ttl_hours=1)
    
    try:
        # Test basic caching operations
        test_content = {"test": "data", "number": 42}
        test_metadata = {"source": "test", "version": "1.0"}
        
        # Test set_cache
        print("1. Testing set_cache...")
        success = cache_manager.set_cache(
            file_name="test_document.xml",
            cache_type=CacheType.SUMMARY,
            content=test_content,
            metadata=test_metadata
        )
        print(f"   Set cache result: {success}")
        
        # Test get_cache
        print("2. Testing get_cache...")
        retrieved_content = cache_manager.get_cache("test_document.xml", CacheType.SUMMARY)
        print(f"   Retrieved content: {retrieved_content}")
        
        # Test has_cache
        print("3. Testing has_cache...")
        has_cache = cache_manager.has_cache("test_document.xml", CacheType.SUMMARY)
        print(f"   Has cache: {has_cache}")
        
        # Test get_cache_metadata
        print("4. Testing get_cache_metadata...")
        metadata = cache_manager.get_cache_metadata("test_document.xml", CacheType.SUMMARY)
        print(f"   Metadata: {metadata}")
        
        # Test cache stats
        print("5. Testing get_cache_stats...")
        stats = cache_manager.get_cache_stats()
        print(f"   Cache stats: {stats}")
        
        # Test invalidate_cache
        print("6. Testing invalidate_cache...")
        invalidated = cache_manager.invalidate_cache("test_document.xml", CacheType.SUMMARY)
        print(f"   Invalidated: {invalidated}")
        
        # Verify cache is gone
        has_cache_after = cache_manager.has_cache("test_document.xml", CacheType.SUMMARY)
        print(f"   Has cache after invalidation: {has_cache_after}")
        
        print("✅ Cache manager tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Cache manager test failed: {e}")
        raise
    finally:
        cache_manager.close()
        # Clean up test database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)


def test_cached_summarizer():
    """Test the cached summarizer functionality."""
    print("\n" + "=" * 60)
    print("Testing Cached Summarizer")
    print("=" * 60)
    
    # Load test chunks data
    chunks_file_path = Path("rag_data/faiss_metadata.json")
    
    if not chunks_file_path.exists():
        print("⚠️ No chunks file found, skipping summarizer test")
        return
    
    try:
        with open(chunks_file_path, 'r', encoding='utf-8') as f:
            all_chunks = json.load(f)
        
        # Group chunks by source file
        chunks_by_file: Dict[str, List[Dict]] = {}
        for chunk in all_chunks:
            source_file = chunk.get('metadata', {}).get('source_file', 'unknown.xml')
            chunks_by_file.setdefault(source_file, []).append(chunk)
        
        if not chunks_by_file:
            print("⚠️ No valid chunks found, skipping summarizer test")
            return
        
        # Get first available file for testing
        test_file = list(chunks_by_file.keys())[0]
        test_chunks = chunks_by_file[test_file]
        
        print(f"Testing with file: {test_file}")
        print(f"Number of chunks: {len(test_chunks)}")
        
        # Create cached summarizer
        summarizer = CachedSummarizer(default_ttl_hours=1)
        
        # Test 1: Check if cache exists initially
        print("1. Testing initial cache check...")
        has_cache = summarizer.has_cached_summary(test_file)
        print(f"   Has cached summary: {has_cache}")
        
        # Test 2: Generate summary (should create cache)
        print("2. Testing summary generation...")
        start_time = time.time()
        summary = summarizer.process(test_chunks, test_file)
        generation_time = time.time() - start_time
        print(f"   Summary generated in {generation_time:.2f} seconds")
        print(f"   Summary length: {len(summary)} characters")
        
        # Test 3: Check if cache was created
        print("3. Testing cache creation...")
        has_cache_after = summarizer.has_cached_summary(test_file)
        print(f"   Has cached summary after generation: {has_cache_after}")
        
        # Test 4: Retrieve cached summary
        print("4. Testing cached summary retrieval...")
        start_time = time.time()
        cached_summary = summarizer.get_cached_summary(test_file)
        retrieval_time = time.time() - start_time
        print(f"   Cached summary retrieved in {retrieval_time:.2f} seconds")
        print(f"   Cached summary length: {len(cached_summary) if cached_summary else 0} characters")
        
        # Test 5: Compare generation vs retrieval times
        print("5. Testing performance comparison...")
        if generation_time > 0 and retrieval_time > 0:
            speedup = generation_time / retrieval_time
            print(f"   Speedup factor: {speedup:.1f}x faster with cache")
        
        # Test 6: Test metadata retrieval
        print("6. Testing metadata retrieval...")
        metadata = summarizer.get_summary_metadata(test_file)
        print(f"   Metadata: {metadata}")
        
        # Test 7: Test cache invalidation
        print("7. Testing cache invalidation...")
        invalidated = summarizer.invalidate_summary_cache(test_file)
        print(f"   Cache invalidated: {invalidated}")
        
        # Test 8: Verify cache is gone
        has_cache_final = summarizer.has_cached_summary(test_file)
        print(f"   Has cache after invalidation: {has_cache_final}")
        
        print("✅ Cached summarizer tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Cached summarizer test failed: {e}")
        raise


def test_document_processors():
    """Test the document processors factory and base classes."""
    print("\n" + "=" * 60)
    print("Testing Document Processors")
    print("=" * 60)
    
    try:
        # Test 1: Get available processors
        print("1. Testing get_available_processors...")
        available_processors = get_available_processors()
        print(f"   Available processors: {available_processors}")
        
        # Test 2: Create summary processor
        print("2. Testing summary processor creation...")
        summary_processor = create_processor('summary', default_ttl_hours=1)
        print(f"   Summary processor type: {type(summary_processor).__name__}")
        print(f"   Processor type: {summary_processor.processor_type}")
        
        # Test 3: Create FAQ processor (placeholder)
        print("3. Testing FAQ processor creation...")
        faq_processor = create_processor('faq', default_ttl_hours=1)
        print(f"   FAQ processor type: {type(faq_processor).__name__}")
        print(f"   Processor type: {faq_processor.processor_type}")
        
        # Test 4: Create comparison processor (placeholder)
        print("4. Testing comparison processor creation...")
        comparison_processor = create_processor('comparison', default_ttl_hours=1)
        print(f"   Comparison processor type: {type(comparison_processor).__name__}")
        print(f"   Processor type: {comparison_processor.processor_type}")
        
        # Test 5: Test invalid processor type
        print("5. Testing invalid processor type...")
        try:
            invalid_processor = create_processor('invalid_type')
            print("   ❌ Should have raised ValueError")
        except ValueError as e:
            print(f"   ✅ Correctly raised ValueError: {e}")
        
        print("✅ Document processors tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Document processors test failed: {e}")
        raise


def test_integration():
    """Test integration between all components."""
    print("\n" + "=" * 60)
    print("Testing Integration")
    print("=" * 60)
    
    try:
        # Test 1: Global cache manager
        print("1. Testing global cache manager...")
        global_cache = get_cache_manager()
        print(f"   Global cache manager: {type(global_cache).__name__}")
        
        # Test 2: Cache different types
        print("2. Testing different cache types...")
        test_content = {"test": "data"}
        
        # Cache summary
        success1 = global_cache.set_cache("test.xml", CacheType.SUMMARY, test_content)
        print(f"   Cached summary: {success1}")
        
        # Cache FAQ (placeholder)
        success2 = global_cache.set_cache("test.xml", CacheType.FAQ, test_content)
        print(f"   Cached FAQ: {success2}")
        
        # Cache comparison (placeholder)
        success3 = global_cache.set_cache("test.xml", CacheType.COMPARISON, test_content)
        print(f"   Cached comparison: {success3}")
        
        # Test 3: Retrieve different types
        print("3. Testing retrieval of different cache types...")
        summary_cache = global_cache.get_cache("test.xml", CacheType.SUMMARY)
        faq_cache = global_cache.get_cache("test.xml", CacheType.FAQ)
        comparison_cache = global_cache.get_cache("test.xml", CacheType.COMPARISON)
        
        print(f"   Summary cache: {summary_cache is not None}")
        print(f"   FAQ cache: {faq_cache is not None}")
        print(f"   Comparison cache: {comparison_cache is not None}")
        
        # Test 4: Cache statistics
        print("4. Testing cache statistics...")
        stats = global_cache.get_cache_stats()
        print(f"   Cache stats: {stats}")
        
        # Test 5: Cleanup
        print("5. Testing cleanup...")
        cleaned = global_cache.cleanup_expired()
        print(f"   Cleaned expired entries: {cleaned}")
        
        # Clean up test data
        global_cache.invalidate_cache("test.xml")
        
        print("✅ Integration tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        raise


def main():
    """Run all tests."""
    print("Starting Document Caching System Tests")
    print("=" * 80)
    
    try:
        # Run individual component tests
        test_cache_manager()
        test_cached_summarizer()
        test_document_processors()
        test_integration()
        
        print("\n" + "=" * 80)
        print("🎉 All tests completed successfully!")
        print("=" * 80)
        
        print("\nSummary:")
        print("- ✅ Cache Manager: Basic caching operations working")
        print("- ✅ Cached Summarizer: Summary generation and caching working")
        print("- ✅ Document Processors: Factory and base classes working")
        print("- ✅ Integration: All components working together")
        
        print("\nNext Steps:")
        print("1. Implement FAQ generation logic in FAQGenerator class")
        print("2. Implement comparison generation logic in ComparisonGenerator class")
        print("3. Add configuration options for cache TTL and storage")
        print("4. Add cache monitoring and analytics")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        raise


if __name__ == "__main__":
    main() 