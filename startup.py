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
    
    # Get port from environment variable (Azure sets this)
    port = int(os.environ.get("PORT", 8000))
    
    # Run the FastAPI app
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
