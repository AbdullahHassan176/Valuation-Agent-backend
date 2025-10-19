#!/usr/bin/env python3
"""
Azure startup script for the backend API.
Uses pure Python without any external dependencies.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the pure Python app
if __name__ == "__main__":
    from app_pure_python import run_server
    
    print("Starting Valuation Agent Backend...")
    print("Using pure Python HTTP server (no external dependencies)")
    
    # Run the pure Python HTTP server
    run_server()
