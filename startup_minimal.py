#!/usr/bin/env python3
"""
Minimal startup script for Azure deployment
Focuses on core functionality without heavy dependencies
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from simple_app import app
    print("✅ Simple app imported successfully")
except Exception as e:
    print(f"❌ Error importing simple_app: {e}")
    # Create minimal FastAPI app as fallback
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI(title="Valuation Backend - Minimal Mode")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        return {"message": "Valuation Backend - Minimal Mode", "status": "running"}
    
    @app.get("/healthz")
    async def health():
        return {"status": "healthy", "mode": "minimal"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting minimal backend on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")