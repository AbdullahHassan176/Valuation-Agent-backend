#!/usr/bin/env python3
"""
Ultra-simple HTTP server for Azure deployment.
Minimal dependencies, maximum compatibility.
"""

import os
import sys
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

class SimpleAPIHandler(BaseHTTPRequestHandler):
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
            self.send_json_response(200, {
                "response": f"Echo: {data.get('message', '')}",
                "status": "success",
                "timestamp": time.time()
            })
        elif parsed_path.path == '/poc/ifrs-ask':
            self.send_json_response(200, {
                "message": "IFRS ask endpoint is working!",
                "status": "success",
                "timestamp": time.time()
            })
        else:
            self.send_json_response(404, {"error": "Not found"})

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def send_json_response(self, status_code, data):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        """Override to reduce logging noise."""
        # Only log errors
        if "error" in format.lower():
            super().log_message(format, *args)

def run_server():
    """Run the HTTP server with timeout handling."""
    port = int(os.environ.get('PORT', 8000))
    
    print(f"Starting Valuation Agent Backend on port {port}...")
    print(f"Server will run at http://0.0.0.0:{port}")
    
    try:
        server = HTTPServer(('0.0.0.0', port), SimpleAPIHandler)
        print("✅ Server started successfully")
        print("✅ Ready to accept connections")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Print startup messages immediately
    print("=" * 50)
    print("VALUATION AGENT BACKEND STARTING")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Environment PORT: {os.environ.get('PORT', '8000')}")
    print("=" * 50)
    
    # Start server
    run_server()




