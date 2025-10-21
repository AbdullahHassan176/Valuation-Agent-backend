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

# Import and run the QuantLib simple app
try:
    from app_quantlib_simple import app
    print("✅ QuantLib simple app imported successfully")
    
    if __name__ == "__main__":
        import uvicorn
        port = int(os.environ.get("PORT", 8000))
        print(f"🚀 Starting ultra-minimal backend on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
        
except Exception as e:
    print(f"❌ Error starting ultra-minimal app: {e}")
    print(f"❌ Error type: {type(e).__name__}")
    import traceback
    print(f"❌ Traceback: {traceback.format_exc()}")
    
    # Try minimal simple app as fallback
    try:
        print("🔍 Trying minimal simple app as fallback...")
        from app_minimal_simple import app
        print("✅ Minimal simple app imported successfully")
        
        if __name__ == "__main__":
            import uvicorn
            port = int(os.environ.get("PORT", 8000))
            print(f"🚀 Starting minimal simple backend on port {port}")
            uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
            
    except Exception as e2:
        print(f"❌ Error starting minimal simple app: {e2}")
        print(f"❌ Error type: {type(e2).__name__}")
        
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