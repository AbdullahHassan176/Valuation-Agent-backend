#!/usr/bin/env python3
"""
Main entry point for Azure App Service - Minimal Mode
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print(f"🔍 Starting minimal backend service from: {current_dir}")
print(f"🔍 Python path: {sys.path[:3]}")

# Use minimal app directly
from app_minimal import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting minimal backend on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")