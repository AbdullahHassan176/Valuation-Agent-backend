#!/usr/bin/env python3
"""
Main entry point for Azure App Service - Ultra Minimal Mode
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print(f"🔍 Starting ultra-minimal backend service from: {current_dir}")

# Import and run the simple startup app
try:
    from app_simple_startup import app
    print("✅ Simple startup app imported successfully")
    
    if __name__ == "__main__":
        import uvicorn
        port = int(os.environ.get("PORT", 8000))
        print(f"🚀 Starting ultra-minimal backend on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
        
except Exception as e:
    print(f"❌ Error starting ultra-minimal app: {e}")
    print(f"❌ Error type: {type(e).__name__}")
    
    # Absolute fallback - create basic app inline
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI(title="Valuation Backend - Emergency")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        return {"message": "Emergency Fallback", "status": "running"}
    
    @app.get("/healthz")
    async def health():
        return {"status": "healthy"}
    
    if __name__ == "__main__":
        import uvicorn
        port = int(os.environ.get("PORT", 8000))
        print(f"🚀 Starting emergency fallback on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")