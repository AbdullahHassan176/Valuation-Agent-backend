#!/usr/bin/env python3
"""
Main entry point for Azure App Service - Working HTTP Server Mode
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print(f"🔍 Starting working HTTP server from: {current_dir}")

# Try the full FastAPI app with enhanced report generation first
try:
    from app_ultra_minimal import app
    print("✅ Ultra minimal app with enhanced reports imported successfully")
    
    if __name__ == "__main__":
        import uvicorn
        port = int(os.environ.get("PORT", 8000))
        print(f"🚀 Starting ultra-minimal backend with enhanced reports on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
        
except Exception as e:
    print(f"❌ Error starting ultra-minimal app: {e}")
    print(f"❌ Error type: {type(e).__name__}")
    import traceback
    print(f"❌ Traceback: {traceback.format_exc()}")
    
    # Fallback to working HTTP server with intelligent chat responses
    try:
        from startup_working import ValuationHandler
        from http.server import HTTPServer
        import os
        
        print("✅ Working HTTP server imported successfully")
        
        if __name__ == "__main__":
            port = int(os.environ.get("PORT", 8000))
            print(f"🚀 Starting working HTTP server on port {port}")
            
            server = HTTPServer(('0.0.0.0', port), ValuationHandler)
            print(f"✅ Server started successfully on port {port}")
            server.serve_forever()
            
    except Exception as e2:
        print(f"❌ Error starting ultra-minimal app: {e2}")
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