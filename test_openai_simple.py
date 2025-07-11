#!/usr/bin/env python3
"""
Simple OpenAI client test
Author: Fanxing Bu
"""

import os
import openai

# Clear any potential proxy settings
if 'HTTP_PROXY' in os.environ:
    del os.environ['HTTP_PROXY']
if 'HTTPS_PROXY' in os.environ:
    del os.environ['HTTPS_PROXY']
if 'http_proxy' in os.environ:
    del os.environ['http_proxy']
if 'https_proxy' in os.environ:
    del os.environ['https_proxy']

print("Testing OpenAI client creation...")
print(f"OpenAI version: {openai.__version__}")

try:
    # Method 1: Direct initialization
    api_key = os.getenv("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=api_key)
    print("✅ Method 1: Direct initialization successful")
    
    # Test embeddings
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input="test"
    )
    print("✅ Embeddings API call successful")
    
except Exception as e:
    print(f"❌ Method 1 failed: {e}")
    
    try:
        # Method 2: With explicit parameters
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.openai.com/v1"
        )
        print("✅ Method 2: With base_url successful")
        
    except Exception as e2:
        print(f"❌ Method 2 failed: {e2}")
        
        try:
            # Method 3: Check if it's a version issue
            print("Trying to check OpenAI client source...")
            import inspect
            print(f"OpenAI client init signature: {inspect.signature(openai.OpenAI.__init__)}")
            
        except Exception as e3:
            print(f"❌ Method 3 failed: {e3}") 