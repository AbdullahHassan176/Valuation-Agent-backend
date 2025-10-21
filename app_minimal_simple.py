#!/usr/bin/env python3
"""
Minimal FastAPI app for Azure deployment - Simple version without complex valuation
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import math

# Create FastAPI app
app = FastAPI(title="Valuation Backend - Minimal Simple")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (fallback) - Format matches frontend interface
fallback_runs = [
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
        "pv": 125000.5,
        "pv01": 2500.0,
        "created_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat(),
        "progress": 100
    },
    {
        "id": "run-002", 
        "name": "EUR 3Y IRS",
        "type": "IRS",
        "status": "completed",
        "notional": 8500000,
        "currency": "EUR",
        "tenor": "3Y",
        "fixedRate": 0.025,
        "floatingIndex": "EURIBOR",
        "pv": 85000.0,
        "pv01": 1700.0,
        "created_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat(),
        "progress": 100
    }
]

# Health check endpoint
@app.get("/healthz")
async def health():
    return {"status": "healthy", "mode": "minimal_simple"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Valuation Backend - Minimal Simple",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

# Get runs endpoint
@app.get("/api/valuation/runs")
async def get_runs():
    """Get all valuation runs."""
    return fallback_runs

# Create run endpoint
@app.post("/api/valuation/runs")
async def create_run(request: dict):
    """Create a new valuation run with simple calculations."""
    try:
        print(f"🔍 Starting run creation with request: {request}")
        spec = request.get("spec", {})
        as_of = request.get("asOf", datetime.now().strftime("%Y-%m-%d"))
        print(f"🔍 Spec: {spec}")
        print(f"🔍 AsOf: {as_of}")
        
        # Extract basic parameters
        notional = spec.get("notional", 10000000)
        currency = spec.get("ccy", "USD")
        tenor_years = spec.get("tenor_years", 5.0)
        fixed_rate = spec.get("fixedRate", 0.035)
        instrument_type = spec.get("instrument_type", "IRS")
        
        # Simple valuation calculation
        print(f"🔍 Using simple valuation for {instrument_type}...")
        market_rate = 0.04  # Assume market rate is 4%
        rate_diff = fixed_rate - market_rate
        duration = tenor_years * 0.8
        npv_value = rate_diff * notional * duration
        
        # Ensure NPV is reasonable (not more than 10% of notional)
        max_npv = notional * 0.1
        if abs(npv_value) > max_npv:
            npv_value = max_npv if npv_value > 0 else -max_npv
        
        # Calculate PV01 (simplified)
        pv01 = abs(notional * duration * 0.0001)
        
        # Create run
        run_id = f"run-{int(datetime.now().timestamp() * 1000)}"
        new_run = {
            "id": run_id,
            "name": f"{currency} {datetime.now().strftime('%Y-%m-%d')} {instrument_type}",
            "type": instrument_type,
            "status": "completed",
            "notional": notional,
            "currency": currency,
            "tenor": f"{tenor_years}Y",
            "fixedRate": fixed_rate,
            "floatingIndex": "SOFR" if currency == "USD" else "EURIBOR",
            "pv": npv_value,
            "pv01": pv01,
            "created_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
            "progress": 100,
            "asOf": as_of,
            "spec": spec,
            "instrument_type": instrument_type,
            "pv_base_ccy": npv_value,
            "valuation_result": {
                "instrument_type": instrument_type,
                "npv": npv_value,
                "npv_base_ccy": npv_value,
                "risk_metrics": {"dv01": pv01},
                "methodology": {"valuation_framework": "Simple Calculation"}
            }
        }
        
        # Store in fallback storage
        fallback_runs.append(new_run)
        print(f"✅ Run created successfully: {run_id}")
        
        return new_run
        
    except Exception as e:
        print(f"❌ Error creating run: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Test endpoint
@app.get("/api/test/simple")
async def test_simple():
    """Test endpoint to verify the app is working."""
    return {
        "status": "working",
        "timestamp": datetime.now().isoformat(),
        "total_runs": len(fallback_runs)
    }
