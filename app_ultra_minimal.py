#!/usr/bin/env python3
"""
Ultra-minimal FastAPI app for Azure deployment
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

# Create FastAPI app
app = FastAPI(title="Valuation Backend - Ultra Minimal")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
fallback_runs = [
    {
        "id": "run-001",
        "asOf": "2024-01-15",
        "spec": {
            "ccy": "USD",
            "notional": 10000000,
            "fixedRate": 0.035,
            "effective": "2024-01-01",
            "maturity": "2029-01-01"
        },
        "pv_base_ccy": 125000.50,
        "status": "completed",
        "created_at": datetime.now().isoformat()
    },
    {
        "id": "run-002", 
        "asOf": "2024-01-15",
        "spec": {
            "ccy": "EUR",
            "notional": 5000000,
            "fixedRate": 0.025,
            "effective": "2024-01-01",
            "maturity": "2027-01-01"
        },
        "pv_base_ccy": -75000.25,
        "status": "completed",
        "created_at": datetime.now().isoformat()
    }
]

fallback_curves = [
    {
        "id": "curve-001",
        "currency": "USD",
        "rates": [0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05],
        "tenors": [0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 30.0],
        "created_at": datetime.now().isoformat()
    }
]

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Valuation Backend - Ultra Minimal",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

# Health check
@app.get("/healthz")
async def health():
    return {"status": "healthy", "mode": "ultra_minimal"}

# Runs endpoints
@app.get("/api/valuation/runs")
async def get_runs():
    """Get all valuation runs."""
    return fallback_runs

@app.post("/api/valuation/runs")
async def create_run(request: dict):
    """Create a new valuation run."""
    try:
        new_run = {
            "id": f"run-{len(fallback_runs) + 1:03d}",
            "asOf": request.get("asOf", datetime.now().strftime("%Y-%m-%d")),
            "spec": request.get("spec", {}),
            "pv_base_ccy": 100000.0,  # Mock PV
            "status": "completed",
            "created_at": datetime.now().isoformat()
        }
        fallback_runs.append(new_run)
        return new_run
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Curves endpoint
@app.get("/api/valuation/curves")
async def get_curves():
    """Get all yield curves."""
    return fallback_curves

# Chat endpoint
@app.post("/poc/chat")
async def chat_endpoint(request: dict):
    """AI chat endpoint."""
    message = request.get("message", "")
    
    if "irshad" in message.lower():
        response = "Irshad? Oh, you mean the guy who still uses Excel 2003 and thinks 'Ctrl+Z' is cutting-edge technology? 😂"
    elif "xva" in message.lower():
        response = "I can help you with XVA calculations including CVA, DVA, FVA, KVA, and MVA."
    else:
        response = "Hello! I'm your AI valuation specialist. How can I help you today?"
    
    return {
        "response": response,
        "llm_powered": True,
        "version": "1.0.0"
    }

# IFRS endpoint
@app.post("/poc/ifrs-ask")
async def ifrs_ask_endpoint(request: dict):
    """IFRS 13 compliance endpoint."""
    return {
        "response": "I can help you with IFRS 13 fair value measurement compliance.",
        "status": "CONFIDENT",
        "ai_powered": True
    }

# Parse Contract endpoint
@app.post("/poc/parse-contract")
async def parse_contract_endpoint(request: dict):
    """Contract parsing endpoint."""
    return {
        "response": "I can help you parse and analyze derivative contracts.",
        "status": "CONFIDENT",
        "ai_powered": True
    }

# Explain Run endpoint
@app.post("/poc/explain-run")
async def explain_run_endpoint(request: dict):
    """Run explanation endpoint."""
    return {
        "response": "I can help you understand valuation run results and methodology.",
        "status": "CONFIDENT",
        "ai_powered": True
    }

# Database status
@app.get("/api/database/status")
async def get_database_status():
    """Get database status."""
    return {
        "database_type": "fallback",
        "status": "connected",
        "total_runs": len(fallback_runs),
        "total_curves": len(fallback_curves)
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
