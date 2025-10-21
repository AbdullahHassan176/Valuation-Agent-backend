#!/usr/bin/env python3
"""
Minimal FastAPI backend for Azure App Service - Guaranteed to work
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import json
from datetime import datetime
from typing import List, Dict, Any
import aiohttp

# Create FastAPI app
app = FastAPI(
    title="Valuation Agent Backend",
    description="Backend service for valuation agent",
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

# Fallback in-memory storage
fallback_runs = [
    {
        "id": "sample-run-001",
        "status": "completed",
        "instrument_type": "IRS",
        "currency": "USD",
        "notional_amount": 1000000,
        "as_of_date": "2024-01-15",
        "pv_base_ccy": 25000.50,
        "created_at": "2024-01-15T10:00:00Z"
    }
]

fallback_curves = [
    {
        "id": "USD_OIS_2024-01-15",
        "currency": "USD",
        "type": "OIS",
        "as_of_date": "2024-01-15",
        "nodes": [
            {"tenor": "1M", "rate": 0.045},
            {"tenor": "3M", "rate": 0.047},
            {"tenor": "6M", "rate": 0.049},
            {"tenor": "1Y", "rate": 0.052}
        ],
        "created_at": "2024-01-15T09:00:00Z"
    }
]

@app.get("/")
def root():
    return {
        "message": "Valuation Agent Backend - Minimal Version", 
        "version": "1.0.0", 
        "status": "running",
        "service": "backend"
    }

@app.get("/healthz")
def health():
    return {"ok": True, "service": "backend", "status": "healthy"}

@app.get("/api/valuation/runs")
async def get_runs():
    """Get all valuation runs."""
    return fallback_runs

@app.post("/api/valuation/runs")
async def create_run(request: dict = None):
    """Create a new valuation run."""
    run_id = f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    current_time = datetime.now().isoformat()
    
    # Extract data from request
    instrument_type = "IRS"
    currency = "USD"
    notional_amount = 1000000.0
    as_of_date = datetime.now().strftime('%Y-%m-%d')
    
    if request:
        if "spec" in request:
            spec = request.get("spec", {})
            instrument_type = "IRS"
            if spec.get("notionalCcy2") or spec.get("ccy2"):
                instrument_type = "CCS"
            currency = spec.get("ccy", "USD")
            notional_amount = spec.get("notional", 1000000.0)
            as_of_date = request.get("asOf", datetime.now().strftime('%Y-%m-%d'))
        else:
            instrument_type = request.get("instrument_type", instrument_type)
            currency = request.get("currency", currency)
            notional_amount = request.get("notional_amount", notional_amount)
            as_of_date = request.get("as_of_date", as_of_date)
    
    # Simple PV calculation
    pv_base_ccy = notional_amount * 0.025  # Simple 2.5% of notional
    
    run_data = {
        "id": run_id,
        "status": "completed",
        "instrument_type": instrument_type,
        "currency": currency,
        "notional_amount": notional_amount,
        "as_of_date": as_of_date,
        "pv_base_ccy": round(pv_base_ccy, 2),
        "spec": request.get("spec") if request else None,
        "metadata": {
            "source": "minimal_backend",
            "calculation_method": "simple",
            "created_at": current_time
        },
        "created_at": current_time
    }
    
    fallback_runs.append(run_data)
    
    return {
        "message": "Run created successfully (Minimal Backend)",
        "status": "success",
        "id": run_id,
        "pv_base_ccy": round(pv_base_ccy, 2)
    }

@app.get("/api/valuation/curves")
async def get_curves():
    """Get yield curves."""
    return fallback_curves

@app.get("/poc/chat")
async def chat_get():
    return {
        "message": "Chat endpoint active - MINIMAL VERSION", 
        "status": "ready", 
        "version": "minimal"
    }

@app.post("/poc/chat")
async def chat_post(request: dict = None):
    """Process chat messages with simple responses."""
    if not request or not request.get("message"):
        return {
            "response": "Hello! I'm your minimal valuation assistant. How can I help you today?",
            "status": "success",
            "version": "minimal"
        }
    
    message = request.get("message", "").strip().lower()
    
    # Simple rule-based responses
    if "hello" in message or "hi" in message:
        return {
            "response": "Hello! I'm your minimal valuation assistant. I can help you with basic valuation questions and run analysis.",
            "status": "success",
            "version": "minimal"
        }
    elif "runs" in message or "valuation" in message:
        return {
            "response": f"I can see {len(fallback_runs)} valuation runs in the system. The latest run shows a present value calculation for a financial instrument.",
            "status": "success",
            "version": "minimal"
        }
    elif "curves" in message or "rates" in message:
        return {
            "response": f"There are {len(fallback_curves)} yield curves available. The USD OIS curve shows current market rates.",
            "status": "success",
            "version": "minimal"
        }
    elif "help" in message:
        return {
            "response": "I can help you with: 1) Viewing valuation runs, 2) Checking yield curves, 3) Basic valuation questions. What would you like to know?",
            "status": "success",
            "version": "minimal"
        }
    else:
        return {
            "response": f"I understand you're asking about '{message}'. I'm a minimal assistant, but I can help with basic valuation questions. Try asking about runs, curves, or valuations.",
            "status": "success",
            "version": "minimal"
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

