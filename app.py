import os
from fastapi import FastAPI

app = FastAPI()

@app.get("/healthz")
def health_check():
    api_base_url = os.getenv("API_BASE_URL", "http://api:9000")
    return {"ok": True, "service": "backend", "api_base_url": api_base_url}
