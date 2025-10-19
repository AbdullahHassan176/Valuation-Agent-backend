#!/usr/bin/env python3
"""
Azure startup script for the backend API.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    from app.main import app
    from app.database import create_tables
    
    # Initialize database tables
    try:
        create_tables()
        print("Database tables initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize database tables: {e}")
    
    # Get port from environment variable (Azure sets this)
    port = int(os.environ.get("PORT", 8000))
    
    # Run the FastAPI app
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
