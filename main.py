#!/usr/bin/env python3
"""
Main entry point for Azure App Service
"""
import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print(f"🔍 Starting backend service from: {current_dir}")
print(f"🔍 Python path: {sys.path[:3]}")

try:
    # Import and run the simple app
    from simple_app import app
    import uvicorn
    
    print("✅ Successfully imported simple_app")
    print("🚀 Starting FastAPI server...")
    
    # Run the app
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )
    
except Exception as e:
    print(f"❌ Error starting backend: {e}")
    print(f"❌ Error type: {type(e).__name__}")
    import traceback
    print(f"❌ Traceback: {traceback.format_exc()}")
    sys.exit(1)
