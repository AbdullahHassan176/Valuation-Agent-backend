"""
Simplified FastAPI application for Azure deployment.
This version only includes essential endpoints to avoid import errors.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.settings import get_settings

settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title="Valuation Agent Backend API",
    description="Valuation Agent Backend API",
    version="0.1.0",
    debug=False
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "Valuation Agent Backend API",
        "version": "0.1.0",
        "docs": "/docs"
    }

@app.get("/healthz")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "valuation-backend"}

# Simple chat endpoint for testing
@app.post("/poc/chat")
async def chat_endpoint(request: dict) -> dict:
    """Simple chat endpoint for testing."""
    return {
        "message": "Chat endpoint is working!",
        "request": request
    }

# IFRS ask endpoint
@app.post("/poc/ifrs-ask")
async def ifrs_ask(request: dict) -> dict:
    """IFRS ask endpoint."""
    return {
        "message": "IFRS ask endpoint is working!",
        "request": request
    }

# Parse contract endpoint
@app.post("/poc/parse-contract")
async def parse_contract(request: dict) -> dict:
    """Parse contract endpoint."""
    return {
        "message": "Parse contract endpoint is working!",
        "request": request
    }

# Explain run endpoint
@app.post("/poc/explain-run")
async def explain_run(request: dict) -> dict:
    """Explain run endpoint."""
    return {
        "message": "Explain run endpoint is working!",
        "request": request
    }
