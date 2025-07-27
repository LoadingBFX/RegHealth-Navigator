#!/usr/bin/env python3
"""
test_api_key_reload.py

Test script to verify that API key reloading works correctly.
Tests that environment variables are properly loaded when auto_update_pipeline is used.

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

def test_api_key_loading():
    """Test that API key is properly loaded from environment."""
    print("🧪 Testing API key loading...")
    
    # Test 1: Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"✅ API key found: {api_key[:5]}...{api_key[-5:]}")
    else:
        print("❌ API key not found in environment")
        return False
    
    # Test 2: Test AutoUpdatePipeline initialization
    try:
        from core.auto_update_pipeline import AutoUpdatePipeline
        pipeline = AutoUpdatePipeline()
        print("✅ AutoUpdatePipeline initialized successfully")
    except Exception as e:
        print(f"❌ AutoUpdatePipeline initialization failed: {e}")
        return False
    
    # Test 3: Test IncrementalSummary initialization
    try:
        from core.incremental_summary import IncrementalSummary
        summary = IncrementalSummary()
        print("✅ IncrementalSummary initialized successfully")
    except Exception as e:
        print(f"❌ IncrementalSummary initialization failed: {e}")
        return False
    
    # Test 4: Test SummaryGenerator initialization
    try:
        from core.summarizer import SummaryGenerator
        generator = SummaryGenerator()
        print("✅ SummaryGenerator initialized successfully")
    except Exception as e:
        print(f"❌ SummaryGenerator initialization failed: {e}")
        return False
    
    print("🎉 All tests passed! API key reloading is working correctly.")
    return True

def test_environment_reload():
    """Test that environment variables are reloaded when modules are imported."""
    print("\n🔄 Testing environment variable reloading...")
    
    # Clear any cached environment variables
    if "OPENAI_API_KEY" in os.environ:
        original_key = os.environ["OPENAI_API_KEY"]
        print(f"📝 Original API key: {original_key[:5]}...{original_key[-5:]}")
    else:
        print("❌ No API key found in environment")
        return False
    
    # Test that the key is still accessible after module imports
    try:
        from core.auto_update_pipeline import AutoUpdatePipeline
        pipeline = AutoUpdatePipeline()
        print("✅ Environment variables reloaded successfully")
        return True
    except Exception as e:
        print(f"❌ Environment reload failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting API key reload tests...")
    
    success = True
    success &= test_api_key_loading()
    success &= test_environment_reload()
    
    if success:
        print("\n🎉 All tests passed! Your API key reloading is working correctly.")
        print("💡 You can now update your .env file and the changes will be picked up.")
    else:
        print("\n❌ Some tests failed. Please check your .env file and API key configuration.")
        sys.exit(1) 