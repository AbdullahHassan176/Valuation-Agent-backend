#!/usr/bin/env python3
"""
Simple FastAPI backend for Azure App Service
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import json
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Try to import MongoDB client, fallback if not available
try:
    from mongodb_client import mongodb_client
    MONGODB_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ MongoDB dependencies not available: {e}")
    print("💡 Using fallback storage mode")
    MONGODB_AVAILABLE = False
    mongodb_client = None

# Initialize MongoDB connection
async def init_database():
    """Initialize MongoDB connection."""
    if not MONGODB_AVAILABLE:
        print("⚠️ MongoDB dependencies not available, using fallback mode")
        print("💡 To enable MongoDB: Install pymongo and motor packages")
        return False
        
    try:
        # Check if MongoDB connection string is configured
        connection_string = os.getenv("MONGODB_CONNECTION_STRING")
        database_name = os.getenv("MONGODB_DATABASE", "valuation-backend-server")
        
        print(f"🔍 MongoDB connection string configured: {bool(connection_string)}")
        print(f"🔍 Database name: {database_name}")
        
        if not connection_string or connection_string == "mongodb://localhost:27017":
            print("⚠️ MongoDB connection string not configured, using fallback mode")
            print("💡 To enable MongoDB: Set MONGODB_CONNECTION_STRING environment variable")
            return False
        
        # Set the database name in the client
        mongodb_client.database_name = database_name
        
        print(f"🔍 Attempting to connect to MongoDB...")
        success = await mongodb_client.connect()
        
        if success:
            print("✅ MongoDB connected successfully")
            # Test the connection with a simple operation
            try:
                test_result = await mongodb_client.db.command("ping")
                print(f"✅ MongoDB ping successful: {test_result}")
            except Exception as ping_error:
                print(f"⚠️ MongoDB ping failed: {ping_error}")
                success = False
        else:
            print("❌ MongoDB connection failed, falling back to in-memory storage")
        
        return success
    except Exception as e:
        print(f"❌ MongoDB initialization error: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False

# Financial calculation functions
def calculate_present_value(notional: float, rate: float, time_to_maturity: float, 
                           instrument_type: str = "IRS") -> float:
    """Calculate present value using simplified financial formulas."""
    if instrument_type == "IRS":
        # Interest Rate Swap: PV = Notional * (Fixed Rate - Floating Rate) * Time
        # Simplified: assume floating rate = 0.05 (5%)
        floating_rate = 0.05
        rate_diff = rate - floating_rate
        pv = notional * rate_diff * time_to_maturity
    elif instrument_type == "CCS":
        # Cross Currency Swap: more complex, simplified here
        pv = notional * rate * time_to_maturity * 0.8  # Currency risk factor
    else:
        # Generic bond-like instrument
        pv = notional * rate * time_to_maturity
    
    return pv

def calculate_risk_metrics(notional: float, pv: float, currency: str) -> Dict[str, float]:
    """Calculate basic risk metrics."""
    # Simplified risk calculations
    duration = 2.5  # Simplified duration
    convexity = 0.1  # Simplified convexity
    
    # Interest rate sensitivity (DV01)
    dv01 = notional * duration * 0.0001
    
    # Currency risk (if not USD)
    fx_risk = 0.0
    if currency != "USD":
        fx_risk = abs(pv) * 0.1  # 10% FX risk for non-USD
    
    return {
        "duration": duration,
        "convexity": convexity,
        "dv01": dv01,
        "fx_risk": fx_risk,
        "var_95": abs(pv) * 0.02,  # 2% VaR
        "expected_shortfall": abs(pv) * 0.03  # 3% ES
    }

def generate_realistic_rates(currency: str, base_rate: float = 0.05) -> List[Dict[str, Any]]:
    """Generate realistic yield curve rates."""
    tenors = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "15Y", "20Y", "30Y"]
    rates = []
    
    for i, tenor in enumerate(tenors):
        # Generate realistic yield curve shape
        if tenor in ["1M", "3M"]:
            rate = base_rate - 0.01  # Short end lower
        elif tenor in ["6M", "1Y"]:
            rate = base_rate  # Around base rate
        elif tenor in ["2Y", "3Y", "5Y"]:
            rate = base_rate + 0.005 + (i * 0.001)  # Slight upward slope
        else:
            rate = base_rate + 0.01 + (i * 0.0005)  # Long end higher
        
        # Add some randomness
        rate += (hash(tenor + currency) % 100 - 50) / 10000
        
        rates.append({
            "tenor": tenor,
            "rate": round(rate, 4),
            "discount_factor": round(math.exp(-rate * (i + 1) / 12), 6)
        })
    
    return rates

# Initialize database (will be called in startup)
db_initialized = False

# Fallback in-memory storage for when MongoDB isn't available
fallback_runs = []
fallback_curves = []

# Create FastAPI app
app = FastAPI(
    title="Valuation Agent Backend",
    description="Backend service for valuation agent",
    version="1.0.0"
)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize MongoDB connection on startup."""
    global db_initialized
    db_initialized = await init_database()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "Valuation Agent Backend", 
        "version": "1.0.0", 
        "status": "running",
        "service": "backend"
    }

@app.get("/healthz")
def health():
    return {"ok": True, "service": "backend", "status": "healthy"}

@app.get("/api/database/status")
async def database_status():
    """Get database status and statistics."""
    if not MONGODB_AVAILABLE:
        return {
            "database_type": "Fallback Mode (In-Memory)",
            "database_name": "fallback_storage",
            "total_runs": len(fallback_runs),
            "total_curves": len(fallback_curves),
            "recent_runs": fallback_runs[-5:] if fallback_runs else [],
            "message": "MongoDB dependencies not available - using in-memory storage. Install pymongo and motor to enable MongoDB."
        }
    
    if not db_initialized:
        return {
            "database_type": "Fallback Mode (In-Memory)",
            "database_name": "fallback_storage",
            "total_runs": len(fallback_runs),
            "total_curves": len(fallback_curves),
            "recent_runs": fallback_runs[-5:] if fallback_runs else [],
            "message": "MongoDB not configured - using in-memory storage. Configure MONGODB_CONNECTION_STRING to use Azure Cosmos DB."
        }
    
    try:
        stats = await mongodb_client.get_database_stats()
        return stats
    except Exception as e:
        return {
            "database_type": "MongoDB (Azure Cosmos DB)",
            "status": "error",
            "error": str(e),
            "message": "Error retrieving database statistics"
        }

@app.get("/api/valuation/runs")
async def get_runs():
    """Get all valuation runs from MongoDB or fallback storage."""
    if not MONGODB_AVAILABLE or not db_initialized:
        # Return fallback runs
        return fallback_runs
    
    try:
        runs = await mongodb_client.get_runs()
        return runs
    except Exception as e:
        # Fallback to in-memory storage
        return fallback_runs

@app.post("/api/valuation/runs")
async def create_run(request: dict = None):
    """Create a new valuation run in MongoDB or fallback storage."""
    if not MONGODB_AVAILABLE or not db_initialized:
        print("⚠️ MongoDB not available, using fallback storage")
    
    run_id = f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    current_time = datetime.now().isoformat()
    
    # Extract data from request - handle both old and new payload formats
    instrument_type = "IRS"  # Default
    currency = "USD"  # Default
    notional_amount = 1000000.0  # Default
    as_of_date = datetime.now().strftime('%Y-%m-%d')
    spec = None
    
    if request:
        # Check if this is the new frontend payload format
        if "spec" in request:
            spec = request.get("spec", {})
            instrument_type = "IRS"  # Determine from spec if needed
            if spec.get("notionalCcy2") or spec.get("ccy2"):
                instrument_type = "CCS"  # Cross Currency Swap
            currency = spec.get("ccy", "USD")
            notional_amount = spec.get("notional", 1000000.0)
            as_of_date = request.get("asOf", datetime.now().strftime('%Y-%m-%d'))
        else:
            # Old format
            instrument_type = request.get("instrument_type", instrument_type)
            currency = request.get("currency", currency)
            notional_amount = request.get("notional_amount", notional_amount)
            as_of_date = request.get("as_of_date", as_of_date)
    
    # Calculate realistic PV using financial formulas
    time_to_maturity = 5.0  # Default 5 years
    rate = 0.055  # Default 5.5% rate
    
    # Use spec data if available for more accurate calculations
    if spec:
        # Calculate actual time to maturity from spec
        if "effective" in spec and "maturity" in spec:
            try:
                effective_date = datetime.strptime(spec["effective"], "%Y-%m-%d")
                maturity_date = datetime.strptime(spec["maturity"], "%Y-%m-%d")
                time_to_maturity = (maturity_date - effective_date).days / 365.25
            except:
                pass  # Use default if parsing fails
        
        # Use actual fixed rate from spec
        if "fixedRate" in spec:
            rate = spec["fixedRate"]
    
    # Use financial calculation
    pv_base_ccy = calculate_present_value(notional_amount, rate, time_to_maturity, instrument_type)
    
    # Calculate risk metrics
    risk_metrics = calculate_risk_metrics(notional_amount, pv_base_ccy, currency)
    
    # Prepare run data for MongoDB
    run_data = {
        "id": run_id,
        "status": "completed",
        "instrument_type": instrument_type,
        "currency": currency,
        "notional_amount": notional_amount,
        "as_of_date": as_of_date,
        "pv_base_ccy": round(pv_base_ccy, 2),
        "spec": spec if spec else None,
        "metadata": {
            "source": "backend",
            "calculation_method": "enhanced_financial",
            "time_to_maturity": time_to_maturity,
            "rate_used": rate,
            "risk_metrics": risk_metrics,
            "calculation_timestamp": current_time,
            "payload_format": "new_frontend" if spec else "legacy"
        }
    }
    
    if MONGODB_AVAILABLE and db_initialized:
        try:
            # Insert into MongoDB
            mongo_id = await mongodb_client.create_run(run_data)
            
            return {
                "message": "Run created successfully with enhanced financial calculations (MongoDB)",
                "status": "success",
                "id": run_id,
                "mongo_id": mongo_id,
                "pv_base_ccy": round(pv_base_ccy, 2),
                "risk_metrics": risk_metrics,
                "calculation_details": {
                    "method": "enhanced_financial",
                    "time_to_maturity": time_to_maturity,
                    "rate_used": rate,
                    "instrument_type": instrument_type
                }
            }
        except Exception as e:
            print(f"❌ MongoDB error: {e}, falling back to in-memory storage")
            # Fall through to fallback storage
    
    # Fallback to in-memory storage
    run_data["_id"] = f"fallback_{run_id}"
    fallback_runs.append(run_data)
    
    return {
        "message": "Run created successfully with enhanced financial calculations (Fallback Storage)",
        "status": "success",
        "id": run_id,
        "storage_type": "fallback",
        "pv_base_ccy": round(pv_base_ccy, 2),
        "risk_metrics": risk_metrics,
        "calculation_details": {
            "method": "enhanced_financial",
            "time_to_maturity": time_to_maturity,
            "rate_used": rate,
            "instrument_type": instrument_type
        }
    }

@app.get("/api/valuation/curves")
async def get_curves():
    """Get yield curves from MongoDB or fallback storage."""
    if not MONGODB_AVAILABLE or not db_initialized:
        # Return fallback curves or generate sample curves
        if not fallback_curves:
            # Generate sample curves if none exist
            sample_curves = []
            for currency in ["USD", "EUR", "GBP"]:
                curve_data = {
                    "id": f"{currency}_OIS_{datetime.now().strftime('%Y-%m-%d')}",
                    "currency": currency,
                    "type": "OIS",
                    "as_of_date": datetime.now().strftime('%Y-%m-%d'),
                    "nodes": generate_realistic_rates(currency, 0.05),
                    "created_at": datetime.now().isoformat()
                }
                sample_curves.append(curve_data)
                fallback_curves.append(curve_data)
            return sample_curves
        return fallback_curves
    
    try:
        # Get curves from MongoDB
        curves = await mongodb_client.get_curves()
        return curves
    except Exception as e:
        # Fallback to in-memory storage
        return fallback_curves

@app.post("/api/valuation/curves")
async def create_curves():
    """Create sample yield curves."""
    curves_created = []
    
    for currency in ["USD", "EUR", "GBP"]:
        curve_data = {
            "id": f"{currency}_OIS_{datetime.now().strftime('%Y-%m-%d')}",
            "currency": currency,
            "type": "OIS",
            "as_of_date": datetime.now().strftime('%Y-%m-%d'),
            "nodes": generate_realistic_rates(currency, 0.05),
            "created_at": datetime.now().isoformat()
        }
        
        if MONGODB_AVAILABLE and db_initialized:
            try:
                # Store in MongoDB
                mongo_id = await mongodb_client.create_curve(curve_data)
                curve_data["_id"] = mongo_id
                curves_created.append(curve_data)
            except Exception as e:
                print(f"❌ Error storing curve in MongoDB: {e}")
                # Fallback to in-memory storage
                fallback_curves.append(curve_data)
                curves_created.append(curve_data)
        else:
            # Store in fallback storage
            fallback_curves.append(curve_data)
            curves_created.append(curve_data)
    
    return {
        "message": f"Created {len(curves_created)} yield curves",
        "curves": curves_created,
        "storage_type": "MongoDB" if (MONGODB_AVAILABLE and db_initialized) else "Fallback"
    }

@app.get("/poc/chat")
async def chat_get():
    return {"message": "Chat endpoint active - NEW VERSION DEPLOYED", "status": "ready", "version": "2.0"}

@app.get("/api/test/chat")
async def test_chat():
    """Test endpoint to verify chat functionality is working."""
    return {
        "message": "Chat test endpoint working",
        "status": "success",
        "version": "2.0",
        "features": [
            "Intelligent responses",
            "Runs query",
            "Curves query", 
            "Health check",
            "Help system"
        ]
    }

@app.get("/api/test/mongodb-connection")
async def test_mongodb_connection():
    """Test MongoDB connection and return detailed status."""
    if not MONGODB_AVAILABLE:
        return {
            "status": "error",
            "message": "MongoDB dependencies not available",
            "mongodb_available": False,
            "connection_string_configured": False,
            "database_initialized": False
        }
    
    connection_string = os.getenv("MONGODB_CONNECTION_STRING")
    database_name = os.getenv("MONGODB_DATABASE", "valuation-backend-server")
    
    return {
        "status": "info",
        "mongodb_available": True,
        "connection_string_configured": bool(connection_string),
        "database_name": database_name,
        "database_initialized": db_initialized,
        "connection_string_preview": connection_string[:20] + "..." if connection_string else "Not set",
        "message": "MongoDB status check complete"
    }

@app.post("/poc/chat")
async def chat_post(request: dict = None):
    """Process chat messages and provide intelligent responses."""
    print(f"🔍 Chat endpoint called with request: {request}")
    
    if not request or not request.get("message"):
        return {
            "response": "Hello! I'm your valuation assistant. How can I help you today?",
            "status": "success"
        }
    
    message = request.get("message", "").lower().strip()
    
    # Handle different types of queries
    if any(word in message for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
        return {
            "response": "Hello! I'm your valuation assistant. I can help you with:\n• Analyzing valuation runs\n• Generating sensitivity scenarios\n• Exporting reports\n• IFRS-13 compliance questions\n\nWhat would you like to know?",
            "status": "success"
        }
    
    elif any(word in message for word in ["runs", "valuation", "latest", "show me"]):
        try:
            # Get recent runs
            if MONGODB_AVAILABLE and db_initialized:
                runs = await mongodb_client.get_runs(limit=5)
            else:
                runs = fallback_runs[-5:] if fallback_runs else []
            
            if runs:
                response = f"Here are your recent valuation runs:\n\n"
                for run in runs:
                    response += f"• **{run.get('id', 'Unknown')}** - {run.get('instrument_type', 'Unknown')} ({run.get('currency', 'Unknown')})\n"
                    response += f"  Status: {run.get('status', 'Unknown')}\n"
                    response += f"  PV: ${run.get('pv_base_ccy', 0):,.2f}\n"
                    response += f"  Notional: ${run.get('notional_amount', 0):,.0f}\n\n"
            else:
                response = "No valuation runs found. Would you like me to help you create one?"
            
            return {"response": response, "status": "success"}
        except Exception as e:
            return {"response": f"Sorry, I couldn't retrieve the runs. Error: {str(e)}", "status": "error"}
    
    elif any(word in message for word in ["curves", "yield", "rates"]):
        try:
            # Get available curves
            if MONGODB_AVAILABLE and db_initialized:
                curves = await mongodb_client.get_curves(limit=5)
            else:
                curves = fallback_curves[-5:] if fallback_curves else []
            
            if curves:
                response = "Here are the available yield curves:\n\n"
                for curve in curves:
                    response += f"• **{curve.get('currency', 'Unknown')} {curve.get('type', 'Unknown')}**\n"
                    response += f"  As of: {curve.get('as_of_date', 'Unknown')}\n"
                    response += f"  Nodes: {len(curve.get('nodes', []))} points\n\n"
            else:
                response = "No yield curves available. Would you like me to generate some sample curves?"
            
            return {"response": response, "status": "success"}
        except Exception as e:
            return {"response": f"Sorry, I couldn't retrieve the curves. Error: {str(e)}", "status": "error"}
    
    elif any(word in message for word in ["health", "status", "backend"]):
        try:
            # Get system status
            if MONGODB_AVAILABLE and db_initialized:
                stats = await mongodb_client.get_database_stats()
                response = f"**System Status:** ✅ Healthy\n\n"
                response += f"**Database:** {stats.get('database_type', 'Unknown')}\n"
                response += f"**Total Runs:** {stats.get('total_runs', 0)}\n"
                response += f"**Total Curves:** {stats.get('total_curves', 0)}\n"
                response += f"**Message:** {stats.get('message', 'All systems operational')}"
            else:
                response = "**System Status:** ⚠️ Using fallback storage\n\n"
                response += f"**Runs in memory:** {len(fallback_runs)}\n"
                response += f"**Curves in memory:** {len(fallback_curves)}\n"
                response += "**Note:** MongoDB not configured - using in-memory storage"
            
            return {"response": response, "status": "success"}
        except Exception as e:
            return {"response": f"Sorry, I couldn't check the system status. Error: {str(e)}", "status": "error"}
    
    elif any(word in message for word in ["create", "new", "irs", "swap"]):
        return {
            "response": "To create a new valuation run:\n\n1. Go to the main page\n2. Click 'Create New Run'\n3. Fill in the instrument details\n4. Submit to generate the valuation\n\nI can help you with the analysis once you have a run!",
            "status": "success"
        }
    
    elif any(word in message for word in ["help", "what can you do", "capabilities"]):
        return {
            "response": "I'm your valuation assistant! Here's what I can do:\n\n**📊 Analysis:**\n• Show latest valuation runs\n• Analyze risk metrics\n• Generate sensitivity scenarios\n\n**📈 Data:**\n• Display available yield curves\n• Check system health\n• Export reports\n\n**📋 Compliance:**\n• Answer IFRS-13 questions\n• Explain valuation methodologies\n• Provide regulatory guidance\n\nWhat would you like to explore?",
            "status": "success"
        }
    
    else:
        return {
            "response": f"I understand you're asking about '{message}'. I'm a valuation assistant specialized in financial instruments and IFRS compliance. Could you be more specific about what you'd like to know? For example:\n\n• 'Show me the latest runs'\n• 'What curves are available?'\n• 'Check system health'\n• 'Help me with IFRS compliance'",
            "status": "success"
        }

@app.get("/api/test/mongodb")
async def test_mongodb():
    """Test MongoDB connection and create sample data."""
    if not MONGODB_AVAILABLE:
        return {
            "status": "error",
            "message": "MongoDB dependencies not available",
            "mongodb_available": False
        }
    
    if not db_initialized:
        return {
            "status": "error", 
            "message": "MongoDB not connected",
            "mongodb_connected": False
        }
    
    try:
        # Test connection by creating a test run
        test_run = {
            "id": f"test-run-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "status": "test",
            "instrument_type": "TEST",
            "currency": "USD",
            "notional_amount": 1000.0,
            "as_of_date": datetime.now().strftime('%Y-%m-%d'),
            "pv_base_ccy": 1000.0,
            "test": True,
            "created_at": datetime.now().isoformat()
        }
        
        mongo_id = await mongodb_client.create_run(test_run)
        
        # Get database stats
        stats = await mongodb_client.get_database_stats()
        
        return {
            "status": "success",
            "message": "MongoDB connection working",
            "mongodb_available": True,
            "mongodb_connected": True,
            "test_run_id": mongo_id,
            "database_stats": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"MongoDB test failed: {str(e)}",
            "mongodb_available": True,
            "mongodb_connected": False,
            "error": str(e)
        }

@app.post("/api/test/populate")
async def populate_sample_data():
    """Populate MongoDB with sample data for Data Explorer visibility."""
    if not MONGODB_AVAILABLE or not db_initialized:
        return {
            "status": "error",
            "message": "MongoDB not available",
            "mongodb_available": MONGODB_AVAILABLE,
            "mongodb_connected": db_initialized
        }
    
    try:
        # Create sample runs
        sample_runs = []
        for i in range(3):
            run_data = {
                "id": f"sample-run-{i+1}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "status": "completed",
                "instrument_type": ["IRS", "CCS", "IRS"][i],
                "currency": ["USD", "EUR", "GBP"][i],
                "notional_amount": [1000000, 2000000, 1500000][i],
                "as_of_date": datetime.now().strftime('%Y-%m-%d'),
                "pv_base_ccy": [25000.50, 45000.75, 35000.25][i],
                "spec": {
                    "type": ["IRS", "CCS", "IRS"][i],
                    "ccy": ["USD", "EUR", "GBP"][i],
                    "notional": [1000000, 2000000, 1500000][i],
                    "effective": datetime.now().strftime('%Y-%m-%d'),
                    "maturity": (datetime.now() + timedelta(days=1825)).strftime('%Y-%m-%d'),
                    "fixedRate": [4.25, 3.75, 4.50][i]
                },
                "metadata": {
                    "source": "sample_data",
                    "calculation_method": "enhanced_financial",
                    "created_at": datetime.now().isoformat()
                },
                "created_at": datetime.now().isoformat()
            }
            
            mongo_id = await mongodb_client.create_run(run_data)
            run_data["_id"] = mongo_id
            sample_runs.append(run_data)
        
        # Create sample curves
        sample_curves = []
        for currency in ["USD", "EUR", "GBP"]:
            curve_data = {
                "id": f"{currency}_OIS_{datetime.now().strftime('%Y-%m-%d')}",
                "currency": currency,
                "type": "OIS",
                "as_of_date": datetime.now().strftime('%Y-%m-%d'),
                "nodes": generate_realistic_rates(currency, 0.05),
                "created_at": datetime.now().isoformat()
            }
            
            mongo_id = await mongodb_client.create_curve(curve_data)
            curve_data["_id"] = mongo_id
            sample_curves.append(curve_data)
        
        # Get final database stats
        stats = await mongodb_client.get_database_stats()
        
        return {
            "status": "success",
            "message": "Sample data created successfully",
            "runs_created": len(sample_runs),
            "curves_created": len(sample_curves),
            "database_stats": stats,
            "data_visible_in": "Azure Data Explorer - valuation-backend-server database"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to populate sample data: {str(e)}",
            "error": str(e)
        }

# POC endpoints for advanced functionality

@app.post("/poc/ifrs-ask")
async def ifrs_ask(request: dict = None):
    """Answer IFRS compliance questions."""
    if not request or not request.get("question"):
        return {
            "status": "ABSTAIN",
            "answer": "No question provided",
            "warnings": ["Question is required"]
        }
    
    # Simulate IFRS question answering
    question = request.get("question", "").lower()
    
    if "fair value" in question:
        return {
            "status": "CONFIDENT",
            "answer": "Fair value measurement under IFRS 13 requires using the most appropriate valuation technique for the asset or liability. The fair value hierarchy prioritizes quoted prices in active markets (Level 1), followed by observable inputs (Level 2), and unobservable inputs (Level 3).",
            "citations": [
                {"standard": "IFRS 13", "paragraph": "B5", "section": "Fair Value Hierarchy"}
            ],
            "confidence": 0.85
        }
    elif "impairment" in question:
        return {
            "status": "CONFIDENT", 
            "answer": "IFRS 9 requires entities to recognize expected credit losses (ECL) for financial assets. The ECL model applies a three-stage approach: Stage 1 (12-month ECL), Stage 2 (lifetime ECL), and Stage 3 (lifetime ECL with interest on gross carrying amount).",
            "citations": [
                {"standard": "IFRS 9", "paragraph": "5.5.1", "section": "Expected Credit Losses"}
            ],
            "confidence": 0.90
        }
    else:
        return {
            "status": "CONFIDENT",
            "answer": f"Based on IFRS standards, {request.get('question')} requires careful consideration of the specific circumstances and applicable standards. Please provide more specific details for a targeted response.",
            "citations": [],
            "confidence": 0.60
        }

@app.post("/poc/parse-contract")
async def parse_contract(request: dict = None):
    """Parse contract terms from text."""
    if not request or not request.get("text"):
        return {
            "status": "ABSTAIN",
            "warnings": ["No contract text provided"]
        }
    
    # Simulate contract parsing
    text = request.get("text", "").lower()
    
    # Extract common contract terms
    terms = {}
    if "interest rate" in text or "rate" in text:
        terms["interest_rate"] = "Variable rate based on market conditions"
    if "notional" in text or "principal" in text:
        terms["notional_amount"] = "Amount to be determined"
    if "maturity" in text or "term" in text:
        terms["maturity"] = "Term to be determined"
    if "currency" in text:
        terms["currency"] = "Currency to be determined"
    
    return {
        "status": "CONFIDENT",
        "extracted_terms": terms,
        "confidence": 0.75,
        "warnings": ["This is a simulated response for demonstration purposes"]
    }

@app.post("/poc/explain-run")
async def explain_run(request: dict = None):
    """Explain valuation run results."""
    if not request or not request.get("run_id"):
        return {
            "status": "ABSTAIN",
            "warnings": ["Run ID is required"]
        }
    
    # Simulate run explanation
    return {
        "status": "CONFIDENT",
        "explanation": "This valuation run calculated the present value of the financial instrument using the specified yield curve and market data. The result represents the fair value of the instrument as of the valuation date.",
        "key_factors": [
            "Yield curve interpolation method",
            "Market data quality and timeliness", 
            "Day count conventions applied",
            "Currency conversion rates used"
        ],
        "confidence": 0.80,
        "warnings": ["This is a simulated explanation for demonstration purposes"]
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
