#!/usr/bin/env python3
"""
Simple test script that just prints and exits.
"""

import sys
import os
import time

print("=" * 50)
print("PYTHON TEST SCRIPT")
print("=" * 50)
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Working directory: {os.getcwd()}")
print(f"Environment PORT: {os.environ.get('PORT', '8000')}")
print(f"Timestamp: {time.time()}")
print("=" * 50)
print("✅ Python is working!")
print("✅ Test completed successfully")
print("=" * 50)

# Exit immediately
sys.exit(0)




