#!/usr/bin/env python3
"""
Local development script for the backend.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    from app import app
    
    print("Starting Valuation Agent Backend (Local Development)...")
    print("Backend will be available at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    
    # Run the FastAPI app
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=True
    )
