#!/usr/bin/env python3
"""
Minimal startup script for Azure App Service
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print(f"🔍 Starting minimal backend service from: {current_dir}")
print(f"🔍 Python path: {sys.path[:3]}")

# Import and run the minimal app
try:
    from app_minimal import app
    print("✅ Minimal app imported successfully")
    
    if __name__ == "__main__":
        import uvicorn
        port = int(os.environ.get("PORT", 8000))
        print(f"🚀 Starting minimal backend on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
        
except Exception as e:
    print(f"❌ Error starting minimal app: {e}")
    print(f"❌ Error type: {type(e).__name__}")
    
    # Create a basic FastAPI app as absolute fallback
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI(title="Valuation Backend - Emergency Fallback")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        return {"message": "Valuation Backend - Emergency Fallback", "status": "running"}
    
    @app.get("/healthz")
    async def health():
        return {"status": "healthy", "mode": "emergency_fallback"}
    
    if __name__ == "__main__":
        import uvicorn
        port = int(os.environ.get("PORT", 8000))
        print(f"🚀 Starting emergency fallback on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")