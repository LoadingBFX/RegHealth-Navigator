#!/usr/bin/env python3
"""
Minimal OpenAI client test to isolate the issue
Author: Fanxing Bu
"""

import os
import sys
import importlib

# Clear environment variables that might cause issues
env_vars_to_clear = [
    'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
    'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE', 'SSL_CERT_FILE'
]

for var in env_vars_to_clear:
    if var in os.environ:
        print(f"Clearing {var}")
        del os.environ[var]

print("Testing OpenAI client in isolated environment...")

try:
    # Reload openai module to clear any cached configurations
    if 'openai' in sys.modules:
        del sys.modules['openai']
    
    import openai
    print(f"OpenAI version: {openai.__version__}")
    
    # Check if there are any global configurations
    print("Checking for global configurations...")
    
    # Try to create client with minimal parameters
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        sys.exit(1)
    
    print("Creating OpenAI client...")
    client = openai.OpenAI(api_key=api_key)
    print("✅ OpenAI client created successfully!")
    
    # Test a simple API call
    print("Testing embeddings API...")
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input="test"
    )
    print("✅ Embeddings API call successful!")
    print(f"Embedding dimension: {len(response.data[0].embedding)}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    
    # Try to get more information about the error
    print("\nTrying to understand the error better...")
    try:
        import openai._client
        print(f"OpenAI client module: {openai._client}")
        print(f"OpenAI client class: {openai._client.OpenAI}")
    except Exception as e2:
        print(f"Could not inspect OpenAI client: {e2}") 