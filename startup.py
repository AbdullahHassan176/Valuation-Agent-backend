#!/usr/bin/env python3
"""
Azure startup script for the backend API.
Ultra-simple HTTP server with immediate output.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Print startup messages immediately
print("=" * 50)
print("VALUATION AGENT BACKEND STARTING")
print("=" * 50)
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Environment PORT: {os.environ.get('PORT', '8000')}")
print("=" * 50)

# Import and run the simple HTTP server
if __name__ == "__main__":
    try:
        from app_simple_http import run_server
        print("✅ Imported app_simple_http successfully")
        print("✅ Starting HTTP server...")
        run_server()
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
