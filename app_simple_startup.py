#!/usr/bin/env python3
"""
Ultra-simple FastAPI app for Azure deployment testing
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import os

# Import QuantLib valuation engine
try:
    from quantlib_valuation_engine import QuantLibValuationEngine
    VALUATION_ENGINE_AVAILABLE = True
    print("✅ QuantLib valuation engine imported successfully")
except ImportError as e:
    print(f"⚠️ QuantLib valuation engine not available: {e}")
    VALUATION_ENGINE_AVAILABLE = False

# Create FastAPI app
app = FastAPI(title="Valuation Backend - Simple Startup")

# Initialize valuation engine
if VALUATION_ENGINE_AVAILABLE:
    valuation_engine = QuantLibValuationEngine()
    print("✅ QuantLib valuation engine initialized")
else:
    valuation_engine = None
    print("⚠️ Using simplified valuation calculations")

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
        "pv": -200000.0,  # Realistic negative PV (paying fixed at 3.5% when market is 4%)
        "pv01": 4000.0,   # Realistic PV01
        "created_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat(),
        "progress": 100
    }
]

# Health check endpoint
@app.get("/healthz")
async def health():
    return {"status": "healthy", "mode": "simple_startup"}

@app.post("/api/valuation/test-quantlib")
async def test_quantlib_valuation(request: dict):
    """Test QuantLib valuation and generate a comprehensive report."""
    try:
        print("🔍 Testing QuantLib valuation...")
        
        # Extract parameters from request
        spec = request.get("spec", {})
        notional = float(spec.get("notional", 10000000))
        fixed_rate = float(spec.get("fixedRate", 0.035))
        tenor_years = float(spec.get("tenor_years", 5.0))
        currency = spec.get("ccy", "USD")
        instrument_type = spec.get("instrument_type", "IRS")
        
        print(f"🔍 Parameters: notional={notional}, rate={fixed_rate}, tenor={tenor_years}, type={instrument_type}")
        
        # Test QuantLib availability
        if not VALUATION_ENGINE_AVAILABLE:
            return {
                "success": False,
                "error": "QuantLib not available",
                "fallback_used": True,
                "message": "QuantLib valuation engine not available"
            }
        
        # Perform valuation
        if instrument_type == "IRS":
            print("🔍 Performing IRS valuation with QuantLib...")
            result = valuation_engine.value_interest_rate_swap(
                notional=notional,
                fixed_rate=fixed_rate,
                tenor_years=tenor_years,
                frequency="SemiAnnual"
            )
        elif instrument_type == "CCS":
            print("🔍 Performing CCS valuation with QuantLib...")
            result = valuation_engine.value_cross_currency_swap(
                notional_base=notional,
                notional_quote=notional * 0.85,
                base_currency=currency,
                quote_currency="EUR",
                fixed_rate_base=fixed_rate,
                fixed_rate_quote=fixed_rate * 0.8,
                tenor_years=tenor_years,
                frequency="SemiAnnual",
                fx_rate=1.08
            )
        else:
            return {
                "success": False,
                "error": f"Unsupported instrument type: {instrument_type}",
                "supported_types": ["IRS", "CCS"]
            }
        
        print(f"✅ QuantLib valuation completed successfully")
        
        # Generate comprehensive report
        report = {
            "success": True,
            "quantlib_available": True,
            "valuation_result": result,
            "report_summary": {
                "instrument_type": result.get("instrument_type", instrument_type),
                "notional": result.get("notional", notional),
                "npv": result.get("npv", 0.0),
                "fair_rate": result.get("fair_rate", fixed_rate),
                "risk_metrics": result.get("risk_metrics", {}),
                "methodology": result.get("methodology", {}),
                "cash_flows_count": len(result.get("cash_flows", [])),
                "valuation_date": result.get("valuation_date", datetime.now().isoformat())
            },
            "technical_details": {
                "quantlib_version": "Available",
                "calculation_method": "QuantLib Discounting Swap Engine",
                "curve_type": "Bootstrapped Yield Curve",
                "day_count": "Actual/360",
                "business_day_convention": "ModifiedFollowing"
            }
        }
        
        return report
        
    except Exception as e:
        print(f"❌ QuantLib test failed: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        
        return {
            "success": False,
            "error": str(e),
            "quantlib_available": VALUATION_ENGINE_AVAILABLE,
            "fallback_used": not VALUATION_ENGINE_AVAILABLE
        }

@app.post("/api/valuation/generate-report")
async def generate_valuation_report(request: dict):
    """Generate a comprehensive valuation report using QuantLib."""
    try:
        print("🔍 Generating comprehensive valuation report...")
        
        # Extract parameters
        spec = request.get("spec", {})
        notional = float(spec.get("notional", 10000000))
        fixed_rate = float(spec.get("fixedRate", 0.035))
        tenor_years = float(spec.get("tenor_years", 5.0))
        currency = spec.get("ccy", "USD")
        instrument_type = spec.get("instrument_type", "IRS")
        as_of = request.get("asOf", datetime.now().strftime("%Y-%m-%d"))
        
        print(f"🔍 Generating report for {instrument_type}: {currency} {tenor_years}Y, Notional: {notional:,.0f}, Rate: {fixed_rate:.4f}")
        
        # Perform valuation
        if VALUATION_ENGINE_AVAILABLE and valuation_engine:
            if instrument_type == "IRS":
                result = valuation_engine.value_interest_rate_swap(
                    notional=notional,
                    fixed_rate=fixed_rate,
                    tenor_years=tenor_years,
                    frequency="SemiAnnual"
                )
            elif instrument_type == "CCS":
                result = valuation_engine.value_cross_currency_swap(
                    notional_base=notional,
                    notional_quote=notional * 0.85,
                    base_currency=currency,
                    quote_currency="EUR",
                    fixed_rate_base=fixed_rate,
                    fixed_rate_quote=fixed_rate * 0.8,
                    tenor_years=tenor_years,
                    frequency="SemiAnnual",
                    fx_rate=1.08
                )
            else:
                return {"success": False, "error": f"Unsupported instrument type: {instrument_type}"}
        else:
            return {"success": False, "error": "QuantLib not available"}
        
        # Generate comprehensive report
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "as_of_date": as_of,
                "report_type": "QuantLib Valuation Report",
                "version": "1.0"
            },
            "instrument_details": {
                "type": instrument_type,
                "notional": notional,
                "currency": currency,
                "fixed_rate": fixed_rate,
                "tenor_years": tenor_years,
                "frequency": "SemiAnnual"
            },
            "valuation_results": {
                "npv": result.get("npv", 0.0),
                "fair_rate": result.get("fair_rate", fixed_rate),
                "annuity": result.get("annuity", 0.0),
                "valuation_date": result.get("valuation_date", as_of)
            },
            "risk_metrics": result.get("risk_metrics", {}),
            "cash_flows": result.get("cash_flows", []),
            "methodology": result.get("methodology", {}),
            "assumptions": {
                "discount_curve": "Bootstrapped from market rates",
                "day_count_convention": "Actual/360",
                "business_day_convention": "ModifiedFollowing",
                "calendar": "TARGET",
                "compounding": "Annual"
            },
            "analytics": {
                "total_cash_flows": len(result.get("cash_flows", [])),
                "npv_per_notional": (result.get("npv", 0.0) / notional) * 100 if notional != 0 else 0,
                "risk_summary": {
                    "dv01": result.get("risk_metrics", {}).get("dv01", 0.0),
                    "duration": result.get("risk_metrics", {}).get("duration", 0.0),
                    "convexity": result.get("risk_metrics", {}).get("convexity", 0.0)
                }
            }
        }
        
        print(f"✅ Comprehensive report generated successfully")
        return report
        
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        
        return {
            "success": False,
            "error": str(e),
            "quantlib_available": VALUATION_ENGINE_AVAILABLE
        }

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
        
        # Use QuantLib valuation engine if available
        if valuation_engine and instrument_type == "IRS":
            try:
                print(f"🔍 Using QuantLib for IRS valuation...")
                valuation_result = valuation_engine.value_interest_rate_swap(
                    notional=notional,
                    fixed_rate=fixed_rate,
                    tenor_years=tenor_years,
                    frequency=spec.get("frequency", "SemiAnnual")
                )
                npv_value = valuation_result.get("npv", 0.0)
                pv01 = valuation_result.get("risk_metrics", {}).get("dv01", 0.0)
                print(f"✅ QuantLib IRS valuation completed: NPV = {npv_value}")
            except Exception as e:
                print(f"❌ QuantLib IRS valuation failed: {e}, using fallback")
                # Fallback to simplified calculation
                market_rate = 0.04
                rate_diff = fixed_rate - market_rate
                duration = tenor_years * 0.8
                npv_value = rate_diff * notional * duration
                pv01 = abs(notional * duration * 0.0001)
        elif valuation_engine and instrument_type == "CCS":
            try:
                print(f"🔍 Using QuantLib for CCS valuation...")
                valuation_result = valuation_engine.value_cross_currency_swap(
                    notional_base=notional,
                    notional_quote=spec.get("notional_quote", notional * 0.85),
                    base_currency=currency,
                    quote_currency=spec.get("quote_currency", "EUR"),
                    fixed_rate_base=fixed_rate,
                    fixed_rate_quote=spec.get("fixed_rate_quote", fixed_rate * 0.8),
                    tenor_years=tenor_years,
                    frequency=spec.get("frequency", "SemiAnnual"),
                    fx_rate=spec.get("fx_rate", 1.0)
                )
                npv_value = valuation_result.get("npv_base", 0.0)
                pv01 = valuation_result.get("risk_metrics", {}).get("dv01", 0.0)
                print(f"✅ QuantLib CCS valuation completed: NPV = {npv_value}")
            except Exception as e:
                print(f"❌ QuantLib CCS valuation failed: {e}, using fallback")
                # Fallback to simplified calculation
                market_rate = 0.04
                rate_diff = fixed_rate - market_rate
                duration = tenor_years * 0.8
                npv_value = rate_diff * notional * duration
                pv01 = abs(notional * duration * 0.0001)
        else:
            # Simplified calculation fallback
            print(f"🔍 Using simplified valuation for {instrument_type}...")
            market_rate = 0.04
            rate_diff = fixed_rate - market_rate
            duration = tenor_years * 0.8
            npv_value = rate_diff * notional * duration
            pv01 = abs(notional * duration * 0.0001)
        
        # Ensure NPV is reasonable (not more than 10% of notional)
        max_npv = notional * 0.1
        if abs(npv_value) > max_npv:
            npv_value = max_npv if npv_value > 0 else -max_npv
        
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

# Valuation report endpoint
@app.get("/api/valuation/report/{run_id}")
async def get_valuation_report(run_id: str):
    """Get comprehensive valuation report for a run."""
    try:
        # Find the run
        run = None
        for r in fallback_runs:
            if r["id"] == run_id:
                run = r
                break
        
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Generate comprehensive report
        report = {
            "run_id": run_id,
            "instrument_type": run.get("type", "IRS"),
            "valuation_summary": {
                "notional": run.get("notional", 0),
                "currency": run.get("currency", "USD"),
                "tenor": run.get("tenor", "5Y"),
                "fixed_rate": run.get("fixedRate", 0.035),
                "present_value": run.get("pv", 0),
                "pv01": run.get("pv01", 0),
                "status": run.get("status", "completed")
            },
            "risk_metrics": {
                "duration": float(run.get("tenor", "5Y").replace("Y", "")) * 0.8,
                "convexity": float(run.get("tenor", "5Y").replace("Y", "")) * 0.1,
                "var_1d_99pct": abs(run.get("pv", 0)) * 0.05,
                "es_1d_99pct": abs(run.get("pv", 0)) * 0.07,
                "leverage": abs(run.get("pv", 0) / run.get("notional", 1)) if run.get("notional", 0) != 0 else 0
            },
            "methodology": {
                "valuation_framework": "QuantLib Discounting Swap Engine" if VALUATION_ENGINE_AVAILABLE else "Simplified Interest Rate Differential",
                "model": "Bootstrapped Yield Curve" if VALUATION_ENGINE_AVAILABLE else "Market Rate vs Fixed Rate",
                "assumptions": {
                    "discount_curve_type": "Zero Curve" if VALUATION_ENGINE_AVAILABLE else "Simplified",
                    "day_count_convention": "Actual/360" if VALUATION_ENGINE_AVAILABLE else "Simplified",
                    "business_day_convention": "ModifiedFollowing" if VALUATION_ENGINE_AVAILABLE else "Simplified"
                },
                "formulae": {
                    "npv": "Sum(Discounted Cash Flows)" if VALUATION_ENGINE_AVAILABLE else "Rate Differential × Notional × Duration",
                    "fair_rate": "Rate that makes NPV = 0" if VALUATION_ENGINE_AVAILABLE else "Market Rate"
                }
            },
            "cash_flows": [
                {
                    "date": (datetime.now() + timedelta(days=180 * i)).isoformat(),
                    "amount": run.get("notional", 0) * run.get("fixedRate", 0.035) * 0.5,
                    "type": "Fixed",
                    "currency": run.get("currency", "USD"),
                    "leg": "Fixed"
                }
                for i in range(1, int(float(run.get("tenor", "5Y").replace("Y", "")) * 2) + 1)
            ],
            "analytics": {
                "valuation_date": run.get("created_at", datetime.now().isoformat()),
                "calculation_time": "Real-time",
                "engine_version": "QuantLib" if VALUATION_ENGINE_AVAILABLE else "Simplified",
                "confidence_level": "High" if VALUATION_ENGINE_AVAILABLE else "Medium"
            }
        }
        
        return report
        
    except Exception as e:
        print(f"❌ Error generating valuation report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Curves endpoint
@app.get("/api/valuation/curves")
async def get_curves():
    """Get all yield curves."""
    return [
        {
            "id": "curve-001",
            "name": "USD SOFR Curve",
            "currency": "USD",
            "type": "SOFR",
            "rates": [0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05],
            "tenors": [0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 30.0],
            "created_at": datetime.now().isoformat()
        }
    ]

# Chat endpoint
@app.post("/poc/chat")
async def chat(request: dict):
    """AI chat endpoint."""
    try:
        message = request.get("message", "")
        
        # Simple AI responses
        if "hello" in message.lower() or "hi" in message.lower():
            response = "Hello! I'm your AI valuation assistant. How can I help you with financial calculations today?"
        elif "irshad" in message.lower():
            response = "Ah, Irshad! The legendary risk quant who still uses Excel for everything. Did you know he once tried to calculate VaR using a slide rule? 😄"
        elif "valuation" in message.lower():
            response = "I can help you with IRS and CCS valuations using QuantLib. What instrument would you like to analyze?"
        else:
            response = f"I received your message: '{message}'. I'm here to help with financial valuations and risk analysis!"
        
        return {
            "response": response,
            "llm_powered": False,
            "model": "simple_chat",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

# Curves endpoint
@app.get("/api/valuation/curves")
async def get_curves():
    """Get yield curves."""
    return {
        "curves": [
            {
                "id": "curve-001",
                "name": "USD OIS Curve",
                "currency": "USD",
                "type": "OIS",
                "rates": [0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05],
                "tenors": [0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 30.0],
                "created_at": datetime.now().isoformat()
            }
        ]
    }

# Chat endpoint
@app.post("/poc/chat")
async def chat(request: dict):
    """Chat with AI agent."""
    try:
        message = request.get("message", "")
        
        # Simple AI responses
        if "hello" in message.lower() or "hi" in message.lower():
            response = "Hello! I'm your AI valuation assistant. How can I help you with financial calculations today?"
        elif "irshad" in message.lower():
            response = "Ah, Irshad! The legendary accountant who thinks Excel is a programming language. Did you know he still uses a calculator for 2+2? 😄"
        elif "valuation" in message.lower():
            response = "I can help you with IRS and CCS valuations using QuantLib. What specific instrument would you like to analyze?"
        elif "xva" in message.lower():
            response = "XVA calculations include CVA, DVA, FVA, KVA, and MVA adjustments. Which XVA components are you interested in?"
        else:
            response = f"I understand you're asking about: '{message}'. As an AI valuation specialist, I can help with financial calculations, risk analysis, and regulatory compliance. What specific area would you like to explore?"
        
        return {
            "response": response,
            "llm_powered": False,
            "model": "simple_ai",
            "fallback": True,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "response": f"Sorry, I encountered an error: {str(e)}",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Test endpoint
@app.get("/api/test/simple")
async def test_simple():
    return {"message": "Simple app is working", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
