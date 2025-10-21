#!/usr/bin/env python3
"""
Simple QuantLib valuation app focused on core functionality
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import os
import json
import math

# Try to import QuantLib
try:
    import QuantLib as ql
    QUANTLIB_AVAILABLE = True
    print("✅ QuantLib imported successfully")
except ImportError:
    QUANTLIB_AVAILABLE = False
    print("⚠️ QuantLib not available, using simplified calculations")

# Create FastAPI app
app = FastAPI(title="QuantLib Valuation Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def simple_irs_valuation(notional, fixed_rate, tenor_years, market_rate=0.04):
    """Simple IRS valuation without QuantLib."""
    rate_diff = fixed_rate - market_rate
    duration = tenor_years * 0.8
    npv = rate_diff * notional * duration
    pv01 = abs(notional * duration * 0.0001)
    
    return {
        "npv": npv,
        "fair_rate": market_rate,
        "pv01": pv01,
        "duration": duration,
        "methodology": "Simplified calculation"
    }

def quantlib_irs_valuation(notional, fixed_rate, tenor_years):
    """QuantLib IRS valuation."""
    if not QUANTLIB_AVAILABLE:
        return simple_irs_valuation(notional, fixed_rate, tenor_years)
    
    try:
        # Set evaluation date
        ql.Settings.instance().evaluationDate = ql.Date.todaysDate()
        
        # Create calendar and day count
        calendar = ql.TARGET()
        day_count = ql.Actual360()
        
        # Create dates
        start_date = ql.Date.todaysDate()
        end_date = calendar.advance(start_date, ql.Period(int(tenor_years), ql.Years))
        
        # Create fixed rate leg
        fixed_schedule = ql.Schedule(
            start_date, end_date,
            ql.Period(ql.Semiannual),
            calendar,
            ql.ModifiedFollowing,
            ql.ModifiedFollowing,
            ql.DateGeneration.Forward,
            False
        )
        
        # Create floating rate leg
        floating_schedule = ql.Schedule(
            start_date, end_date,
            ql.Period(ql.Semiannual),
            calendar,
            ql.ModifiedFollowing,
            ql.ModifiedFollowing,
            ql.DateGeneration.Forward,
            False
        )
        
        # Create index (SOFR)
        index = ql.Sofr()
        
        # Create legs
        fixed_leg = ql.FixedRateLeg(fixed_schedule, day_count)
        fixed_leg.withNotionals(notional)
        fixed_leg.withCouponRates(fixed_rate)
        
        floating_leg = ql.IborLeg(floating_schedule, index)
        floating_leg.withNotionals(notional)
        floating_leg.withPaymentDayCounter(day_count)
        floating_leg.withFixingDays(2)
        
        # Create swap
        swap = ql.Swap([fixed_leg, floating_leg])
        
        # Create simple discount curve (flat rate for simplicity)
        rate = 0.04
        curve = ql.FlatForward(start_date, rate, day_count)
        curve_handle = ql.YieldTermStructureHandle(curve)
        
        # Set pricing engine
        swap.setPricingEngine(ql.DiscountingSwapEngine(curve_handle))
        
        # Get results
        npv = swap.NPV()
        fair_rate = swap.fairRate()
        
        # Calculate cash flows
        cash_flows = []
        for i, cf in enumerate(swap.leg(0)):  # Fixed leg
            cash_flows.append({
                "date": ql.Date.to_date(cf.date()).isoformat(),
                "amount": cf.amount(),
                "type": "Fixed"
            })
        
        return {
            "npv": npv,
            "fair_rate": fair_rate,
            "cash_flows": cash_flows,
            "methodology": "QuantLib Discounting Swap Engine"
        }
        
    except Exception as e:
        print(f"❌ QuantLib valuation failed: {e}")
        return simple_irs_valuation(notional, fixed_rate, tenor_years)

@app.get("/")
async def root():
    return {
        "message": "QuantLib Valuation Service",
        "status": "running",
        "quantlib_available": QUANTLIB_AVAILABLE,
        "version": "1.0.0"
    }

@app.get("/healthz")
async def health():
    return {
        "status": "healthy",
        "quantlib_available": QUANTLIB_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/valuation/irs")
async def value_irs(request: dict):
    """Value an Interest Rate Swap."""
    try:
        spec = request.get("spec", {})
        notional = float(spec.get("notional", 10000000))
        fixed_rate = float(spec.get("fixedRate", 0.035))
        tenor_years = float(spec.get("tenor_years", 5.0))
        currency = spec.get("ccy", "USD")
        
        print(f"🔍 Valuing IRS: {currency} {tenor_years}Y, Notional: {notional:,.0f}, Rate: {fixed_rate:.4f}")
        
        # Perform valuation
        if QUANTLIB_AVAILABLE:
            result = quantlib_irs_valuation(notional, fixed_rate, tenor_years)
        else:
            result = simple_irs_valuation(notional, fixed_rate, tenor_years)
        
        # Generate report
        report = {
            "success": True,
            "instrument_type": "Interest Rate Swap",
            "valuation_results": {
                "npv": result["npv"],
                "fair_rate": result["fair_rate"],
                "notional": notional,
                "fixed_rate": fixed_rate,
                "tenor_years": tenor_years,
                "currency": currency
            },
            "methodology": result.get("methodology", "Simplified calculation"),
            "quantlib_used": QUANTLIB_AVAILABLE,
            "cash_flows": result.get("cash_flows", []),
            "valuation_date": datetime.now().isoformat(),
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_type": "IRS Valuation Report",
                "version": "1.0"
            }
        }
        
        print(f"✅ IRS valuation completed: NPV = {result['npv']:,.2f}")
        return report
        
    except Exception as e:
        print(f"❌ IRS valuation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "quantlib_available": QUANTLIB_AVAILABLE
        }

@app.post("/api/valuation/report")
async def generate_report(request: dict):
    """Generate a comprehensive valuation report."""
    try:
        spec = request.get("spec", {})
        notional = float(spec.get("notional", 10000000))
        fixed_rate = float(spec.get("fixedRate", 0.035))
        tenor_years = float(spec.get("tenor_years", 5.0))
        currency = spec.get("ccy", "USD")
        instrument_type = spec.get("instrument_type", "IRS")
        
        print(f"🔍 Generating comprehensive report for {instrument_type}")
        
        # Perform valuation
        if instrument_type == "IRS":
            if QUANTLIB_AVAILABLE:
                result = quantlib_irs_valuation(notional, fixed_rate, tenor_years)
            else:
                result = simple_irs_valuation(notional, fixed_rate, tenor_years)
        else:
            return {"success": False, "error": f"Unsupported instrument type: {instrument_type}"}
        
        # Generate comprehensive report
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_type": "QuantLib Valuation Report",
                "version": "1.0",
                "quantlib_available": QUANTLIB_AVAILABLE
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
                "npv": result["npv"],
                "fair_rate": result["fair_rate"],
                "valuation_date": datetime.now().isoformat()
            },
            "cash_flows": result.get("cash_flows", []),
            "methodology": {
                "calculation_method": result.get("methodology", "Simplified calculation"),
                "quantlib_used": QUANTLIB_AVAILABLE,
                "assumptions": {
                    "discount_curve": "Flat rate curve" if not QUANTLIB_AVAILABLE else "QuantLib curve",
                    "day_count_convention": "Actual/360",
                    "business_day_convention": "ModifiedFollowing"
                }
            },
            "analytics": {
                "total_cash_flows": len(result.get("cash_flows", [])),
                "npv_per_notional": (result["npv"] / notional) * 100 if notional != 0 else 0,
                "rate_difference": fixed_rate - result["fair_rate"]
            }
        }
        
        print(f"✅ Comprehensive report generated successfully")
        return report
        
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "quantlib_available": QUANTLIB_AVAILABLE
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting QuantLib valuation service on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
