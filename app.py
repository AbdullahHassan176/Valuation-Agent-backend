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
        print("=" * 60)
        
        server.serve_forever()
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_server()