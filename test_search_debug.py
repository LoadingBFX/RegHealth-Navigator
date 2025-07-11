#!/usr/bin/env python3
"""
Debug script for search.py issues
Author: Fanxing Bu
"""

import os
import sys
import traceback

# Set environment variable
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

def test_openai_client():
    """Test OpenAI client initialization"""
    print("Testing OpenAI client initialization...")
    try:
        import openai
        print(f"OpenAI version: {openai.__version__}")
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY not set")
            return False
            
        print("✅ OPENAI_API_KEY is set")
        
        # Test client creation
        client = openai.OpenAI(api_key=api_key)
        print("✅ OpenAI client created successfully")
        
        # Test embeddings
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input="test"
        )
        print("✅ Embeddings API call successful")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI client error: {e}")
        traceback.print_exc()
        return False

def test_faiss_files():
    """Test FAISS files existence and loading"""
    print("\nTesting FAISS files...")
    try:
        import faiss
        import json
        
        # Check files exist
        faiss_path = "./rag_data/faiss.index"
        metadata_path = "./rag_data/faiss_metadata.json"
        
        if not os.path.exists(faiss_path):
            print(f"❌ FAISS index file not found: {faiss_path}")
            return False
        print(f"✅ FAISS index file exists: {faiss_path}")
        
        if not os.path.exists(metadata_path):
            print(f"❌ Metadata file not found: {metadata_path}")
            return False
        print(f"✅ Metadata file exists: {metadata_path}")
        
        # Test loading FAISS index
        faiss_index = faiss.read_index(faiss_path)
        print(f"✅ FAISS index loaded with {faiss_index.ntotal} vectors")
        
        # Test loading metadata
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        print(f"✅ Metadata loaded with {len(metadata)} chunks")
        
        return True
        
    except Exception as e:
        print(f"❌ FAISS files error: {e}")
        traceback.print_exc()
        return False

def test_search_service():
    """Test ChatSearchService initialization"""
    print("\nTesting ChatSearchService...")
    try:
        # Import the service
        sys.path.append('./app/core')
        from search import ChatSearchService
        
        api_key = os.getenv("OPENAI_API_KEY")
        service = ChatSearchService(
            openai_api_key=api_key,
            faiss_index_path="./rag_data/faiss.index",
            metadata_path="./rag_data/faiss_metadata.json"
        )
        print("✅ ChatSearchService initialized successfully")
        
        # Test search
        results = service.search("test query", top_k=5)
        print(f"✅ Search successful, returned {len(results)} results")
        
        return True
        
    except Exception as e:
        print(f"❌ ChatSearchService error: {e}")
        traceback.print_exc()
        return False

def test_ask_query():
    """Test the ask_query function"""
    print("\nTesting ask_query function...")
    try:
        # Import the function
        sys.path.append('./app/core')
        from search import ask_query
        
        result = ask_query("How are PE RVUs established for specific services?")
        print("✅ ask_query function executed successfully")
        
        if result is None:
            print("❌ ask_query returned None")
            return False
            
        answer, chunks = result
        print(f"✅ Got answer and {len(chunks)} chunks")
        print(f"Answer preview: {answer[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ ask_query error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Debugging search.py issues...")
    print("=" * 60)
    
    # Run tests in order
    tests = [
        test_openai_client,
        test_faiss_files,
        test_search_service,
        test_ask_query
    ]
    
    for test in tests:
        success = test()
        if not success:
            print(f"\n❌ Test failed: {test.__name__}")
            break
        print(f"\n✅ Test passed: {test.__name__}")
    
    print("\n" + "=" * 60)
    print("Debug complete!") 