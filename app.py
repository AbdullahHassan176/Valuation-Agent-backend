"""
Ultra-simple FastAPI app for Azure deployment.
No complex imports, just basic functionality.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any

# Create FastAPI application
app = FastAPI(
    title="Valuation Agent Backend",
    description="Simple backend for valuation agent",
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

# Request models
class ChatRequest(BaseModel):
    message: str
    user_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    status: str = "success"

@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Valuation Agent Backend API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/healthz")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "valuation-backend",
        "version": "1.0.0"
    }

@app.post("/poc/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Simple chat endpoint."""
    return ChatResponse(
        response=f"Echo: {request.message}",
        status="success"
    )

@app.post("/poc/ifrs-ask")
async def ifrs_ask(request: Dict[str, Any]) -> Dict[str, str]:
    """IFRS ask endpoint."""
    return {
        "message": "IFRS ask endpoint is working!",
        "status": "success"
    }

@app.post("/poc/parse-contract")
async def parse_contract(request: Dict[str, Any]) -> Dict[str, str]:
    """Parse contract endpoint."""
    return {
        "message": "Parse contract endpoint is working!",
        "status": "success"
    }

@app.post("/poc/explain-run")
async def explain_run(request: Dict[str, Any]) -> Dict[str, str]:
    """Explain run endpoint."""
    return {
        "message": "Explain run endpoint is working!",
        "status": "success"
    }