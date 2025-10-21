#!/usr/bin/env python3
"""
Ultra-simple FastAPI app for Azure deployment.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Create FastAPI application
app = FastAPI(
    title="Valuation Agent Backend",
    description="Simple backend for testing",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Valuation Agent Backend API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "valuation-backend",
        "version": "1.0.0"
    }

@app.post("/poc/chat")
async def chat_endpoint(data: dict):
    """Simple chat endpoint."""
    message = data.get("message", "")
    return {
        "response": f"Echo: {message}",
        "status": "success"
    }

@app.post("/poc/ifrs-ask")
async def ifrs_ask(data: dict):
    """Simple IFRS endpoint."""
    question = data.get("question", "")
    return {
        "message": "IFRS ask endpoint is working!",
        "status": "success"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)




