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
        
        @app.post("/poc/chat")
        async def chat_endpoint(request: dict):
            """Emergency chat endpoint with intelligent responses."""
            message = request.get("message", "").strip()
            print(f"💬 Emergency chat message received: {message[:50]}...")
            
            # Intelligent AI responses
            if not message:
                response = "Hello! I'm your valuation assistant. I can help you analyze financial instruments, generate reports, and answer IFRS-13 compliance questions. What would you like to know?"
            elif "hello" in message.lower() or "hi" in message.lower() or "hey" in message.lower():
                response = "Hello! I'm your AI valuation assistant. I can help you with:\n\n• Analyze and explain valuation runs\n• Generate sensitivity scenarios\n• Export reports and documentation\n• Answer IFRS-13 compliance questions\n\nWhat would you like to know?"
            elif "how are you" in message.lower() or "how are you doing" in message.lower():
                response = "I'm doing great! Ready to help you with financial valuations and risk analysis. I've been busy calculating PV01s and running Monte Carlo simulations. What can I assist you with today?"
            elif "irshad" in message.lower():
                response = "Ah, Irshad! The legendary risk quant who still uses Excel for everything. Did you know he once tried to calculate VaR using a slide rule? 😄 He's probably still debugging that VLOOKUP formula from 2019!"
            elif "valuation" in message.lower() or "value" in message.lower():
                response = "I can help you with derivative valuations using advanced quantitative methods. I specialize in:\n\n• Interest Rate Swaps (IRS)\n• Cross Currency Swaps (CCS)\n• XVA calculations (CVA, DVA, FVA)\n• Risk metrics (PV01, DV01, Duration)\n\nWhat instrument would you like to analyze?"
            elif "xva" in message.lower() or "cva" in message.lower():
                response = "XVA (X-Value Adjustment) is crucial for derivative pricing! I can help with:\n\n• CVA (Credit Valuation Adjustment)\n• DVA (Debit Valuation Adjustment)\n• FVA (Funding Valuation Adjustment)\n• KVA (Capital Valuation Adjustment)\n• MVA (Margin Valuation Adjustment)\n\nWhich XVA component would you like to explore?"
            elif "risk" in message.lower():
                response = "Risk management is essential in derivatives! I can help you analyze:\n\n• Interest Rate Risk (PV01, DV01)\n• Credit Risk (CVA, DVA)\n• Market Risk (VaR, Expected Shortfall)\n• Liquidity Risk (FVA)\n• Operational Risk\n\nWhat risk metric interests you?"
            elif "report" in message.lower():
                response = "I can generate comprehensive reports including:\n\n• Valuation reports with embedded charts\n• CVA analysis with credit risk metrics\n• Portfolio summaries with risk analytics\n• Regulatory compliance documentation\n\nWould you like me to create a report for your runs?"
            elif "help" in message.lower():
                response = "I'm here to help! I can assist you with:\n\n• **Valuation Analysis**: IRS, CCS, and other derivatives\n• **Risk Management**: PV01, VaR, stress testing\n• **XVA Calculations**: CVA, DVA, FVA, KVA, MVA\n• **Report Generation**: Professional HTML/PDF reports\n• **IFRS-13 Compliance**: Fair value measurement\n• **Portfolio Analytics**: Risk metrics and insights\n\nJust ask me anything about financial valuations!"
            elif "thank" in message.lower() or "thanks" in message.lower():
                response = "You're welcome! I'm always here to help with your valuation and risk analysis needs. Feel free to ask me anything about financial instruments or risk management!"
            else:
                response = f"I understand you're asking about '{message}'. I'm your AI valuation specialist and I can help you with:\n\n• Financial instrument valuations\n• Risk analysis and metrics\n• XVA calculations\n• Report generation\n• IFRS-13 compliance\n\nCould you be more specific about what you'd like to know?"
            
            return {
                "response": response,
                "status": "success",
                "emergency_mode": True
            }
        
        if __name__ == "__main__":
            import uvicorn
            port = int(os.environ.get("PORT", 8000))
            print(f"🚀 Starting emergency fallback on port {port}")
            uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")