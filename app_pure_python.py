#!/usr/bin/env python3
"""
Pure Python backend without any external dependencies.
Uses only Python standard library.
"""

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

class ValuationAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                "message": "Valuation Agent Backend API",
                "version": "1.0.0",
                "status": "running"
            }
            self.wfile.write(json.dumps(response).encode())
            
        elif parsed_path.path == '/healthz':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                "status": "healthy",
                "service": "valuation-backend",
                "version": "1.0.0"
            }
            self.wfile.write(json.dumps(response).encode())
            
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {"error": "Not found"}
            self.wfile.write(json.dumps(response).encode())

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
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            message = data.get('message', '')
            response = {
                "response": f"Echo: {message}",
                "status": "success"
            }
            self.wfile.write(json.dumps(response).encode())
            
        elif parsed_path.path == '/poc/ifrs-ask':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                "message": "IFRS ask endpoint is working!",
                "status": "success"
            }
            self.wfile.write(json.dumps(response).encode())
            
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {"error": "Not found"}
            self.wfile.write(json.dumps(response).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run_server():
    """Run the HTTP server."""
    port = int(os.environ.get('PORT', 8000))
    server = HTTPServer(('0.0.0.0', port), ValuationAPIHandler)
    print(f"Starting Valuation Agent Backend on port {port}...")
    print(f"Server running at http://0.0.0.0:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run_server()




