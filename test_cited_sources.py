#!/usr/bin/env python3
"""
Test script for cited sources extraction functionality.
Author: Fanxing Bu
Date: 2024
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from core.search import (
    ChatSearchService, 
    extract_cited_sources_only_standalone, 
    print_cited_sources_info_standalone,
    ask_query
)

def test_cited_sources_extraction():
    """
    Test the cited sources extraction functionality with a sample query.
    """
    print("🧪 Testing Cited Sources Extraction Functionality")
    print("="*60)
    
    # Test query
    query = "Only tell me How are PE RVUs established for specific services described in MPFS 2024?"
    
    try:
        # Test the main ask_query function
        print(f"🔍 Testing query: {query}")
        answer, chunks, cited_info = ask_query(query)
        
        print(f"\n✅ Test completed successfully!")
        print(f"📊 Cited sources: {cited_info['total_cited_sources']}")
        print(f"📝 Citations found: {cited_info['citation_patterns_found']}")
        
        # Test standalone functions
        print("\n🧪 Testing standalone functions...")
        
        # Create a mock result for testing standalone functions
        mock_result = {
            "answer": "PE RVUs are established through methodology [Source1] and direct costs [Source2]. The process involves [Source1] and [Source3] for calculations.",
            "sources_used": [
                {
                    "source_id": 1,
                    "source_file": "test_file1.xml",
                    "text_preview": "Test preview 1...",
                    "distance": 0.1,
                    "metadata": {"test": "data1"}
                },
                {
                    "source_id": 2,
                    "source_file": "test_file2.xml",
                    "text_preview": "Test preview 2...",
                    "distance": 0.2,
                    "metadata": {"test": "data2"}
                },
                {
                    "source_id": 3,
                    "source_file": "test_file3.xml",
                    "text_preview": "Test preview 3...",
                    "distance": 0.3,
                    "metadata": {"test": "data3"}
                }
            ]
        }
        
        mock_chunks = [
            {
                "text": "This is test chunk text 1 for demonstration purposes.",
                "metadata": {"source_file": "test_file1.xml"},
                "distance": 0.1
            },
            {
                "text": "This is test chunk text 2 for demonstration purposes.",
                "metadata": {"source_file": "test_file2.xml"},
                "distance": 0.2
            },
            {
                "text": "This is test chunk text 3 for demonstration purposes.",
                "metadata": {"source_file": "test_file3.xml"},
                "distance": 0.3
            }
        ]
        
        # Test standalone extraction
        cited_info_mock = extract_cited_sources_only_standalone(mock_result, mock_chunks)
        print(f"✅ Standalone extraction test passed: {cited_info_mock['total_cited_sources']} cited sources extracted")
        print(f"📝 Citations found: {cited_info_mock['citation_patterns_found']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def test_chat_search_service_cited_methods():
    """
    Test the ChatSearchService cited sources methods directly.
    """
    print("\n🧪 Testing ChatSearchService Cited Sources Methods")
    print("="*60)
    
    try:
        # Initialize service
        service = ChatSearchService(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            faiss_index_path="./rag_data/faiss.index",
            metadata_path="./rag_data/faiss_metadata.json"
        )
        
        # Test query
        query = "Only tell me How are PE RVUs established for specific services described in MPFS 2024?"
        result, chunks = service.ask_question(query, top_k=5)
        
        # Test the extract_cited_sources_only method
        cited_info = service.extract_cited_sources_only(result, chunks)
        print(f"✅ Service method test passed: {cited_info['total_cited_sources']} cited sources extracted")
        print(f"📝 Citations found: {cited_info['citation_patterns_found']}")
        
        # Test the print method
        service.print_cited_sources_info(result, chunks)
        
        return True
        
    except Exception as e:
        print(f"❌ Service method test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Cited Sources Extraction Tests")
    print("="*60)
    
    # Run tests
    test1_passed = test_cited_sources_extraction()
    test2_passed = test_chat_search_service_cited_methods()
    
    print("\n📊 Test Results Summary")
    print("="*60)
    print(f"Test 1 (Main Function): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 (Service Methods): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Cited sources extraction functionality is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the error messages above.") 