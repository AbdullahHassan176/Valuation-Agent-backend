#!/usr/bin/env python3
"""
Backend startup script for Azure deployment.
This ensures the backend runs from the correct directory.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the backend server."""
    # Get the directory where this script is located
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Set environment variables for Azure
    os.environ.setdefault('PORT', '8000')
    os.environ.setdefault('HOST', '0.0.0.0')
    
    # Start the server
    cmd = [
        sys.executable, '-m', 'uvicorn', 
        'app.main:app', 
        '--host', '0.0.0.0',
        '--port', os.environ.get('PORT', '8000'),
        '--workers', '1'  # Single worker for Azure
    ]
    
    print(f"Starting backend from: {backend_dir}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("Backend stopped by user")
    except Exception as e:
        print(f"Error starting backend: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()