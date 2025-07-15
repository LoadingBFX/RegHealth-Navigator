#!/usr/bin/env python3
"""
Test script for chat filter functionality
"""
import requests
import json

def test_documents_endpoint():
    """Test the documents endpoint"""
    print("🔍 Testing /api/documents endpoint...")
    
    try:
        response = requests.get("http://127.0.0.1:8080/api/documents")
        response.raise_for_status()
        
        data = response.json()
        documents = data.get("documents", [])
        
        print(f"✅ Successfully retrieved {len(documents)} documents")
        
        # Show first few documents
        for i, doc in enumerate(documents[:3]):
            print(f"  {i+1}. {doc['name']} ({doc['program']} {doc['year']} {doc['type']})")
        
        return documents
        
    except Exception as e:
        print(f"❌ Error testing documents endpoint: {e}")
        return []

def test_chat_without_filter():
    """Test chat without document filter"""
    print("\n🔍 Testing chat without document filter...")
    
    try:
        response = requests.post(
            "http://127.0.0.1:8080/api/chat",
            json={"query": "What is the conversion factor for 2024?"}
        )
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Chat response: {data['response'][:100]}...")
        
    except Exception as e:
        print(f"❌ Error testing chat without filter: {e}")

def test_chat_with_filter(documents):
    """Test chat with document filter"""
    print("\n🔍 Testing chat with document filter...")
    
    if not documents:
        print("❌ No documents available for filtering")
        return
    
    # Find a 2024 MPFS final document
    target_doc = None
    for doc in documents:
        if doc['year'] == '2024' and doc['program'] == 'MPFS' and doc['type'] == 'final':
            target_doc = doc
            break
    
    if not target_doc:
        print("❌ No 2024 MPFS final document found")
        return
    
    print(f"📄 Using document: {target_doc['name']}")
    
    try:
        response = requests.post(
            "http://127.0.0.1:8080/api/chat",
            json={
                "query": "What is the conversion factor for 2024?",
                "doc_names": [f"{target_doc['name']}.xml"]
            }
        )
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Filtered chat response: {data['response'][:100]}...")
        
    except Exception as e:
        print(f"❌ Error testing chat with filter: {e}")

def test_multiple_documents_filter(documents):
    """Test chat with multiple document filters"""
    print("\n🔍 Testing chat with multiple document filters...")
    
    if len(documents) < 2:
        print("❌ Need at least 2 documents for multiple filter test")
        return
    
    # Select first two documents
    selected_docs = documents[:2]
    doc_names = [f"{doc['name']}.xml" for doc in selected_docs]
    
    print(f"📄 Using documents: {', '.join([doc['name'] for doc in selected_docs])}")
    
    try:
        response = requests.post(
            "http://127.0.0.1:8080/api/chat",
            json={
                "query": "What are the key changes in recent regulations?",
                "doc_names": doc_names
            }
        )
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Multi-document chat response: {data['response'][:100]}...")
        
    except Exception as e:
        print(f"❌ Error testing multi-document chat: {e}")

def main():
    """Main test function"""
    print("🚀 Starting Chat Filter Functionality Tests")
    print("=" * 50)
    
    # Test documents endpoint
    documents = test_documents_endpoint()
    
    # Test chat without filter
    test_chat_without_filter()
    
    # Test chat with single document filter
    test_chat_with_filter(documents)
    
    # Test chat with multiple document filters
    test_multiple_documents_filter(documents)
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")

if __name__ == "__main__":
    main() 