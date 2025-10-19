#!/usr/bin/env python3
"""
Simple Backend server startup script
"""
import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print(f"Current directory: {current_dir}")
print(f"Python path: {sys.path[:3]}...")

try:
    import simple_app
    print("✅ Simple app imported successfully")
    
    import uvicorn
    print("✅ Uvicorn imported successfully")
    
    print("🚀 Starting Backend server on http://127.0.0.1:8000")
    uvicorn.run(simple_app.app, host="127.0.0.1", port=8000, log_level="info")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

