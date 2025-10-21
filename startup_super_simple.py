#!/usr/bin/env python3
"""
Super simple startup that writes output immediately.
"""

import os
import sys
import time

# Write to multiple files immediately
def write_immediate_output():
    """Write output to multiple locations immediately."""
    timestamp = time.time()
    
    # Write to startup log
    try:
        with open('/tmp/startup.log', 'w') as f:
            f.write(f"STARTUP: {timestamp}\n")
            f.write("STATUS: STARTING\n")
            f.flush()
    except:
        pass
    
    # Write to stdout immediately
    print(f"STARTUP: {timestamp}")
    print("STATUS: STARTING")
    print("PYTHON:", sys.executable)
    print("PORT:", os.environ.get('PORT', '8000'))
    print("DIR:", os.getcwd())
    sys.stdout.flush()

# Write output immediately
write_immediate_output()

# Simple HTTP server
try:
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import json
    
    class SimpleHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {"status": "ok", "message": "Valuation Agent Backend"}
                self.wfile.write(json.dumps(response).encode())
            elif self.path == '/healthz':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {"status": "healthy", "service": "valuation-backend"}
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {"error": "Not found"}
                self.wfile.write(json.dumps(response).encode())
    
    # Start server
    port = int(os.environ.get('PORT', 8000))
    print(f"STARTING SERVER ON PORT {port}")
    sys.stdout.flush()
    
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    print("SERVER STARTED")
    sys.stdout.flush()
    
    server.serve_forever()
    
except Exception as e:
    print(f"ERROR: {e}")
    sys.stdout.flush()
    sys.exit(1)




