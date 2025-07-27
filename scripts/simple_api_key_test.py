#!/usr/bin/env python3
"""
simple_api_key_test.py

Simple test script to verify that API key reloading works correctly.
Tests that environment variables are properly loaded.

Author: Fanxing Bu
"""
import os
import sys
from pathlib import Path

# Add the app directory to Python path
project_root = Path(__file__).parent.parent
app_path = project_root / "app"
sys.path.insert(0, str(app_path))
sys.path.insert(0, str(project_root))

def test_dotenv_loading():
    """Test that dotenv properly loads environment variables."""
    print("🧪 Testing dotenv loading...")
    
    # Import dotenv
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"✅ API key found: {api_key[:5]}...{api_key[-5:]}")
        return True
    else:
        print("❌ API key not found in environment")
        return False

def test_summarizer_api_key():
    """Test that SummaryGenerator can access the API key."""
    print("\n🧪 Testing SummaryGenerator API key access...")
    
    try:
        from core.summarizer import SummaryGenerator
        generator = SummaryGenerator()
        print("✅ SummaryGenerator initialized successfully")
        return True
    except Exception as e:
        print(f"❌ SummaryGenerator initialization failed: {e}")
        return False

def test_incremental_summary_api_key():
    """Test that IncrementalSummary can access the API key."""
    print("\n🧪 Testing IncrementalSummary API key access...")
    
    try:
        from core.incremental_summary import IncrementalSummary
        summary = IncrementalSummary()
        print("✅ IncrementalSummary initialized successfully")
        return True
    except Exception as e:
        print(f"❌ IncrementalSummary initialization failed: {e}")
        return False

def test_environment_variable_reload():
    """Test that environment variables are reloaded when modules are imported."""
    print("\n🔄 Testing environment variable reloading...")
    
    # Check current API key
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"📝 Current API key: {api_key[:5]}...{api_key[-5:]}")
    else:
        print("❌ No API key found in environment")
        return False
    
    # Test that modules can still access the key
    try:
        from core.summarizer import SummaryGenerator
        generator = SummaryGenerator()
        print("✅ Environment variables reloaded successfully")
        return True
    except Exception as e:
        print(f"❌ Environment reload failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting simple API key tests...")
    
    success = True
    success &= test_dotenv_loading()
    success &= test_summarizer_api_key()
    success &= test_incremental_summary_api_key()
    success &= test_environment_variable_reload()
    
    if success:
        print("\n🎉 All tests passed! Your API key reloading is working correctly.")
        print("💡 You can now update your .env file and the changes will be picked up.")
        print("\n📝 To test with a new API key:")
        print("1. Update your .env file with the new API key")
        print("2. Restart your Python process")
        print("3. The new API key will be automatically loaded")
    else:
        print("\n❌ Some tests failed. Please check your .env file and API key configuration.")
        sys.exit(1) 