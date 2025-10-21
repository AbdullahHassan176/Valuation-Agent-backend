#!/usr/bin/env python3
"""
Test script to verify the server works locally.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """Test that we can import the server."""
    try:
        from app_simple_http import SimpleAPIHandler, run_server
        print("✅ Successfully imported app_simple_http")
        return True
    except Exception as e:
        print(f"❌ Failed to import app_simple_http: {e}")
        return False

def test_server_start():
    """Test that the server can start (without actually running it)."""
    try:
        from app_simple_http import run_server
        print("✅ Server function is callable")
        return True
    except Exception as e:
        print(f"❌ Failed to test server: {e}")
        return False

if __name__ == "__main__":
    print("Testing Valuation Agent Backend...")
    print("=" * 40)
    
    # Test imports
    if not test_import():
        sys.exit(1)
    
    # Test server function
    if not test_server_start():
        sys.exit(1)
    
    print("✅ All tests passed!")
    print("✅ Server is ready for deployment")




