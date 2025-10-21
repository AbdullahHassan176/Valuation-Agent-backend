#!/usr/bin/env python3
"""
Ultra-simple FastAPI app for Azure deployment testing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

# Create FastAPI app
app = FastAPI(title="Valuation Backend - Simple Startup")

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
        "name": "USD 5Y IRS",
        "type": "IRS",
        "status": "completed",
        "notional": 10000000,
        "currency": "USD",
        "tenor": "5Y",
        "fixedRate": 0.035,
        "floatingIndex": "SOFR",
        "pv": 100000.0,
        "pv01": 1000.0,
        "created_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat(),
        "progress": 100
    }
]

# Health check endpoint
@app.get("/healthz")
async def health():
    return {"status": "healthy", "mode": "simple_startup"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Valuation Backend - Simple Startup",
        "status": "running",
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
    """Create a new valuation run."""
    try:
        spec = request.get("spec", {})
        as_of = request.get("asOf", datetime.now().strftime("%Y-%m-%d"))
        
        # Extract basic parameters
        notional = spec.get("notional", 10000000)
        currency = spec.get("ccy", "USD")
        tenor_years = spec.get("tenor_years", 5.0)
        fixed_rate = spec.get("fixedRate", 0.035)
        instrument_type = spec.get("instrument_type", "IRS")
        
        # Simple NPV calculation (1% of notional)
        npv_value = notional * 0.01
        pv01 = abs(npv_value) * 0.0001
        
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
            "pv_base_ccy": npv_value
        }
        
        # Store in fallback storage
        fallback_runs.append(new_run)
        print(f"✅ Run created successfully: {run_id}")
        
        return new_run
        
    except Exception as e:
        print(f"❌ Error creating run: {e}")
        return {"error": str(e)}

# Test endpoint
@app.get("/api/test/simple")
async def test_simple():
    return {"message": "Simple app is working", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
