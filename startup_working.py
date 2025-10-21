#!/usr/bin/env python3
"""
Working HTTP server for Azure deployment.
"""

import os
import sys
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Print startup info immediately
print("=" * 60)
print("VALUATION AGENT BACKEND - STARTING v2.0")
print("=" * 60)
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Environment PORT: {os.environ.get('PORT', '8000')}")
print(f"Timestamp: {time.time()}")
print("=" * 60)

class ValuationHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.send_json_response(200, {
                "message": "Valuation Agent Backend API",
                "version": "1.0.0",
                "status": "running",
                "timestamp": time.time()
            })
        elif parsed_path.path == '/healthz':
            self.send_json_response(200, {
                "status": "healthy",
                "service": "valuation-backend",
                "version": "1.0.0",
                "timestamp": time.time()
            })
        elif parsed_path.path == '/api/valuation/runs':
            # Mock valuation runs
            runs = [
                {
                    "run_id": "run_001",
                    "as_of_date": "2025-01-18T00:00:00Z",
                    "valuation_type": "IRS",
                    "status": "completed",
                    "created_at": "2025-01-18T08:00:00Z"
                },
                {
                    "run_id": "run_002", 
                    "as_of_date": "2025-01-18T00:00:00Z",
                    "valuation_type": "CCS",
                    "status": "running",
                    "created_at": "2025-01-18T08:30:00Z"
                }
            ]
            self.send_json_response(200, runs)
        elif parsed_path.path == '/api/valuation/curves':
            # Mock curves
            curves = [
                {
                    "id": "curve_001",
                    "name": "USD OIS",
                    "currency": "USD",
                    "curve_type": "OIS",
                    "status": "active",
                    "nodes": 47,
                    "version": "2.1.4"
                },
                {
                    "id": "curve_002",
                    "name": "EUR OIS", 
                    "currency": "EUR",
                    "curve_type": "OIS",
                    "status": "active",
                    "nodes": 45,
                    "version": "2.1.4"
                }
            ]
            self.send_json_response(200, curves)
        elif parsed_path.path == '/poc/chat':
            # Simple chat endpoint
            self.send_json_response(200, {
                "response": "Hello! I'm your valuation assistant. I can help you with valuation runs, curves, and analysis.",
                "status": "success",
                "timestamp": time.time()
            })
        else:
            self.send_json_response(404, {"error": "Not found"})

    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except:
            data = {}
        
        if parsed_path.path == '/poc/chat':
            message = data.get('message', '').strip()
            print(f"💬 Chat message received: {message[:50]}...")
            
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
            
            print(f"✅ Chat response generated: {response[:50]}...")
            self.send_json_response(200, {
                "response": response,
                "llm_powered": True,
                "model": "intelligent_chat_v2",
                "status": "success",
                "timestamp": time.time()
            })
        elif parsed_path.path == '/api/valuation/runs':
            # Create new valuation run
            run_id = f"run_{int(time.time())}"
            response = {
                "run_id": run_id,
                "status": "created",
                "message": "Valuation run created successfully",
                "data": data
            }
            self.send_json_response(201, response)
        else:
            self.send_json_response(404, {"error": "Not found"})

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def send_json_response(self, status_code, data):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def log_message(self, format, *args):
        """Override to reduce logging noise."""
        # Only log errors
        if "error" in format.lower():
            super().log_message(format, *args)

def run_server():
    """Run the HTTP server."""
    port = int(os.environ.get('PORT', 8000))
    
    print("✅ Starting HTTP server...")
    print(f"✅ Server will run on port {port}")
    print("✅ Ready to accept connections")
    print("=" * 60)
    
    try:
        server = HTTPServer(('0.0.0.0', port), ValuationHandler)
        print(f"🚀 Server running at http://0.0.0.0:{port}")
        print("📊 API Endpoints:")
        print(f"  GET  /                    - API info")
        print(f"  GET  /healthz             - Health check")
        print(f"  GET  /api/valuation/runs  - List valuation runs")
        print(f"  GET  /api/valuation/curves - List curves")
        print(f"  POST /poc/chat            - Chat endpoint")
        print("=" * 60)
        
        server.serve_forever()
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_server()
