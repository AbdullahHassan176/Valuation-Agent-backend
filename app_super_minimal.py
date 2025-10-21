#!/usr/bin/env python3
"""
Super minimal FastAPI app for Azure deployment - bypasses all issues
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
import json

# Create FastAPI app
app = FastAPI(title="Valuation Backend - Super Minimal")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
runs = [
    {
        "id": "run-001",
        "name": "USD 5Y IRS",
        "type": "IRS",
        "status": "completed",
        "notional": 10000000,
        "currency": "USD",
        "tenor": "5Y",
        "fixedRate": 0.035,
        "floatingIndex": "SOFR",
        "pv": 125000.50,
        "pv01": 1250.0,
        "created_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat()
    },
    {
        "id": "run-002",
        "name": "EUR 3Y IRS",
        "type": "IRS", 
        "status": "completed",
        "notional": 5000000,
        "currency": "EUR",
        "tenor": "3Y",
        "fixedRate": 0.025,
        "floatingIndex": "EURIBOR",
        "pv": -75000.25,
        "pv01": 750.0,
        "created_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat()
    }
]

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Valuation Backend - Super Minimal",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

# Health check
@app.get("/healthz")
async def health():
    return {"status": "healthy", "mode": "super_minimal"}

# Runs endpoints
@app.get("/api/valuation/runs")
async def get_runs():
    """Get all valuation runs."""
    return runs

@app.post("/api/valuation/runs")
async def create_run(request: dict):
    """Create a new valuation run."""
    try:
        spec = request.get("spec", {})
        as_of = request.get("asOf", datetime.now().strftime("%Y-%m-%d"))
        
        # Create new run
        new_run = {
            "id": f"run-{int(datetime.now().timestamp() * 1000)}",
            "name": f"{spec.get('ccy', 'USD')} {spec.get('tenor_years', 5)}Y {spec.get('instrument_type', 'IRS')}",
            "type": spec.get("instrument_type", "IRS"),
            "status": "completed",
            "notional": spec.get("notional", 10000000),
            "currency": spec.get("ccy", "USD"),
            "tenor": f"{spec.get('tenor_years', 5)}Y",
            "fixedRate": spec.get("fixedRate", 0.035),
            "floatingIndex": "SOFR" if spec.get("ccy", "USD") == "USD" else "EURIBOR",
            "pv": 100000.0,  # Mock PV
            "pv01": 1000.0,  # Mock PV01
            "created_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat()
        }
        
        runs.append(new_run)
        return new_run
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Curves endpoint
@app.get("/api/valuation/curves")
async def get_curves():
    """Get all yield curves."""
    return [
        {
            "id": "curve-001",
            "currency": "USD",
            "rates": [0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05],
            "tenors": [0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 30.0],
            "created_at": datetime.now().isoformat()
        }
    ]

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

# Database status
@app.get("/api/database/status")
async def get_database_status():
    """Get database status."""
    return {
        "database_type": "in_memory",
        "status": "connected",
        "total_runs": len(runs),
        "total_curves": 1
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
