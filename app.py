import os
from fastapi import FastAPI

# Import generated SDK (placeholder for now)
try:
    from sdk import Client, IRSSpec, CCSSpec, RunRequest, RunStatus, PVBreakdown
    sdk_available = True
except ImportError:
    sdk_available = False

app = FastAPI()

@app.get("/healthz")
def health_check():
    api_base_url = os.getenv("API_BASE_URL", "http://api:9000")
    return {
        "ok": True, 
        "service": "backend", 
        "api_base_url": api_base_url,
        "sdk_available": sdk_available
    }
