#!/usr/bin/env python3
"""
Azure startup script for the backend API.
"""

import os
import sys
import subprocess

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Install dependencies if missing
def install_dependencies():
    """Install dependencies if they're missing."""
    try:
        import uvicorn
        print("✅ Dependencies already installed")
    except ImportError:
        print("📦 Installing missing dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            sys.exit(1)

# Import and run the FastAPI app
if __name__ == "__main__":
    # Install dependencies first
    install_dependencies()
    
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
