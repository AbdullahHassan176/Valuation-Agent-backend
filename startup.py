#!/usr/bin/env python3
"""
Azure startup script for the backend API.
"""

import os
import sys
import subprocess

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import uvicorn, install dependencies if missing
try:
    import uvicorn
    print("✅ Dependencies already available")
except ImportError:
    print("📦 Installing missing dependencies...")
    try:
        # Try different pip commands
        pip_commands = [
            [sys.executable, "-m", "pip", "install", "-r", "requirements-minimal.txt"],
            ["pip3", "install", "-r", "requirements-minimal.txt"],
            ["pip", "install", "-r", "requirements-minimal.txt"],
        ]
        
        for cmd in pip_commands:
            try:
                print(f"Trying: {' '.join(cmd)}")
                subprocess.check_call(cmd)
                print("✅ Dependencies installed successfully")
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        else:
            print("⚠️ Could not install dependencies, but continuing...")
    except Exception as e:
        print(f"⚠️ Dependency installation failed: {e}, but continuing...")

# Import and run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    from app import app
    
    print("Starting Valuation Agent Backend...")
    
    # Get port from environment variable (Azure sets this)
    port = int(os.environ.get("PORT", 8000))
    
    # Run the FastAPI app
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
