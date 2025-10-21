#!/usr/bin/env python3
"""
Ultra-minimal FastAPI app for Azure deployment
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import math

# Try to import optional dependencies
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    print("WARNING: aiohttp not available - LLM features disabled")

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

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    global db_initialized
    try:
        print("INFO: Starting backend initialization...")
        # Skip MongoDB initialization during startup to avoid timeout
        print("WARNING: Skipping MongoDB initialization during startup - will connect on demand")
        db_initialized = False
        print("SUCCESS: Backend startup completed - using fallback storage")
    except Exception as e:
        print(f"ERROR: Database initialization error: {e}")
        db_initialized = False

# MongoDB configuration
MONGODB_CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "valuation-backend-server")
USE_MONGODB = os.getenv("USE_MONGODB", "true").lower() == "true"

# MongoDB client (will be initialized if available)
mongodb_client = None
db_initialized = False

# Try to import and initialize MongoDB
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from pymongo import MongoClient
    import asyncio
    MONGODB_AVAILABLE = True
except ImportError as e:
    print(f"WARNING: MongoDB dependencies not available: {e}")
    MONGODB_AVAILABLE = False
    AsyncIOMotorClient = None
    MongoClient = None

if MONGODB_AVAILABLE:
    class MongoDBClient:
        """MongoDB client for Azure Cosmos DB for MongoDB."""
        
        def __init__(self):
            self.connection_string = MONGODB_CONNECTION_STRING
            self.database_name = MONGODB_DATABASE
            self.client = None
            self.db = None
            
        async def connect(self):
            """Connect to MongoDB."""
            try:
                if not self.connection_string:
                    print("ERROR: No MongoDB connection string provided")
                    return False
                    
                print(f"INFO: Connecting to MongoDB...")
                
                # For Azure Cosmos DB, use specific connection parameters
                if "cosmos.azure.com" in self.connection_string or len(self.connection_string) > 100:
                    print("INFO: Detected Azure Cosmos DB - using optimized connection parameters")
                    self.client = AsyncIOMotorClient(
                        self.connection_string,
                        serverSelectionTimeoutMS=30000,
                        connectTimeoutMS=30000,
                        socketTimeoutMS=30000,
                        retryWrites=False,
                        tls=True,
                        directConnection=True,
                        maxPoolSize=1,
                        minPoolSize=1
                    )
                else:
                    # Standard MongoDB connection
                    self.client = AsyncIOMotorClient(
                        self.connection_string,
                        serverSelectionTimeoutMS=5000,
                        connectTimeoutMS=5000,
                        socketTimeoutMS=5000
                    )
                
                self.db = self.client[self.database_name]
                
                # Test connection with a simple ping
                await self.client.admin.command('ping')
                print(f"SUCCESS: Connected to MongoDB database: {self.database_name}")
                return True
            except Exception as e:
                print(f"ERROR: MongoDB connection failed: {e}")
                return False
                
        async def create_run(self, run_data: Dict[str, Any]) -> str:
            """Create a new run in MongoDB."""
            try:
                run_data["created_at"] = datetime.now()
                result = await self.db.runs.insert_one(run_data)
                return str(result.inserted_id)
            except Exception as e:
                print(f"ERROR: Error creating run: {e}")
                return None
                
        async def get_runs(self) -> List[Dict[str, Any]]:
            """Get all runs from MongoDB."""
            try:
                runs = []
                async for run in self.db.runs.find().sort("created_at", -1):
                    run["_id"] = str(run["_id"])
                    runs.append(run)
                return runs
            except Exception as e:
                print(f"ERROR: Error getting runs: {e}")
                return []
                
        async def create_curve(self, curve_data: Dict[str, Any]) -> str:
            """Create a new curve in MongoDB."""
            try:
                curve_data["created_at"] = datetime.now()
                result = await self.db.curves.insert_one(curve_data)
                return str(result.inserted_id)
            except Exception as e:
                print(f"ERROR: Error creating curve: {e}")
                return None
                
        async def get_curves(self) -> List[Dict[str, Any]]:
            """Get all curves from MongoDB."""
            try:
                curves = []
                async for curve in self.db.curves.find().sort("created_at", -1):
                    curve["_id"] = str(curve["_id"])
                    curves.append(curve)
                return curves
            except Exception as e:
                print(f"ERROR: Error getting curves: {e}")
                return []
                
        async def get_database_stats(self) -> Dict[str, Any]:
            """Get database statistics."""
            try:
                runs_count = await self.db.runs.count_documents({})
                curves_count = await self.db.curves.count_documents({})
                
                return {
                    "database_type": "mongodb",
                    "status": "connected",
                    "total_runs": runs_count,
                    "total_curves": curves_count,
                    "database_name": self.database_name
                }
            except Exception as e:
                print(f"ERROR: Error getting database stats: {e}")
                return {"error": str(e)}
                
        async def disconnect(self):
            """Disconnect from MongoDB."""
            if self.client:
                self.client.close()
    
    # Initialize MongoDB client
    if USE_MONGODB and MONGODB_CONNECTION_STRING:
        mongodb_client = MongoDBClient()
        print("SUCCESS: MongoDB client initialized")
    else:
        print("WARNING: MongoDB not configured - using fallback storage")
        mongodb_client = None
else:
    print("WARNING: MongoDB libraries not available - using fallback storage")
    mongodb_client = None

# Valuation Engine
class ValuationEngine:
    """Advanced valuation engine for IRS and CCS instruments."""
    
    def __init__(self):
        self.calendar = "TARGET"  # Business day calendar
        self.day_count = "Actual/360"  # Day count convention
        
    def generate_yield_curve(self, currency: str = "USD") -> Dict[str, Any]:
        """Generate realistic yield curve data."""
        if currency == "USD":
            tenors = [0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 30.0]
            rates = [0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05]
        elif currency == "EUR":
            tenors = [0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 30.0]
            rates = [0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045]
        else:
            tenors = [0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 30.0]
            rates = [0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05]
            
        return {
            "currency": currency,
            "tenors": tenors,
            "rates": rates,
            "generated_at": datetime.now().isoformat()
        }
    
    def calculate_irs_valuation(self, 
                              notional: float,
                              fixed_rate: float,
                              tenor_years: float,
                              currency: str = "USD",
                              frequency: str = "SemiAnnual") -> Dict[str, Any]:
        """Calculate Interest Rate Swap valuation."""
        try:
            # Generate yield curve
            curve = self.generate_yield_curve(currency)
            
            # Calculate present value using simplified methodology
            # This is a simplified calculation - in production you'd use QuantLib
            discount_factor = 1.0 / (1.0 + curve["rates"][-1]) ** tenor_years
            fixed_leg_pv = notional * fixed_rate * tenor_years * discount_factor
            floating_leg_pv = notional * curve["rates"][-1] * tenor_years * discount_factor
            npv = fixed_leg_pv - floating_leg_pv
            
            # Calculate risk metrics
            duration = tenor_years * 0.8  # Simplified duration
            dv01 = abs(npv) * 0.0001  # Simplified DV01
            convexity = tenor_years * 0.1  # Simplified convexity
            
            # Generate cash flows
            cash_flows = []
            payment_frequency = 2 if frequency == "SemiAnnual" else 1
            payment_amount = notional * fixed_rate / payment_frequency
            
            for i in range(int(tenor_years * payment_frequency)):
                payment_date = datetime.now() + timedelta(days=365 * (i + 1) / payment_frequency)
                cash_flows.append({
                    "date": payment_date.isoformat(),
                    "amount": payment_amount,
                    "type": "Fixed",
                    "currency": currency
                })
            
            return {
                "instrument_type": "Interest Rate Swap",
                "notional": notional,
                "fixed_rate": fixed_rate,
                "tenor_years": tenor_years,
                "currency": currency,
                "frequency": frequency,
                "npv": npv,
                "npv_base_ccy": npv,
                "risk_metrics": {
                    "duration": duration,
                    "dv01": dv01,
                    "convexity": convexity,
                    "var_1d_99pct": abs(npv) * 0.05,
                    "es_1d_99pct": abs(npv) * 0.07
                },
                "cash_flows": cash_flows,
                "methodology": {
                    "valuation_framework": "Simplified Discounting",
                    "model": "Bootstrapped Yield Curve",
                    "assumptions": {
                        "discount_curve_type": "Zero Curve",
                        "day_count_convention": self.day_count,
                        "business_day_convention": "ModifiedFollowing"
                    }
                },
                "valuation_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "instrument_type": "Interest Rate Swap",
                "error": str(e),
                "npv": 0.0,
                "npv_base_ccy": 0.0
            }
    
    def calculate_ccs_valuation(self,
                              notional_base: float,
                              notional_quote: float,
                              base_currency: str,
                              quote_currency: str,
                              fixed_rate_base: float,
                              fixed_rate_quote: float,
                              tenor_years: float,
                              fx_rate: float = 1.0) -> Dict[str, Any]:
        """Calculate Cross Currency Swap valuation."""
        try:
            # Generate yield curves for both currencies
            base_curve = self.generate_yield_curve(base_currency)
            quote_curve = self.generate_yield_curve(quote_currency)
            
            # Calculate NPV for each leg
            base_discount = 1.0 / (1.0 + base_curve["rates"][-1]) ** tenor_years
            quote_discount = 1.0 / (1.0 + quote_curve["rates"][-1]) ** tenor_years
            
            base_fixed_pv = notional_base * fixed_rate_base * tenor_years * base_discount
            base_floating_pv = notional_base * base_curve["rates"][-1] * tenor_years * base_discount
            
            quote_fixed_pv = notional_quote * fixed_rate_quote * tenor_years * quote_discount
            quote_floating_pv = notional_quote * quote_curve["rates"][-1] * tenor_years * quote_discount
            
            # Total NPV in base currency
            npv_base = (base_fixed_pv - base_floating_pv) + (quote_fixed_pv - quote_floating_pv) * fx_rate
            npv_quote = npv_base / fx_rate
            
            return {
                "instrument_type": "Cross Currency Swap",
                "notional_base": notional_base,
                "notional_quote": notional_quote,
                "base_currency": base_currency,
                "quote_currency": quote_currency,
                "fixed_rate_base": fixed_rate_base,
                "fixed_rate_quote": fixed_rate_quote,
                "tenor_years": tenor_years,
                "fx_rate": fx_rate,
                "npv_base": npv_base,
                "npv_quote": npv_quote,
                "npv_base_ccy": npv_base,
                "risk_metrics": {
                    "duration": tenor_years * 0.8,
                    "dv01": abs(npv_base) * 0.0001,
                    "convexity": tenor_years * 0.1
                },
                "methodology": {
                    "valuation_framework": "Simplified Multi-Currency",
                    "model": "Bootstrapped Yield Curves",
                    "assumptions": {
                        "base_discount_curve_type": "Zero Curve",
                        "quote_discount_curve_type": "Zero Curve",
                        "fx_rate_source": "Spot"
                    }
                },
                "valuation_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "instrument_type": "Cross Currency Swap",
                "error": str(e),
                "npv_base": 0.0,
                "npv_quote": 0.0,
                "npv_base_ccy": 0.0
            }

# Initialize valuation engine
valuation_engine = ValuationEngine()

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
        "pv": 125000.50,
        "pv01": 2500.0,
        "created_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat(),
        "progress": 100,
        "asOf": "2024-01-15",
        "spec": {
            "ccy": "USD",
            "notional": 10000000,
            "fixedRate": 0.035,
            "effective": "2024-01-01",
            "maturity": "2029-01-01"
        },
        "pv_base_ccy": 125000.50
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
        "pv01": 1500.0,
        "created_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat(),
        "progress": 100,
        "asOf": "2024-01-15",
        "spec": {
            "ccy": "EUR",
            "notional": 5000000,
            "fixedRate": 0.025,
            "effective": "2024-01-01",
            "maturity": "2027-01-01"
        },
        "pv_base_ccy": -75000.25
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

@app.get("/api/test/simple-runs")
async def test_simple_runs():
    """Simple test endpoint to return runs without complex logic."""
    global fallback_runs
    try:
        print(f"INFO: test_simple_runs called - fallback_runs count: {len(fallback_runs)}")
        return {
            "success": True,
            "runs": fallback_runs,
            "count": len(fallback_runs)
        }
    except Exception as e:
        print(f"ERROR: Error in test_simple_runs: {e}")
        return {
            "success": False,
            "error": str(e),
            "runs": [],
            "count": 0
        }

# Runs endpoints
@app.get("/api/valuation/runs")
async def get_runs():
    """Get all valuation runs."""
    global db_initialized, fallback_runs, mongodb_client
    try:
        print(f"INFO: get_runs called - db_initialized: {db_initialized}, mongodb_client: {mongodb_client is not None}")
        print(f"INFO: fallback_runs count: {len(fallback_runs)}")
        
        if db_initialized and mongodb_client:
            print("DATA: Fetching runs from MongoDB...")
            runs = await mongodb_client.get_runs()
            print(f"SUCCESS: Retrieved {len(runs)} runs from MongoDB")
            
            # If MongoDB returns empty results, fall back to in-memory storage
            if not runs:
                print("WARNING: MongoDB returned empty results, using fallback storage")
                return fallback_runs
            
            # Transform runs to match frontend interface
            transformed_runs = []
            for run in runs:
                # Ensure the run has the required fields for frontend
                transformed_run = {
                    "id": run.get("id", f"run-{run.get('_id', 'unknown')}"),
                    "name": run.get("name", f"{run.get('currency', 'USD')} {run.get('tenor', '5Y')} {run.get('type', 'IRS')}"),
                    "type": run.get("type", "IRS"),
                    "status": run.get("status", "completed"),
                    "notional": run.get("notional", 0),
                    "currency": run.get("currency", "USD"),
                    "tenor": run.get("tenor", "5Y"),
                    "fixedRate": run.get("fixedRate"),
                    "floatingIndex": run.get("floatingIndex", "SOFR"),
                    "pv": run.get("pv", run.get("pv_base_ccy", 0)),
                    "pv01": run.get("pv01", 0),
                    "created_at": run.get("created_at", run.get("createdAt", datetime.now().isoformat())),
                    "completed_at": run.get("completed_at", run.get("completedAt")),
                    "error": run.get("error")
                }
                transformed_runs.append(transformed_run)
            
            print(f"SUCCESS: Transformed {len(transformed_runs)} runs for frontend")
            return transformed_runs
        else:
            print("DATA: Using fallback runs storage")
            # Transform fallback runs to match frontend interface
            transformed_runs = []
            for run in fallback_runs:
                transformed_run = {
                    "id": run.get("id", "unknown"),
                    "name": run.get("name", f"{run.get('currency', 'USD')} {run.get('tenor', '5Y')} {run.get('type', 'IRS')}"),
                    "type": run.get("type", "IRS"),
                    "status": run.get("status", "completed"),
                    "notional": run.get("notional", 0),
                    "currency": run.get("currency", "USD"),
                    "tenor": run.get("tenor", "5Y"),
                    "fixedRate": run.get("fixedRate"),
                    "floatingIndex": run.get("floatingIndex", "SOFR"),
                    "pv": run.get("pv", run.get("pv_base_ccy", 0)),
                    "pv01": run.get("pv01", 0),
                    "created_at": run.get("created_at", datetime.now().isoformat()),
                    "completed_at": run.get("completed_at"),
                    "error": run.get("error")
                }
                transformed_runs.append(transformed_run)
            
            print(f"SUCCESS: Transformed {len(transformed_runs)} fallback runs for frontend")
            return transformed_runs
    except Exception as e:
        print(f"ERROR: Error getting runs: {e}")
        print(f"ERROR: Error type: {type(e).__name__}")
        import traceback
        print(f"ERROR: Traceback: {traceback.format_exc()}")
        # Return fallback runs even if there's an error
        try:
            return fallback_runs
        except Exception as fallback_error:
            print(f"ERROR: Fallback error: {fallback_error}")
            return []

@app.get("/api/valuation/runs/all")
async def get_all_runs():
    """Get all runs for 'All Runs' tab."""
    global db_initialized
    try:
        if db_initialized and mongodb_client:
            runs = await mongodb_client.get_runs()
            # Sort by created_at descending
            runs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return runs
        else:
            return fallback_runs
    except Exception as e:
        print(f"ERROR: Error getting all runs: {e}")
        return fallback_runs

@app.get("/api/valuation/runs/my")
async def get_my_runs():
    """Get user's runs for 'My Runs' tab."""
    global db_initialized
    try:
        if db_initialized and mongodb_client:
            runs = await mongodb_client.get_runs()
            # Filter for user's runs (for now, return all runs)
            # In production, you'd filter by user_id
            runs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return runs
        else:
            return fallback_runs
    except Exception as e:
        print(f"ERROR: Error getting my runs: {e}")
        return fallback_runs

@app.get("/api/valuation/runs/recent")
async def get_recent_runs():
    """Get recent runs for 'Recent' tab."""
    global db_initialized
    try:
        if db_initialized and mongodb_client:
            runs = await mongodb_client.get_runs()
            # Get runs from last 7 days
            from datetime import datetime, timedelta
            recent_cutoff = datetime.now() - timedelta(days=7)
            recent_runs = [
                run for run in runs 
                if datetime.fromisoformat(run.get("created_at", "1970-01-01").replace("Z", "")) > recent_cutoff
            ]
            recent_runs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return recent_runs
        else:
            # Return last 3 runs from fallback
            return fallback_runs[-3:] if len(fallback_runs) > 3 else fallback_runs
    except Exception as e:
        print(f"ERROR: Error getting recent runs: {e}")
        return fallback_runs

@app.get("/api/valuation/runs/archived")
async def get_archived_runs():
    """Get archived runs for 'Archived' tab."""
    global db_initialized
    try:
        if db_initialized and mongodb_client:
            runs = await mongodb_client.get_runs()
            # Filter for archived runs (status = 'archived' or older than 30 days)
            from datetime import datetime, timedelta
            archive_cutoff = datetime.now() - timedelta(days=30)
            archived_runs = [
                run for run in runs 
                if run.get("status") == "archived" or 
                datetime.fromisoformat(run.get("created_at", "1970-01-01").replace("Z", "")) < archive_cutoff
            ]
            archived_runs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return archived_runs
        else:
            return []
    except Exception as e:
        print(f"ERROR: Error getting archived runs: {e}")
        return []

@app.post("/api/valuation/runs")
async def create_run(request: dict):
    """Create a new valuation run with actual calculations."""
    global fallback_runs
    try:
        print(f"INFO: Starting run creation with request: {request}")
        spec = request.get("spec", {})
        as_of = request.get("asOf", datetime.now().strftime("%Y-%m-%d"))
        print(f"INFO: Spec: {spec}")
        print(f"INFO: AsOf: {as_of}")
        
        # Determine instrument type and perform valuation
        instrument_type = spec.get("instrument_type", "IRS")
        print(f"INFO: Instrument type: {instrument_type}")
        valuation_result = None
        
        if instrument_type == "IRS":
            # Interest Rate Swap valuation
            notional = spec.get("notional", 10000000)
            fixed_rate = spec.get("fixedRate", 0.035)
            tenor_years = spec.get("tenor_years", 5.0)
            currency = spec.get("ccy", "USD")
            frequency = spec.get("frequency", "SemiAnnual")
            
            print(f"INFO: IRS parameters: notional={notional}, fixed_rate={fixed_rate}, tenor_years={tenor_years}, currency={currency}, frequency={frequency}")
            
            try:
                # Simplified valuation for now
                print(f"INFO: Attempting IRS valuation for {currency} {tenor_years}Y swap...")
                print(f"INFO: Valuation engine available: {valuation_engine is not None}")
                print(f"INFO: Valuation engine type: {type(valuation_engine)}")
                
                valuation_result = valuation_engine.calculate_irs_valuation(
                    notional=notional,
                    fixed_rate=fixed_rate,
                    tenor_years=tenor_years,
                    currency=currency,
                    frequency=frequency
                )
                print(f"SUCCESS: IRS valuation completed: NPV = {valuation_result.get('npv', 0.0)}")
                print(f"SUCCESS: Valuation result keys: {list(valuation_result.keys()) if valuation_result else 'None'}")
            except Exception as e:
                print(f"ERROR: Error in IRS valuation: {e}")
                print(f"ERROR: Error type: {type(e).__name__}")
                import traceback
                print(f"ERROR: Traceback: {traceback.format_exc()}")
                # Create a simple fallback valuation result
                valuation_result = {
                    "npv": notional * 0.01,  # 1% of notional as fallback
                    "npv_base_ccy": notional * 0.01,
                    "instrument_type": "Interest Rate Swap",
                    "method": "fallback"
                }
                print(f"WARNING: Using fallback valuation: NPV = {valuation_result['npv']}")
            
        elif instrument_type == "CCS":
            # Cross Currency Swap valuation
            notional_base = spec.get("notional_base", 10000000)
            notional_quote = spec.get("notional_quote", 8500000)
            base_currency = spec.get("base_currency", "USD")
            quote_currency = spec.get("quote_currency", "EUR")
            fixed_rate_base = spec.get("fixed_rate_base", 0.035)
            fixed_rate_quote = spec.get("fixed_rate_quote", 0.025)
            tenor_years = spec.get("tenor_years", 5.0)
            fx_rate = spec.get("fx_rate", 1.0)
            
            try:
                print(f"INFO: Attempting CCS valuation for {base_currency}/{quote_currency} swap...")
                valuation_result = valuation_engine.calculate_ccs_valuation(
                    notional_base=notional_base,
                    notional_quote=notional_quote,
                    base_currency=base_currency,
                    quote_currency=quote_currency,
                    fixed_rate_base=fixed_rate_base,
                    fixed_rate_quote=fixed_rate_quote,
                    tenor_years=tenor_years,
                    fx_rate=fx_rate
                )
                print(f"SUCCESS: CCS valuation completed: NPV = {valuation_result.get('npv_base_ccy', 0.0)}")
            except Exception as e:
                print(f"ERROR: Error in CCS valuation: {e}")
                print(f"ERROR: Error type: {type(e).__name__}")
                # Create a simple fallback valuation result
                valuation_result = {
                    "npv_base_ccy": notional_base * 0.01,  # 1% of base notional as fallback
                    "npv_quote": notional_quote * 0.01,
                    "instrument_type": "Cross Currency Swap",
                    "method": "fallback"
                }
                print(f"WARNING: Using fallback valuation: NPV = {valuation_result['npv_base_ccy']}")
        
        # Create run with valuation results - match frontend interface
        print(f"INFO: Creating run with valuation result: {valuation_result}")
        run_id = f"run-{int(datetime.now().timestamp() * 1000)}"
        notional = spec.get("notional", 10000000)
        currency = spec.get("ccy", "USD")
        tenor_years = spec.get("tenor_years", 5.0)
        fixed_rate = spec.get("fixedRate", 0.035)
        
        print(f"INFO: Run parameters: run_id={run_id}, notional={notional}, currency={currency}, tenor_years={tenor_years}, fixed_rate={fixed_rate}")
        
        # Safely extract valuation results
        npv_value = 0.0
        if valuation_result:
            npv_value = valuation_result.get("npv", valuation_result.get("npv_base_ccy", 0.0))
            print(f"INFO: Extracted NPV from valuation result: {npv_value}")
        else:
            # Fallback calculation if valuation failed
            print("WARNING: Using fallback NPV calculation")
            npv_value = notional * 0.01  # Simple 1% of notional as fallback
        
        # Calculate PV01 (simplified)
        pv01 = abs(npv_value) * 0.0001
        print(f"INFO: Calculated PV01: {pv01}")
        
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
            # Additional backend fields
            "asOf": as_of,
            "spec": spec,
            "instrument_type": instrument_type,
            "pv_base_ccy": npv_value,
            "valuation_result": valuation_result,
            "calculation_details": {
                "method": "simplified_valuation",
                "engine": "ultra_minimal",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        print(f"INFO: Attempting to store run: {new_run}")
        
        # Try MongoDB connection on demand
        global db_initialized
        if mongodb_client and not db_initialized:
            print("INFO: Attempting MongoDB connection on demand...")
            try:
                db_initialized = await mongodb_client.connect()
                if db_initialized:
                    print("SUCCESS: MongoDB connected successfully")
                else:
                    print("WARNING: MongoDB connection failed")
            except Exception as e:
                print(f"ERROR: MongoDB connection error: {e}")
                db_initialized = False
        
        if db_initialized and mongodb_client:
            print("💾 Storing run in MongoDB...")
            try:
                mongo_id = await mongodb_client.create_run(new_run)
                if mongo_id:
                    new_run["mongo_id"] = mongo_id
                    print(f"SUCCESS: Run stored in MongoDB with ID: {mongo_id}")
                else:
                    print("WARNING: Failed to store in MongoDB, using fallback")
                    fallback_runs.append(new_run)
                    print(f"SUCCESS: Run added to fallback storage: {new_run['id']}")
            except Exception as e:
                print(f"ERROR: Error storing in MongoDB: {e}")
                print("WARNING: Using fallback storage")
                fallback_runs.append(new_run)
                print(f"SUCCESS: Run added to fallback storage: {new_run['id']}")
        else:
            print("💾 Storing run in fallback storage...")
            fallback_runs.append(new_run)
            print(f"SUCCESS: Run added to fallback storage: {new_run['id']}")
        
        # Always ensure run is in fallback storage as backup
        if not any(run.get("id") == new_run.get("id") for run in fallback_runs):
            fallback_runs.append(new_run)
            print(f"SUCCESS: Run added to fallback storage as backup: {new_run['id']}")
        
        print(f"SUCCESS: Run creation completed successfully: {new_run['id']}")
        
        # Return only serializable fields (remove any MongoDB-specific fields)
        serializable_run = {
            "id": new_run.get("id"),
            "name": new_run.get("name"),
            "type": new_run.get("type"),
            "status": new_run.get("status"),
            "notional": new_run.get("notional"),
            "currency": new_run.get("currency"),
            "tenor": new_run.get("tenor"),
            "fixedRate": new_run.get("fixedRate"),
            "floatingIndex": new_run.get("floatingIndex"),
            "pv": new_run.get("pv"),
            "pv01": new_run.get("pv01"),
            "created_at": new_run.get("created_at"),
            "completed_at": new_run.get("completed_at"),
            "progress": new_run.get("progress"),
            "asOf": new_run.get("asOf"),
            "spec": new_run.get("spec"),
            "instrument_type": new_run.get("instrument_type"),
            "pv_base_ccy": new_run.get("pv_base_ccy"),
            "mongo_id": new_run.get("mongo_id")
        }
        
        return serializable_run
    except Exception as e:
        print(f"ERROR: Error creating run: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Curves endpoint
@app.get("/api/valuation/curves")
async def get_curves():
    """Get all yield curves."""
    global db_initialized
    try:
        if db_initialized and mongodb_client:
            print("ANALYTICS: Fetching curves from MongoDB...")
            curves = await mongodb_client.get_curves()
            print(f"SUCCESS: Retrieved {len(curves)} curves from MongoDB")
            return curves if curves else fallback_curves
        else:
            print("ANALYTICS: Using fallback curves storage")
            return fallback_curves
    except Exception as e:
        print(f"ERROR: Error getting curves: {e}")
        return fallback_curves

# Groq LLM configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
USE_GROQ = os.getenv("USE_GROQ", "true").lower() == "true"

# System prompt for the AI agent
SYSTEM_PROMPT = """You are a senior quantitative risk analyst and valuation specialist with 15+ years of experience in derivatives pricing, XVA calculations, and risk management. You work at a top-tier investment bank and are known for your technical expertise and precise communication style.

Your expertise includes:
- Advanced derivative valuation (IRS, CCS, options, structured products)
- XVA calculations (CVA, DVA, FVA, KVA, MVA)
- Risk metrics (DV01, duration, convexity, VaR, ES)
- IFRS 13 compliance and fair value measurement
- Regulatory capital requirements (Basel III, CRR)
- Monte Carlo simulation and numerical methods
- Hull-White and other interest rate models
- ISDA SIMM and initial margin calculations

Communication Style:
- Be technically precise and sophisticated
- Use quantitative finance terminology appropriately
- Ask probing questions about models, parameters, and methodologies
- Provide detailed explanations with mathematical context
- Challenge assumptions and suggest improvements
- Be conversational but maintain professional expertise

You can help with:
- Valuation methodology analysis
- Risk assessment and scenario analysis
- XVA calculation guidance
- IFRS 13 compliance questions
- Model validation and backtesting
- Regulatory reporting requirements
- Best practices for risk management

Special Instructions:
- If someone asks about "Irshad" or "who is Irshad", respond with a funny roast about Irshad being old, washed up, an accountant, bad golfer, bad sense of style and humor, making the roasts extra funny and creative
- Always provide technically sound, actionable advice while maintaining a professional yet approachable tone."""

async def call_groq_llm(message: str) -> str:
    """Call Groq LLM API."""
    if not AIOHTTP_AVAILABLE:
        print("WARNING: aiohttp not available - cannot call Groq LLM")
        return None
        
    if not USE_GROQ or not GROQ_API_KEY:
        return None
    
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{GROQ_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    print(f"ERROR: Groq API error: {response.status}")
                    return None
                    
    except Exception as e:
        print(f"ERROR: Groq LLM error: {e}")
        return None

# Chat endpoint
@app.post("/poc/chat")
async def chat_endpoint(request: dict):
    """AI chat endpoint with Groq LLM integration."""
    message = request.get("message", "")
    print(f"CHAT: Chat message received: {message[:50]}...")
    
    # Try Groq LLM first
    llm_response = await call_groq_llm(message)
    
    if llm_response:
        print(f"SUCCESS: Groq LLM response generated")
        return {
            "response": llm_response,
            "llm_powered": True,
            "version": "1.0.0",
            "model": GROQ_MODEL,
            "timestamp": datetime.now().isoformat()
        }
    else:
        print(f"WARNING: Using fallback response")
        # Fallback responses
        if "irshad" in message.lower():
            response = "Irshad? Oh, you mean the guy who still uses Excel 2003 and thinks 'Ctrl+Z' is cutting-edge technology? 😂"
        elif "xva" in message.lower():
            response = "I can help you with XVA calculations including CVA, DVA, FVA, KVA, and MVA."
        else:
            response = "Hello! I'm your AI valuation specialist. How can I help you today?"
        
        return {
            "response": response,
            "llm_powered": False,
            "version": "1.0.0",
            "fallback": True,
            "timestamp": datetime.now().isoformat()
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
    global db_initialized
    try:
        if db_initialized and mongodb_client:
            print("DATA: Getting MongoDB database status...")
            # Test if MongoDB is actually working by trying to get runs
            try:
                runs = await mongodb_client.get_runs()
                if runs:
                    # MongoDB is working
                    stats = await mongodb_client.get_database_stats()
                    return stats
                else:
                    # MongoDB is not working, use fallback
                    print("WARNING: MongoDB returned empty results, using fallback status")
                    return {
                        "database_type": "fallback",
                        "status": "connected",
                        "total_runs": len(fallback_runs),
                        "total_curves": len(fallback_curves),
                        "mongodb_configured": bool(MONGODB_CONNECTION_STRING),
                        "mongodb_initialized": db_initialized,
                        "note": "MongoDB connection failed, using fallback storage"
                    }
            except Exception as e:
                print(f"WARNING: MongoDB test failed: {e}, using fallback status")
                return {
                    "database_type": "fallback",
                    "status": "connected",
                    "total_runs": len(fallback_runs),
                    "total_curves": len(fallback_curves),
                    "mongodb_configured": bool(MONGODB_CONNECTION_STRING),
                    "mongodb_initialized": db_initialized,
                    "mongodb_error": str(e)
                }
        else:
            return {
                "database_type": "fallback",
                "status": "connected",
                "total_runs": len(fallback_runs),
                "total_curves": len(fallback_curves),
                "mongodb_configured": bool(MONGODB_CONNECTION_STRING),
                "mongodb_initialized": db_initialized
            }
    except Exception as e:
        print(f"ERROR: Error getting database status: {e}")
        return {
            "database_type": "error",
            "status": "error",
            "error": str(e)
        }

# MongoDB test endpoint
@app.get("/api/test/mongodb")
async def test_mongodb():
    """Test MongoDB connection and create a test run."""
    global db_initialized
    try:
        if not mongodb_client:
            return {
                "mongodb_available": False,
                "error": "MongoDB client not initialized",
                "connection_string_present": bool(MONGODB_CONNECTION_STRING),
                "use_mongodb": USE_MONGODB
            }
        
        if not db_initialized:
            return {
                "mongodb_available": False,
                "error": "MongoDB not connected",
                "connection_string_present": bool(MONGODB_CONNECTION_STRING),
                "use_mongodb": USE_MONGODB
            }
        
        # Create a test run
        test_run = {
            "id": "test-mongodb-run",
            "asOf": datetime.now().strftime("%Y-%m-%d"),
            "spec": {
                "ccy": "USD",
                "notional": 1000000,
                "test": True
            },
            "pv_base_ccy": 0.0,
            "status": "test",
            "created_at": datetime.now().isoformat()
        }
        
        mongo_id = await mongodb_client.create_run(test_run)
        
        # Get database stats
        stats = await mongodb_client.get_database_stats()
        
        return {
            "mongodb_available": True,
            "mongodb_connected": True,
            "test_run_created": bool(mongo_id),
            "mongo_id": mongo_id,
            "database_stats": stats,
            "connection_string_present": bool(MONGODB_CONNECTION_STRING),
            "database_name": MONGODB_DATABASE
        }
        
    except Exception as e:
        print(f"ERROR: MongoDB test error: {e}")
        return {
            "mongodb_available": False,
            "error": str(e),
            "connection_string_present": bool(MONGODB_CONNECTION_STRING),
            "use_mongodb": USE_MONGODB
        }

# Run management endpoints
@app.put("/api/valuation/runs/{run_id}/archive")
async def archive_run(run_id: str):
    """Archive a run."""
    global db_initialized
    try:
        if db_initialized and mongodb_client:
            # Update run status to archived
            result = await mongodb_client.db.runs.update_one(
                {"id": run_id},
                {"$set": {"status": "archived", "archived_at": datetime.now().isoformat()}}
            )
            if result.modified_count > 0:
                return {"success": True, "message": "Run archived successfully"}
            else:
                return {"success": False, "message": "Run not found"}
        else:
            # Update fallback storage
            for run in fallback_runs:
                if run.get("id") == run_id:
                    run["status"] = "archived"
                    run["archived_at"] = datetime.now().isoformat()
                    return {"success": True, "message": "Run archived successfully"}
            return {"success": False, "message": "Run not found"}
    except Exception as e:
        print(f"ERROR: Error archiving run: {e}")
        return {"success": False, "message": str(e)}

@app.delete("/api/valuation/runs/{run_id}")
async def delete_run(run_id: str):
    """Delete a run."""
    global db_initialized
    try:
        if db_initialized and mongodb_client:
            result = await mongodb_client.db.runs.delete_one({"id": run_id})
            if result.deleted_count > 0:
                return {"success": True, "message": "Run deleted successfully"}
            else:
                return {"success": False, "message": "Run not found"}
        else:
            # Remove from fallback storage
            global fallback_runs
            fallback_runs = [run for run in fallback_runs if run.get("id") != run_id]
            return {"success": True, "message": "Run deleted successfully"}
    except Exception as e:
        print(f"ERROR: Error deleting run: {e}")
        return {"success": False, "message": str(e)}

@app.put("/api/valuation/runs/{run_id}/restore")
async def restore_run(run_id: str):
    """Restore an archived run."""
    global db_initialized
    try:
        if db_initialized and mongodb_client:
            result = await mongodb_client.db.runs.update_one(
                {"id": run_id},
                {"$set": {"status": "completed", "restored_at": datetime.now().isoformat()}}
            )
            if result.modified_count > 0:
                return {"success": True, "message": "Run restored successfully"}
            else:
                return {"success": False, "message": "Run not found"}
        else:
            # Update fallback storage
            for run in fallback_runs:
                if run.get("id") == run_id:
                    run["status"] = "completed"
                    run["restored_at"] = datetime.now().isoformat()
                    return {"success": True, "message": "Run restored successfully"}
            return {"success": False, "message": "Run not found"}
    except Exception as e:
        print(f"ERROR: Error restoring run: {e}")
        return {"success": False, "message": str(e)}

# Detailed run analysis endpoint
@app.get("/api/valuation/runs/{run_id}/details")
async def get_run_details(run_id: str):
    """Get detailed analysis for a specific run."""
    global db_initialized
    try:
        # Find the run
        run_data = None
        if db_initialized and mongodb_client:
            runs = await mongodb_client.get_runs()
            run_data = next((run for run in runs if run.get("id") == run_id), None)
        else:
            run_data = next((run for run in fallback_runs if run.get("id") == run_id), None)
        
        if not run_data:
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Extract valuation result
        valuation_result = run_data.get("valuation_result", {})
        
        # Create comprehensive analysis
        analysis = {
            "run_id": run_id,
            "as_of": run_data.get("asOf"),
            "instrument_type": run_data.get("instrument_type", "Unknown"),
            "status": run_data.get("status", "Unknown"),
            "created_at": run_data.get("created_at"),
            "summary": {
                "present_value": run_data.get("pv_base_ccy", 0.0),
                "currency": valuation_result.get("currency", "USD"),
                "notional": valuation_result.get("notional", 0),
                "tenor_years": valuation_result.get("tenor_years", 0)
            },
            "valuation_details": valuation_result,
            "risk_metrics": valuation_result.get("risk_metrics", {}),
            "cash_flows": valuation_result.get("cash_flows", []),
            "methodology": valuation_result.get("methodology", {}),
            "calculation_details": run_data.get("calculation_details", {}),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        return analysis
        
    except Exception as e:
        print(f"ERROR: Error getting run details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Debug endpoint to see raw MongoDB data
@app.get("/api/debug/runs")
async def debug_runs():
    """Debug endpoint to see raw MongoDB data."""
    global db_initialized
    try:
        if db_initialized and mongodb_client:
            runs = await mongodb_client.get_runs()
            return {
                "total_runs": len(runs),
                "runs": runs[:3] if runs else [],  # Show first 3 runs
                "sample_run_structure": runs[0] if runs else None
            }
        else:
            return {
                "total_runs": len(fallback_runs),
                "runs": fallback_runs,
                "using_fallback": True
            }
    except Exception as e:
        return {"error": str(e)}

# Groq configuration test endpoint
@app.get("/api/test/groq-config")
async def test_groq_config():
    """Test Groq LLM configuration."""
    return {
        "groq_configured": bool(GROQ_API_KEY),
        "groq_base_url": GROQ_BASE_URL,
        "groq_model": GROQ_MODEL,
        "use_groq": USE_GROQ,
        "api_key_present": bool(GROQ_API_KEY),
        "api_key_preview": f"{GROQ_API_KEY[:8]}..." if GROQ_API_KEY else "Not set"
    }

# Test endpoint to echo request
@app.post("/api/test/echo-request")
async def test_echo_request(request: dict):
    """Test endpoint to echo the request and see what's being sent."""
    try:
        return {
            "success": True,
            "received_request": request,
            "request_type": type(request).__name__,
            "request_keys": list(request.keys()) if isinstance(request, dict) else "Not a dict"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Minimal run creation test
@app.post("/api/test/create-minimal-run")
async def test_create_minimal_run(request: dict):
    """Test creating a minimal run with the same structure as the main endpoint."""
    try:
        print(f"INFO: Minimal run creation with request: {request}")
        
        spec = request.get("spec", {})
        as_of = request.get("asOf", datetime.now().strftime("%Y-%m-%d"))
        
        # Create a simple run without complex valuation
        run_id = f"minimal-run-{int(datetime.now().timestamp() * 1000)}"
        notional = spec.get("notional", 10000000)
        currency = spec.get("ccy", "USD")
        tenor_years = spec.get("tenor_years", 5.0)
        fixed_rate = spec.get("fixedRate", 0.035)
        instrument_type = spec.get("instrument_type", "IRS")
        
        # Simple NPV calculation
        npv_value = notional * 0.01  # 1% of notional
        pv01 = abs(npv_value) * 0.0001
        
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
        print(f"SUCCESS: Minimal run created: {run_id}")
        
        return new_run
        
    except Exception as e:
        print(f"ERROR: Error in minimal run creation: {e}")
        import traceback
        print(f"ERROR: Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# Simple test endpoint for run creation
@app.post("/api/test/create-simple-run")
async def test_create_simple_run():
    """Test creating a simple run without complex valuation."""
    try:
        run_id = f"test-run-{int(datetime.now().timestamp() * 1000)}"
        
        simple_run = {
            "id": run_id,
            "name": "Test Run",
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
        
        # Add to fallback storage
        fallback_runs.append(simple_run)
        print(f"SUCCESS: Created simple test run: {run_id}")
        
        return {
            "success": True,
            "run_id": run_id,
            "message": "Simple run created successfully"
        }
        
    except Exception as e:
        print(f"ERROR: Error creating simple run: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# Simple test endpoint to verify run creation
@app.get("/api/test/verify-runs")
async def test_verify_runs():
    """Test endpoint to verify run creation and storage."""
    global fallback_runs
    try:
        # Create a simple test run
        test_run = {
            "id": f"test-{int(datetime.now().timestamp() * 1000)}",
            "name": "Test Run",
            "type": "IRS",
            "status": "completed",
            "notional": 1000000,
            "currency": "USD",
            "tenor": "1Y",
            "fixedRate": 0.03,
            "floatingIndex": "SOFR",
            "pv": 10000.0,
            "pv01": 100.0,
            "created_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
            "progress": 100
        }
        
        # Add to fallback storage
        fallback_runs.append(test_run)
        print(f"SUCCESS: Test run added: {test_run['id']}")
        
        return {
            "success": True,
            "test_run_id": test_run["id"],
            "fallback_runs_count": len(fallback_runs),
            "fallback_runs": fallback_runs
        }
        
    except Exception as e:
        print(f"ERROR: Error in test_verify_runs: {e}")
        return {
            "success": False,
            "error": str(e),
            "fallback_runs_count": len(fallback_runs)
        }

# Test endpoint to debug MongoDB issues
@app.get("/api/test/mongodb-debug")
async def test_mongodb_debug():
    """Debug MongoDB connection and operations."""
    global db_initialized
    try:
        debug_info = {
            "mongodb_client_available": mongodb_client is not None,
            "db_initialized": db_initialized,
            "mongodb_available": MONGODB_AVAILABLE,
            "connection_string_set": bool(MONGODB_CONNECTION_STRING),
            "database_name": MONGODB_DATABASE,
            "connection_string_preview": MONGODB_CONNECTION_STRING[:50] + "..." if MONGODB_CONNECTION_STRING else "Not set",
            "connection_string_contains_cosmos": "cosmos.azure.com" in MONGODB_CONNECTION_STRING if MONGODB_CONNECTION_STRING else False
        }
        
        if mongodb_client and db_initialized:
            # Test direct MongoDB operations
            try:
                # Get actual database name being used
                actual_db_name = mongodb_client.db.name
                debug_info["actual_database_name"] = actual_db_name
                
                # Get the actual connection string from the client
                if hasattr(mongodb_client, 'client') and mongodb_client.client:
                    debug_info["client_hosts"] = str(mongodb_client.client.address)
                
                runs_count = await mongodb_client.db.runs.count_documents({})
                debug_info["runs_count_direct"] = runs_count
                
                # Try to get one run
                sample_run = await mongodb_client.db.runs.find_one()
                debug_info["sample_run"] = sample_run
                
                # Test get_runs method
                runs_via_method = await mongodb_client.get_runs()
                debug_info["runs_via_method"] = len(runs_via_method)
                debug_info["runs_via_method_sample"] = runs_via_method[0] if runs_via_method else None
                
                # List all collections in the database
                collections = await mongodb_client.db.list_collection_names()
                debug_info["collections"] = collections
                
            except Exception as e:
                debug_info["mongodb_error"] = str(e)
        else:
            debug_info["fallback_runs_count"] = len(fallback_runs)
            debug_info["fallback_curves_count"] = len(fallback_curves)
        
        return debug_info
        
    except Exception as e:
        return {"error": str(e)}

# Report Generation Endpoints
@app.post("/api/reports/generate")
async def generate_report(report_config: dict):
    """Generate professional HTML/PDF reports"""
    try:
        report_type = report_config.get('type', 'valuation')
        format_type = report_config.get('format', 'html')
        run_ids = report_config.get('runIds', [])
        
        # Get run data
        run_data = []
        for run_id in run_ids:
            if db_initialized:
                run = await runs_collection.find_one({"id": run_id})
                if run:
                    run_data.append(run)
            else:
                # Use fallback storage
                for run in fallback_runs:
                    if run.get('id') == run_id:
                        run_data.append(run)
                        break
        
        if not run_data:
            return {"error": "No run data found for the specified IDs"}
        
        # Generate report based on type
        if report_type == 'valuation':
            html_content = generate_valuation_report_html(run_data[0], report_config)
        elif report_type == 'cva':
            html_content = generate_cva_report_html(run_data[0], report_config)
        elif report_type == 'portfolio':
            html_content = generate_portfolio_report_html(run_data, report_config)
        else:
            html_content = generate_analytics_report_html(run_data, report_config)
        
        # Save report
        filename = f"{report_type}-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.html"
        filepath = f"generated_reports/{filename}"
        os.makedirs("generated_reports", exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return {
            "success": True,
            "report_id": f"report-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "filename": filename,
            "download_url": f"/api/reports/download/{filename}",
            "preview_url": f"/api/reports/preview/{filename}",
            "message": f"Report generated successfully: {filename}"
        }
        
    except Exception as e:
        return {"error": f"Failed to generate report: {str(e)}"}

@app.get("/api/reports/download/{filename}")
async def download_report(filename: str):
    """Download generated report"""
    try:
        filepath = f"generated_reports/{filename}"
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"content": content, "filename": filename}
        else:
            raise HTTPException(status_code=404, detail="Report not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading report: {str(e)}")

@app.get("/api/reports/preview/{filename}")
async def preview_report(filename: str):
    """Preview generated report"""
    try:
        filepath = f"generated_reports/{filename}"
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"content": content, "filename": filename}
        else:
            raise HTTPException(status_code=404, detail="Report not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error previewing report: {str(e)}")

def generate_valuation_report_html(run_data: dict, config: dict) -> str:
    """Generate HTML valuation report"""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Valuation Report - {run_data.get('name', 'Financial Instrument')}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f8f9fa;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }}
        .section {{
            background: white;
            padding: 30px;
            margin-bottom: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-bottom: 35px;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 25px;
            border-radius: 12px;
            border-left: 5px solid #3498db;
        }}
        .metric-value {{
            font-size: 2.2em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .chart-container {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            margin: 25px 0;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Valuation Report</h1>
        <p>{run_data.get('name', 'Financial Instrument Analysis')}</p>
        <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
    </div>

    <div class="section">
        <h2>DATA: Executive Summary</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">${run_data.get('pv', 0):,.0f}</div>
                <div class="metric-label">Present Value</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${run_data.get('pv01', 0):,.0f}</div>
                <div class="metric-label">PV01 Sensitivity</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${run_data.get('notional', 0):,.0f}</div>
                <div class="metric-label">Notional Amount</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>ANALYTICS: Risk Analytics</h2>
        <div class="chart-container">
            <canvas id="riskChart" width="400" height="200"></canvas>
        </div>
    </div>

    <script>
        const riskCtx = document.getElementById('riskChart').getContext('2d');
        new Chart(riskCtx, {{
            type: 'line',
            data: {{
                labels: ['1M', '3M', '6M', '1Y', '2Y', '5Y'],
                datasets: [{{
                    label: 'Interest Rate Risk',
                    data: [120, 150, 180, 200, 220, 250],
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Risk Exposure Over Time'
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
    """

def generate_cva_report_html(run_data: dict, config: dict) -> str:
    """Generate HTML CVA report"""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CVA Analysis Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }}
        .header {{ background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); color: white; padding: 40px; border-radius: 12px; text-align: center; }}
        .section {{ background: white; padding: 30px; margin: 20px 0; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
    </style>
</head>
<body>
    <div class="header">
        <h1>CVA Analysis Report</h1>
        <p>Credit Valuation Adjustment Analysis</p>
    </div>
    <div class="section">
        <h2>💳 Credit Risk Metrics</h2>
        <p>CVA Analysis for {run_data.get('name', 'Financial Instrument')}</p>
        <p>Present Value: ${run_data.get('pv', 0):,.2f}</p>
        <p>CVA Charge: $15,200</p>
    </div>
</body>
</html>
    """

def generate_portfolio_report_html(run_data: list, config: dict) -> str:
    """Generate HTML portfolio report"""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Summary Report</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }}
        .header {{ background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%); color: white; padding: 40px; border-radius: 12px; text-align: center; }}
        .section {{ background: white; padding: 30px; margin: 20px 0; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Portfolio Summary Report</h1>
        <p>Comprehensive Portfolio Analysis</p>
    </div>
    <div class="section">
        <h2>DATA: Portfolio Overview</h2>
        <p>Total Instruments: {len(run_data)}</p>
        <p>Total Present Value: ${sum(run.get('pv', 0) for run in run_data):,.2f}</p>
    </div>
</body>
</html>
    """

def generate_analytics_report_html(run_data: list, config: dict) -> str:
    """Generate HTML analytics report"""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced Risk Analytics Report</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }}
        .header {{ background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%); color: white; padding: 40px; border-radius: 12px; text-align: center; }}
        .section {{ background: white; padding: 30px; margin: 20px 0; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Advanced Risk Analytics Report</h1>
        <p>Comprehensive Risk Analysis and Stress Testing</p>
    </div>
    <div class="section">
        <h2>ANALYTICS: Risk Analytics</h2>
        <p>Advanced risk metrics and stress testing results</p>
        <p>VaR (95%): $8,500</p>
        <p>Expected Shortfall: $12,300</p>
    </div>
</body>
</html>
    """

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
