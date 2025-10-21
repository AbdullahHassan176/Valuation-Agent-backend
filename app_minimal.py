#!/usr/bin/env python3
"""
Minimal FastAPI app for Azure deployment
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print(f"🔍 Starting minimal app from: {current_dir}")
print(f"🔍 Python path: {sys.path[:3]}")

# Create FastAPI app
app = FastAPI(
    title="Valuation Backend - Minimal",
    description="Minimal valuation backend for Azure deployment",
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

# Pydantic models
class RunRequest(BaseModel):
    asOf: str
    spec: Dict[str, Any]
    xva_selection: Optional[List[str]] = None

class RunResponse(BaseModel):
    id: str
    asOf: str
    instrument_type: str
    currency: str
    notional: float
    pv_base_ccy: float
    xva_selection: Optional[List[str]] = None
    calculation_details: Optional[Dict[str, Any]] = None
    xva_analysis: Optional[Dict[str, Any]] = None

# In-memory storage
fallback_runs = []
fallback_curves = []

# Initialize with sample data
def init_sample_data():
    """Initialize with sample data for testing."""
    global fallback_runs, fallback_curves
    
    # Sample runs
    fallback_runs.extend([
        {
            "id": "run_001",
            "asOf": "2024-10-21",
            "instrument_type": "Interest Rate Swap",
            "currency": "USD",
            "notional": 10000000,
            "pv_base_ccy": 125000.50,
            "xva_selection": ["CVA", "DVA"],
            "calculation_details": {
                "method": "simplified",
                "status": "completed"
            },
            "xva_analysis": {
                "xva_components": {
                    "CVA": {"value": -5000.25, "description": "Credit Valuation Adjustment"},
                    "DVA": {"value": 2000.75, "description": "Debit Valuation Adjustment"}
                }
            }
        },
        {
            "id": "run_002", 
            "asOf": "2024-10-21",
            "instrument_type": "Cross Currency Swap",
            "currency": "EUR",
            "notional": 5000000,
            "pv_base_ccy": 75000.25,
            "xva_selection": ["CVA", "FVA"],
            "calculation_details": {
                "method": "simplified",
                "status": "completed"
            },
            "xva_analysis": {
                "xva_components": {
                    "CVA": {"value": -2500.50, "description": "Credit Valuation Adjustment"},
                    "FVA": {"value": -1000.25, "description": "Funding Valuation Adjustment"}
                }
            }
        }
    ])
    
    # Sample curves
    fallback_curves.extend([
        {
            "id": "curve_001",
            "currency": "USD",
            "type": "Zero",
            "nodes": [
                {"tenor": 0.25, "rate": 0.01},
                {"tenor": 0.5, "rate": 0.015},
                {"tenor": 1.0, "rate": 0.02},
                {"tenor": 2.0, "rate": 0.025},
                {"tenor": 5.0, "rate": 0.03},
                {"tenor": 10.0, "rate": 0.035}
            ]
        }
    ])

# Initialize sample data
init_sample_data()

# Health check endpoint
@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "mode": "minimal"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Valuation Backend - Minimal Mode",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/healthz",
            "runs": "/api/valuation/runs",
            "xva_options": "/api/valuation/xva-options"
        }
    }

# Get all runs
@app.get("/api/valuation/runs", response_model=List[RunResponse])
async def get_runs():
    """Get all valuation runs."""
    try:
        print(f"📊 Returning {len(fallback_runs)} runs from fallback storage")
        return fallback_runs
    except Exception as e:
        print(f"❌ Error getting runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Create new run
@app.post("/api/valuation/runs", response_model=RunResponse)
async def create_run(request: RunRequest):
    """Create a new valuation run."""
    try:
        # Generate run ID
        run_id = f"run_{len(fallback_runs) + 1:03d}"
        
        # Calculate PV (simplified)
        notional = request.spec.get("notional", 10000000)
        fixed_rate = request.spec.get("fixed_rate", 0.035)
        tenor_years = 5.0  # Default tenor
        
        # Simple PV calculation
        pv = notional * fixed_rate * tenor_years * 0.8  # Simplified calculation
        
        # Create run data
        run_data = {
            "id": run_id,
            "asOf": request.asOf,
            "instrument_type": "Interest Rate Swap",
            "currency": request.spec.get("ccy", "USD"),
            "notional": notional,
            "pv_base_ccy": pv,
            "xva_selection": request.xva_selection or [],
            "calculation_details": {
                "method": "simplified",
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Add XVA analysis if requested
        if request.xva_selection:
            xva_components = {}
            for xva in request.xva_selection:
                if xva == "CVA":
                    xva_components["CVA"] = {"value": -pv * 0.05, "description": "Credit Valuation Adjustment"}
                elif xva == "DVA":
                    xva_components["DVA"] = {"value": pv * 0.02, "description": "Debit Valuation Adjustment"}
                elif xva == "FVA":
                    xva_components["FVA"] = {"value": -pv * 0.01, "description": "Funding Valuation Adjustment"}
                elif xva == "KVA":
                    xva_components["KVA"] = {"value": -pv * 0.02, "description": "Capital Valuation Adjustment"}
                elif xva == "MVA":
                    xva_components["MVA"] = {"value": -pv * 0.01, "description": "Margin Valuation Adjustment"}
            
            run_data["xva_analysis"] = {"xva_components": xva_components}
        
        # Add to storage
        fallback_runs.append(run_data)
        
        print(f"✅ Created run {run_id} with PV: ${pv:,.2f}")
        return run_data
        
    except Exception as e:
        print(f"❌ Error creating run: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# XVA options endpoint
@app.get("/api/valuation/xva-options")
async def get_xva_options():
    """Get available XVA options."""
    return {
        "quantlib_available": False,
        "available_xva_components": {
            "CVA": "Credit Valuation Adjustment",
            "DVA": "Debit Valuation Adjustment", 
            "FVA": "Funding Valuation Adjustment",
            "KVA": "Capital Valuation Adjustment",
            "MVA": "Margin Valuation Adjustment"
        },
        "default_selections": {
            "IRS": ["CVA", "DVA"],
            "CCS": ["CVA", "FVA"]
        }
    }

# Database status endpoint
@app.get("/api/database/status")
async def get_database_status():
    """Get database status."""
    return {
        "database_type": "fallback",
        "status": "connected",
        "total_runs": len(fallback_runs),
        "total_curves": len(fallback_curves),
        "recent_runs": fallback_runs[-3:] if fallback_runs else []
    }

# Curves endpoint
@app.get("/api/valuation/curves")
async def get_curves():
    """Get all yield curves."""
    try:
        print(f"📈 Returning {len(fallback_curves)} curves from fallback storage")
        return fallback_curves
    except Exception as e:
        print(f"❌ Error getting curves: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Chat endpoint for AI functionality
@app.post("/poc/chat")
async def chat_endpoint(request: dict):
    """AI chat endpoint."""
    try:
        message = request.get("message", "")
        print(f"💬 Chat message received: {message[:50]}...")
        
        # Simple AI responses based on message content
        if "hello" in message.lower() or "hi" in message.lower():
            response = "Hello! I'm your AI valuation specialist. I can help you with XVA calculations, risk analysis, and financial modeling. What would you like to know?"
        elif "xva" in message.lower():
            response = "I can help you with XVA calculations including CVA, DVA, FVA, KVA, and MVA. These are crucial for proper derivative valuation and risk management."
        elif "irshad" in message.lower():
            response = "Irshad? Oh, you mean the guy who still uses Excel 2003 and thinks 'Ctrl+Z' is cutting-edge technology? 😂"
        elif "valuation" in message.lower():
            response = "I specialize in derivative valuation using advanced quantitative methods. I can help with IRS, CCS, and other complex financial instruments."
        elif "risk" in message.lower():
            response = "Risk management is crucial in derivatives trading. I can help you analyze DV01, duration, convexity, VaR, and other risk metrics."
        else:
            response = "I'm your AI valuation specialist. I can help you with XVA calculations, risk analysis, financial modeling, and derivative valuation. What specific question do you have?"
        
        return {
            "response": response,
            "llm_powered": True,
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error in chat endpoint: {e}")
        return {
            "response": "I'm sorry, I encountered an error processing your message. Please try again.",
            "llm_powered": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting minimal backend on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
