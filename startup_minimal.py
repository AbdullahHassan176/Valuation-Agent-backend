#!/usr/bin/env python3
"""
Minimal startup script that just prints and exits immediately.
"""

import os
import sys
import time

# Print immediately
print("=" * 60)
print("VALUATION AGENT BACKEND - MINIMAL STARTUP")
print("=" * 60)
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Environment PORT: {os.environ.get('PORT', '8000')}")
print(f"Timestamp: {time.time()}")
print("=" * 60)
print("✅ Backend is starting...")
print("✅ This is a minimal test to verify deployment works")
print("=" * 60)

# Exit immediately - this is just a test
print("✅ Minimal startup completed successfully")
print("✅ Backend deployment is working")
print("=" * 60)
sys.exit(0)



