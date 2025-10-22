#!/usr/bin/env python3
"""
Main entry point for Azure App Service - Robust Deployment
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print(f"🔍 Starting Azure App Service from: {current_dir}")
print(f"🔍 Python version: {sys.version}")
print(f"🔍 Working directory: {os.getcwd()}")

# Check if we're in the right directory
print(f"🔍 Files in current directory: {list(Path('.').glob('*.py'))}")

# Try the ultra minimal app first (has Groq endpoints)
try:
    print("🔍 Attempting to import app_ultra_minimal...")
    from app_ultra_minimal import app
    print("✅ Ultra minimal app with Groq endpoints imported successfully")
    
    if __name__ == "__main__":
        import uvicorn
        port = int(os.environ.get("PORT", 8000))
        print(f"🚀 Starting ultra-minimal backend with Groq on port {port}")
        print(f"🔍 Groq configuration:")
        print(f"   - USE_GROQ: {os.getenv('USE_GROQ', 'Not set')}")
        print(f"   - GROQ_API_KEY: {'Set' if os.getenv('GROQ_API_KEY') else 'Not set'}")
        print(f"   - GROQ_MODEL: {os.getenv('GROQ_MODEL', 'Not set')}")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
        
except Exception as e:
    print(f"❌ Error importing app_ultra_minimal: {e}")
    print(f"❌ Error type: {type(e).__name__}")
    import traceback
    print(f"❌ Traceback: {traceback.format_exc()}")
    
    # Try simple_app as fallback
    try:
        print("🔍 Attempting to import simple_app...")
        from simple_app import app
        print("✅ Simple app imported successfully")
        
        if __name__ == "__main__":
            import uvicorn
            port = int(os.environ.get("PORT", 8000))
            print(f"🚀 Starting simple backend on port {port}")
            uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
            
    except Exception as e2:
        print(f"❌ Error importing simple_app: {e2}")
        print(f"❌ Error type: {type(e2).__name__}")
        
        # Absolute fallback - create basic app inline with Groq support
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        import aiohttp
        
        app = FastAPI(title="Valuation Backend - Emergency Fallback")
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Groq configuration
        GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        USE_GROQ = os.getenv("USE_GROQ", "false").lower() == "true"
        
        @app.get("/")
        async def root():
            return {
                "message": "Emergency Fallback", 
                "status": "running",
                "groq_configured": bool(GROQ_API_KEY),
                "use_groq": USE_GROQ
            }
        
        @app.get("/healthz")
        async def health():
            return {"status": "healthy"}
        
        @app.get("/api/test/groq-config")
        async def test_groq_config():
            """Test Groq LLM configuration."""
            return {
                "groq_configured": bool(GROQ_API_KEY),
                "groq_base_url": GROQ_BASE_URL,
                "groq_model": GROQ_MODEL,
                "use_groq": USE_GROQ,
                "api_key_present": bool(GROQ_API_KEY),
                "api_key_preview": f"{GROQ_API_KEY[:8]}..." if GROQ_API_KEY else "Not set"
            }
        
        async def call_groq_llm(message: str) -> str:
            """Call Groq LLM API."""
            if not USE_GROQ or not GROQ_API_KEY:
                return None
            
            try:
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a financial valuation expert."},
                        {"role": "user", "content": message}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{GROQ_BASE_URL}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data["choices"][0]["message"]["content"]
                        else:
                            print(f"ERROR: Groq API error: {response.status}")
                            return None
                            
            except Exception as e:
                print(f"ERROR: Groq LLM error: {e}")
                return None
        
        @app.post("/poc/chat")
        async def chat_endpoint(request: dict):
            """AI chat endpoint with Groq LLM integration."""
            message = request.get("message", "").strip()
            print(f"💬 Chat message received: {message[:50]}...")
            
            # Try Groq LLM first
            llm_response = await call_groq_llm(message)
            if llm_response:
                print(f"✅ Groq LLM response generated")
                return {
                    "response": llm_response,
                    "status": "success",
                    "model": GROQ_MODEL,
                    "llm_powered": True
                }
            
            # Fallback responses
            if not message:
                response = "Hello! I'm your valuation assistant. I can help you analyze financial instruments, generate reports, and answer IFRS-13 compliance questions. What would you like to know?"
            elif "hello" in message.lower() or "hi" in message.lower():
                response = "Hello! I'm your AI valuation assistant. I can help you with valuation analysis, risk management, and XVA calculations. What would you like to know?"
            else:
                response = f"I understand you're asking about '{message}'. I'm your AI valuation specialist and I can help you with financial instrument valuations, risk analysis, and XVA calculations. Could you be more specific?"
            
            return {
                "response": response,
                "status": "success",
                "llm_powered": False,
                "fallback_mode": True
            }
        
        if __name__ == "__main__":
            import uvicorn
            port = int(os.environ.get("PORT", 8000))
            print(f"🚀 Starting emergency fallback on port {port}")
            uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")