#!/usr/bin/env python3
"""
Immediate startup script that writes to file and starts server.
"""

import os
import sys
import time

# Write to a file immediately so Azure can see activity
def write_startup_log():
    """Write startup information to a file."""
    try:
        with open('/tmp/startup.log', 'w') as f:
            f.write("=" * 50 + "\n")
            f.write("VALUATION AGENT BACKEND STARTING\n")
            f.write("=" * 50 + "\n")
            f.write(f"Python version: {sys.version}\n")
            f.write(f"Working directory: {os.getcwd()}\n")
            f.write(f"Environment PORT: {os.environ.get('PORT', '8000')}\n")
            f.write(f"Timestamp: {time.time()}\n")
            f.write("=" * 50 + "\n")
            f.flush()
        print("✅ Startup log written to /tmp/startup.log")
    except Exception as e:
        print(f"⚠️ Could not write startup log: {e}")

# Write startup info immediately
write_startup_log()

# Print to stdout immediately
print("=" * 50)
print("VALUATION AGENT BACKEND STARTING")
print("=" * 50)
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Environment PORT: {os.environ.get('PORT', '8000')}")
print(f"Timestamp: {time.time()}")
print("=" * 50)

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("✅ Python path updated")
print("✅ About to import app_simple_http")

try:
    from app_simple_http import run_server
    print("✅ Successfully imported app_simple_http")
    print("✅ Starting HTTP server...")
    run_server()
except Exception as e:
    print(f"❌ Failed to start server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



