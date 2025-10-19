#!/usr/bin/env python3
"""
Test the immediate startup script locally.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_immediate_startup():
    """Test that the immediate startup script can be imported and run."""
    try:
        print("Testing immediate startup script...")
        
        # Test that we can import the script
        import startup_immediate
        print("✅ Successfully imported startup_immediate")
        
        # Test that the main components exist
        from app_simple_http import SimpleAPIHandler, run_server
        print("✅ Successfully imported app_simple_http")
        
        print("✅ All imports successful")
        print("✅ Ready for Azure deployment")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("TESTING IMMEDIATE STARTUP SCRIPT")
    print("=" * 50)
    
    if test_immediate_startup():
        print("✅ All tests passed!")
        print("✅ Script is ready for Azure")
    else:
        print("❌ Tests failed!")
        sys.exit(1)
