#!/usr/bin/env python3
"""
Ultra-simple FastAPI app for Azure deployment.
"""

import os
import sys
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Print startup info immediately
print("=" * 60)
print("VALUATION AGENT BACKEND - SIMPLE VERSION")
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
        elif parsed_path.path == '/poc/chat':
            self.send_json_response(200, {
                "response": "Hello! I'm your valuation assistant. I can help you with valuation runs, curves, and analysis.",
                "status": "success",
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
            message = data.get('message', '')
            response = f"Echo: {message}. I'm working and connected to the backend!"
            self.send_json_response(200, {
                "response": response,
                "status": "success",
                "timestamp": time.time()
            })
        elif parsed_path.path == '/poc/chat-gpt':
            message = data.get('message', '')
            model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
            api_key = os.environ.get('OPENAI_API_KEY')

            if not api_key:
                self.send_json_response(500, {
                    "error": "OPENAI_API_KEY not configured in backend",
                    "status": "error"
                })
                return

            try:
                reply = call_openai_chat(message, api_key, model)
                self.send_json_response(200, {
                    "response": reply,
                    "model": model,
                    "status": "success",
                    "timestamp": time.time()
                })
            except Exception as e:
                self.send_json_response(500, {
                    "error": f"OpenAI call failed: {e}",
                    "status": "error"
                })
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
        pass

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
        print(f"  POST /poc/chat            - Mock chat")
        print(f"  POST /poc/chat-gpt        - Real ChatGPT via OpenAI API")
        print("=" * 60)
        
        server.serve_forever()
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_server()

# ---- Helpers ----
def call_openai_chat(message: str, api_key: str, model: str) -> str:
    """Call OpenAI Chat Completions using only stdlib HTTP.

    Returns the assistant's message content, or raises on failure.
    """
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful valuation assistant."},
            {"role": "user", "content": message or "Hello"}
        ],
        "max_tokens": 256,
        "temperature": 0.3,
    }

    req = Request(
        url="https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body)
    except HTTPError as e:
        raise RuntimeError(f"HTTPError {e.code}: {e.read().decode('utf-8', 'ignore')}")
    except URLError as e:
        raise RuntimeError(f"URLError: {e}")

    try:
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        raise RuntimeError(f"Unexpected OpenAI response: {data}")