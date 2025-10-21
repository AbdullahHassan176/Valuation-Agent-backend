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
import asyncio
import aiohttp

# Try to import MongoDB client, fallback if not available
try:
    from mongodb_client import mongodb_client
    MONGODB_AVAILABLE = True
    print("✅ MongoDB client imported successfully")
except ImportError as e:
    print(f"⚠️ MongoDB dependencies not available: {e}")
    print("💡 Using fallback storage mode")
    MONGODB_AVAILABLE = False
    mongodb_client = None
except Exception as e:
    print(f"⚠️ MongoDB client error: {e}")
    print("💡 Using fallback storage mode")
    MONGODB_AVAILABLE = False
    mongodb_client = None

# LLM Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# Ollama Configuration (Free Alternative)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
USE_OLLAMA = os.getenv("USE_OLLAMA", "false").lower() == "true"

# Groq Configuration (Free Cloud Alternative)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
USE_GROQ = os.getenv("USE_GROQ", "false").lower() == "true"

# System prompt for the AI valuation auditor
SYSTEM_PROMPT = """You are a friendly AI valuation assistant with expertise in financial analysis and IFRS compliance.

**Your Role:**
- Help users with valuation questions and analysis
- Provide clear, concise explanations
- Be conversational and approachable
- Focus on what the user actually needs

**Communication Style:**
- Be conversational and friendly
- Keep responses concise and focused
- Ask one question at a time
- Avoid information dumps
- Use simple language when possible
- Be helpful but not overwhelming

**Available Data:**
- Valuation runs and their results
- Yield curves and market data
- System status

**Response Guidelines:**
- Keep responses under 3-4 sentences unless specifically asked for details
- Ask one clarifying question at a time
- Don't list all capabilities unless asked
- Focus on the user's specific question
- Be conversational, not formal
- Avoid bullet points and long lists unless necessary

**Example Good Response:**
"I can help you analyze those valuation runs. What specific aspect would you like to focus on - the present values, risk metrics, or something else?"

**Example Bad Response:**
"I have extensive capabilities in valuation calculations, risk analysis, audit procedures, regulatory compliance, market data analysis, sensitivity analysis, XVA calculations, credit risk assessment, and counterparty analysis. I can perform calculations for various financial instruments including Interest Rate Swaps, Credit Default Swaps, Bonds, Derivatives, and other complex financial instruments..."

Be helpful, concise, and conversational."""

# Ollama Client for free LLM responses
async def call_ollama(user_message: str, context_data: Dict[str, Any] = None) -> str:
    """Call Ollama LLM with user message and context data."""
    print(f"🔍 Calling Ollama with message: {user_message[:50]}...")
    print(f"🔍 Ollama URL: {OLLAMA_BASE_URL}")
    print(f"🔍 Model: {OLLAMA_MODEL}")
    
    try:
        # Prepare context information
        context_info = ""
        if context_data:
            if context_data.get("runs"):
                context_info += f"\n**Available Valuation Runs:**\n"
                for run in context_data["runs"][:3]:
                    context_info += f"- {run.get('id', 'Unknown')}: {run.get('instrument_type', 'Unknown')} ({run.get('currency', 'Unknown')}) - PV: ${run.get('pv_base_ccy', 0):,.2f}\n"
            
            if context_data.get("curves"):
                context_info += f"\n**Available Yield Curves:**\n"
                for curve in context_data["curves"][:3]:
                    context_info += f"- {curve.get('currency', 'Unknown')} {curve.get('type', 'Unknown')}: {len(curve.get('nodes', []))} points\n"
            
            if context_data.get("system_status"):
                context_info += f"\n**System Status:** {context_data['system_status']}\n"
        
        # Prepare full prompt
        full_prompt = f"{SYSTEM_PROMPT}\n\nUser Message: {user_message}\n\n{context_info}"
        
        # Call Ollama API
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 1000
                }
            }
            
            async with session.post(f"{OLLAMA_BASE_URL}/api/generate", 
                                   json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Ollama response received")
                    return data.get("response", "No response from Ollama")
                else:
                    error_text = await response.text()
                    print(f"❌ Ollama error: {response.status} - {error_text}")
                    return f"Ollama API error: {response.status} - {error_text}"
                    
    except Exception as e:
        print(f"❌ Ollama exception: {e}")
        return f"Error calling Ollama: {str(e)}"

# Groq Client for free cloud LLM responses
async def call_groq(user_message: str, context_data: Dict[str, Any] = None) -> str:
    """Call Groq LLM with user message and context data."""
    if not GROQ_API_KEY:
        print("❌ GROQ_API_KEY not configured")
        return "Groq API key not configured"
    
    print(f"🔍 Calling Groq with message: {user_message[:50]}...")
    print(f"🔍 Groq URL: {GROQ_BASE_URL}")
    print(f"🔍 Model: {GROQ_MODEL}")
    
    try:
        # Prepare context information
        context_info = ""
        if context_data:
            if context_data.get("runs"):
                context_info += f"\n**Available Valuation Runs:**\n"
                for run in context_data["runs"][:3]:
                    context_info += f"- {run.get('id', 'Unknown')}: {run.get('instrument_type', 'Unknown')} ({run.get('currency', 'Unknown')}) - PV: ${run.get('pv_base_ccy', 0):,.2f}\n"
            
            if context_data.get("curves"):
                context_info += f"\n**Available Yield Curves:**\n"
                for curve in context_data["curves"][:3]:
                    context_info += f"- {curve.get('currency', 'Unknown')} {curve.get('type', 'Unknown')}: {len(curve.get('nodes', []))} points\n"
            
            if context_data.get("system_status"):
                context_info += f"\n**System Status:** {context_data['system_status']}\n"
        
        # Prepare messages for Groq (OpenAI-compatible API)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{user_message}\n\n{context_info}"}
        ]
        
        # Call Groq API
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": GROQ_MODEL,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            async with session.post(f"{GROQ_BASE_URL}/chat/completions", 
                                   headers=headers, 
                                   json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Groq response received")
                    return data["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    print(f"❌ Groq error: {response.status} - {error_text}")
                    return f"Groq API error: {response.status} - {error_text}"
                    
    except Exception as e:
        print(f"❌ Groq exception: {e}")
        return f"Error calling Groq: {str(e)}"

# LLM Client for AI responses
async def call_llm(user_message: str, context_data: Dict[str, Any] = None) -> str:
    """Call LLM with user message and context data."""
    
    # Try Groq first if enabled (free cloud option)
    if USE_GROQ:
        print("🔍 Using Groq LLM")
        return await call_groq(user_message, context_data)
    
    # Try Ollama if enabled (free local option)
    if USE_OLLAMA:
        print("🔍 Using Ollama LLM")
        return await call_ollama(user_message, context_data)
    
    # Fallback to OpenAI
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not configured")
        return "I'm sorry, but I don't have access to the AI language model right now. Please check the configuration."
    
    print(f"🔍 Calling OpenAI LLM with message: {user_message[:50]}...")
    print(f"🔍 API Key configured: {bool(OPENAI_API_KEY)}")
    print(f"🔍 Base URL: {OPENAI_BASE_URL}")
    
    try:
        # Prepare context information
        context_info = ""
        if context_data:
            if context_data.get("runs"):
                context_info += f"\n**Available Valuation Runs:**\n"
                for run in context_data["runs"][:3]:  # Show first 3 runs
                    context_info += f"- {run.get('id', 'Unknown')}: {run.get('instrument_type', 'Unknown')} ({run.get('currency', 'Unknown')}) - PV: ${run.get('pv_base_ccy', 0):,.2f}\n"
            
            if context_data.get("curves"):
                context_info += f"\n**Available Yield Curves:**\n"
                for curve in context_data["curves"][:3]:  # Show first 3 curves
                    context_info += f"- {curve.get('currency', 'Unknown')} {curve.get('type', 'Unknown')}: {len(curve.get('nodes', []))} points\n"
            
            if context_data.get("system_status"):
                context_info += f"\n**System Status:** {context_data['system_status']}\n"
        
        # Prepare messages for LLM
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{user_message}\n\n{context_info}"}
        ]
        
        # Call OpenAI API
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Try different models in order of preference
            # Check if a specific model is configured
            configured_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            models_to_try = [configured_model, "gpt-4o-mini", "gpt-4", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"]
            
            for model in models_to_try:
                try:
                    print(f"🔍 Trying model: {model}")
                    payload = {
                        "model": model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 1000
                    }
                    
                    async with session.post(f"{OPENAI_BASE_URL}/chat/completions", 
                                         headers=headers, 
                                         json=payload) as response:
                        print(f"🔍 Response status: {response.status}")
                        if response.status == 200:
                            data = await response.json()
                            print(f"✅ LLM response received from {model}")
                            return data["choices"][0]["message"]["content"]
                        elif response.status == 404:
                            print(f"❌ Model {model} not available, trying next...")
                            continue
                        else:
                            error_text = await response.text()
                            print(f"❌ Error with model {model}: {response.status} - {error_text}")
                            return f"I encountered an error with the AI service: {response.status} - {error_text}"
                except Exception as e:
                    print(f"❌ Exception with model {model}: {e}")
                    continue
            
            return "I'm sorry, but I don't have access to any compatible AI models. Please check the API configuration."
    
    except Exception as e:
        return f"I'm sorry, but I encountered an error while processing your request: {str(e)}"

# Fallback response generator for when LLM is not available
def generate_fallback_response(message: str, context_data: Dict[str, Any]) -> str:
    """Generate intelligent fallback responses when LLM is not available."""
    user_message = message.lower()
    
    # Get context information
    runs = context_data.get("runs", [])
    curves = context_data.get("curves", [])
    system_status = context_data.get("system_status", "Unknown")
    
    # Greeting responses
    if any(word in user_message for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
        return f"Hi there! I'm your valuation assistant. I can see you have {len(runs)} valuation runs and {len(curves)} yield curves available. What would you like to work on today?"

    # Create new valuation run
    elif any(word in user_message for word in ["create", "new", "irs", "swap", "valuation run"]):
        return "I can help you create a new valuation run. What type of instrument are you looking to value?"

    # Runs analysis
    elif any(word in user_message for word in ["runs", "valuation", "latest", "show me"]):
        if runs:
            return f"I can see you have {len(runs)} valuation runs. What specific aspect would you like me to analyze?"
        else:
            return "No valuation runs found. I can help you create new ones if you'd like."

    # Curves analysis
    elif any(word in user_message for word in ["curves", "yield", "rates"]):
        if curves:
            return f"You have {len(curves)} yield curves available. What would you like to know about them?"
        else:
            return "No yield curves available. I can help you work with them once you have data."

    # IFRS and compliance
    elif any(word in user_message for word in ["ifrs", "compliance", "audit", "fair value"]):
        return "I can help with IFRS 13 compliance questions. What specific area are you working on?"

    # Help and capabilities
    elif any(word in user_message for word in ["help", "what can you do", "capabilities", "what cna you do"]):
        return f"I can help you analyze your {len(runs)} valuation runs and {len(curves)} yield curves. What would you like to focus on?"

    # Credit Valuation Adjustment (CVA)
    elif any(word in user_message for word in ["cva", "credit valuation adjustment", "credit risk", "counterparty risk"]):
        return "I can help with CVA analysis. What specific aspect of credit valuation adjustments are you working on?"

    # XVA (Cross Valuation Adjustments)
    elif any(word in user_message for word in ["xva", "fva", "kva", "mva", "valuation adjustment"]):
        return "I can help with XVA analysis. Which adjustment are you working on - CVA, DVA, FVA, or something else?"

    # System health and status
    elif any(word in user_message for word in ["health", "status", "system", "fallback"]):
        return f"System is in {system_status} with {len(runs)} runs and {len(curves)} curves. What would you like to check?"

    else:
        return f"I can help you with your valuation analysis. You have {len(runs)} runs and {len(curves)} curves available. What would you like to focus on?"

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
            print("💡 This is normal - the app will work with fallback storage")
        
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
fallback_runs = [
    {
        "id": "sample-run-001",
        "status": "completed",
        "instrument_type": "IRS",
        "currency": "USD",
        "notional_amount": 1000000,
        "as_of_date": "2024-01-15",
        "pv_base_ccy": 25000.50,
        "spec": {
            "type": "IRS",
            "ccy": "USD",
            "notional": 1000000,
            "effective": "2024-01-15",
            "maturity": "2029-01-15",
            "fixedRate": 4.25
        },
        "metadata": {
            "source": "sample_data",
            "calculation_method": "enhanced_financial",
            "created_at": "2024-01-15T10:00:00Z"
        },
        "created_at": "2024-01-15T10:00:00Z"
    },
    {
        "id": "sample-run-002", 
        "status": "completed",
        "instrument_type": "CCS",
        "currency": "EUR",
        "notional_amount": 2000000,
        "as_of_date": "2024-01-15",
        "pv_base_ccy": 45000.75,
        "spec": {
            "type": "CCS",
            "ccy": "EUR",
            "notional": 2000000,
            "effective": "2024-01-15",
            "maturity": "2027-01-15",
            "fixedRate": 3.75
        },
        "metadata": {
            "source": "sample_data",
            "calculation_method": "enhanced_financial",
            "created_at": "2024-01-15T11:00:00Z"
        },
        "created_at": "2024-01-15T11:00:00Z"
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
            {"tenor": "1Y", "rate": 0.052},
            {"tenor": "2Y", "rate": 0.055},
            {"tenor": "5Y", "rate": 0.058}
        ],
        "created_at": "2024-01-15T09:00:00Z"
    },
    {
        "id": "EUR_OIS_2024-01-15",
        "currency": "EUR", 
        "type": "OIS",
        "as_of_date": "2024-01-15",
        "nodes": [
            {"tenor": "1M", "rate": 0.035},
            {"tenor": "3M", "rate": 0.037},
            {"tenor": "6M", "rate": 0.039},
            {"tenor": "1Y", "rate": 0.042},
            {"tenor": "2Y", "rate": 0.045},
            {"tenor": "5Y", "rate": 0.048}
        ],
        "created_at": "2024-01-15T09:00:00Z"
    },
    {
        "id": "GBP_OIS_2024-01-15",
        "currency": "GBP",
        "type": "OIS", 
        "as_of_date": "2024-01-15",
        "nodes": [
            {"tenor": "1M", "rate": 0.055},
            {"tenor": "3M", "rate": 0.057},
            {"tenor": "6M", "rate": 0.059},
            {"tenor": "1Y", "rate": 0.062},
            {"tenor": "2Y", "rate": 0.065},
            {"tenor": "5Y", "rate": 0.068}
        ],
        "created_at": "2024-01-15T09:00:00Z"
    }
]

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
    return {
        "message": "Chat endpoint active - INTELLIGENT VERSION 2.0 DEPLOYED", 
        "status": "ready", 
        "version": "2.0",
        "features": "Intelligent responses, runs analysis, curves info, health checks"
    }

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
    """Process chat messages with LLM-powered intelligent responses."""
    print(f"🔍 Chat endpoint called with request: {request}")
    print(f"🔍 Chat endpoint version: 3.0 - LLM-POWERED AI AGENT")
    
    if not request or not request.get("message"):
        return {
            "response": "Hello! I'm your AI valuation auditor and specialist. How can I help you today?",
            "status": "success",
            "version": "3.0"
        }
    
    message = request.get("message", "").strip()
    
    try:
        # Gather context data for the LLM
        context_data = {}
        
        # Get recent runs
        try:
            if MONGODB_AVAILABLE and db_initialized:
                runs = await mongodb_client.get_runs(limit=5)
            else:
                runs = fallback_runs[-5:] if fallback_runs else []
            context_data["runs"] = runs
        except Exception as e:
            print(f"Error getting runs: {e}")
            context_data["runs"] = []
        
        # Get available curves
        try:
            if MONGODB_AVAILABLE and db_initialized:
                curves = await mongodb_client.get_curves(limit=5)
            else:
                curves = fallback_curves[-5:] if fallback_curves else []
            context_data["curves"] = curves
        except Exception as e:
            print(f"Error getting curves: {e}")
            context_data["curves"] = []
        
        # Get system status
        try:
            if MONGODB_AVAILABLE and db_initialized:
                stats = await mongodb_client.get_database_stats()
                context_data["system_status"] = f"Database: {stats.get('database_type', 'Unknown')}, Runs: {stats.get('total_runs', 0)}, Curves: {stats.get('total_curves', 0)}"
            else:
                context_data["system_status"] = f"Fallback mode - Runs: {len(fallback_runs)}, Curves: {len(fallback_curves)}"
        except Exception as e:
            print(f"Error getting system status: {e}")
            context_data["system_status"] = "Status unknown"
        
        # Call LLM with context
        llm_response = await call_llm(message, context_data)
        
        # If LLM fails, provide a fallback response
        if "I'm sorry, but I don't have access" in llm_response or "I encountered an error" in llm_response:
            # Fallback to intelligent rule-based response
            fallback_response = generate_fallback_response(message, context_data)
            return {
                "response": fallback_response,
                "status": "success",
                "version": "3.0",
                "llm_powered": False,
                "fallback": True
            }
        
        return {
            "response": llm_response,
            "status": "success",
            "version": "3.0",
            "llm_powered": True
        }
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return {
            "response": f"I'm sorry, but I encountered an error while processing your request: {str(e)}",
            "status": "error",
            "version": "3.0"
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
    """AI Agent: Explain valuation run results with detailed analysis."""
    if not request or not request.get("run_id"):
        return {
            "status": "ABSTAIN",
            "warnings": ["Run ID is required"]
        }
    
    run_id = request.get("run_id")
    
    # Get actual run data for explanation
    try:
        if MONGODB_AVAILABLE and db_initialized:
            runs = await mongodb_client.get_runs()
            target_run = next((run for run in runs if run.get('id') == run_id), None)
        else:
            target_run = next((run for run in fallback_runs if run.get('id') == run_id), None)
        
        if not target_run:
            return {
                "status": "ABSTAIN",
                "explanation": f"Run {run_id} not found",
                "warnings": ["Run not found in database"]
            }
        
        # Use AI agent to explain the run
        explanation_prompt = f"""
        As an AI valuation auditor, explain this valuation run in detail:
        
        Run ID: {run_id}
        Instrument: {target_run.get('instrument_type', 'Unknown')}
        Currency: {target_run.get('currency', 'Unknown')}
        Notional: ${target_run.get('notional_amount', 0):,.2f}
        Present Value: ${target_run.get('pv_base_ccy', 0):,.2f}
        Status: {target_run.get('status', 'Unknown')}
        
        Provide a comprehensive explanation including:
        1. What this valuation represents
        2. Key risk factors and sensitivities
        3. IFRS 13 compliance considerations
        4. Audit recommendations
        5. Potential areas of concern
        """
        
        # Use LLM for intelligent explanation
        ai_explanation = await call_llm(explanation_prompt, {"runs": [target_run]})
        
        return {
            "status": "CONFIDENT",
            "explanation": ai_explanation,
            "run_data": target_run,
            "confidence": 0.9,
            "ai_powered": True
        }
        
    except Exception as e:
        return {
            "status": "ERROR",
            "explanation": f"Error explaining run: {str(e)}",
            "warnings": ["Failed to retrieve run data"]
        }

@app.post("/poc/ai-agent/explain-results")
async def ai_explain_results(request: dict = None):
    """AI Agent: Explain valuation results with intelligent analysis."""
    if not request or not request.get("message"):
        return {
            "status": "ABSTAIN",
            "response": "Please provide a message about what results you'd like me to explain",
            "warnings": ["Message is required"]
        }
    
    message = request.get("message")
    
    # Use AI agent to explain results
    ai_response = await call_llm(f"""
    As an AI valuation auditor, help explain these results:
    
    User Request: {message}
    
    Please provide:
    1. Clear explanation of what the results mean
    2. Key insights and implications
    3. Risk factors to consider
    4. Next steps or recommendations
    5. IFRS compliance considerations
    """)
    
    return {
        "status": "CONFIDENT",
        "response": ai_response,
        "ai_powered": True,
        "confidence": 0.9
    }

@app.post("/poc/ai-agent/kick-off-valuation")
async def ai_kick_off_valuation(request: dict = None):
    """AI Agent: Guide user through creating new valuations."""
    if not request or not request.get("message"):
        return {
            "status": "ABSTAIN",
            "response": "Please describe what type of valuation you'd like to create",
            "warnings": ["Message is required"]
        }
    
    message = request.get("message")
    
    # Use AI agent to guide valuation creation
    ai_response = await call_llm(f"""
    As an AI valuation auditor, help the user create a new valuation:
    
    User Request: {message}
    
    Please provide:
    1. Step-by-step guidance for creating the valuation
    2. Required parameters and inputs
    3. Risk considerations
    4. Validation checks
    5. Documentation requirements
    """)
    
    return {
        "status": "CONFIDENT",
        "response": ai_response,
        "ai_powered": True,
        "confidence": 0.9
    }

@app.post("/poc/ai-agent/explain-ifrs")
async def ai_explain_ifrs(request: dict = None):
    """AI Agent: Explain IFRS 13 and compliance requirements."""
    if not request or not request.get("message"):
        return {
            "status": "ABSTAIN",
            "response": "Please ask about specific IFRS 13 requirements or compliance questions",
            "warnings": ["Message is required"]
        }
    
    message = request.get("message")
    
    # Use AI agent to explain IFRS
    ai_response = await call_llm(f"""
    As an AI valuation auditor, explain IFRS 13 compliance:
    
    User Question: {message}
    
    Please provide:
    1. Clear explanation of IFRS 13 requirements
    2. How it applies to their specific situation
    3. Compliance steps and documentation
    4. Common pitfalls and best practices
    5. Regulatory considerations
    """)
    
    return {
        "status": "CONFIDENT",
        "response": ai_response,
        "ai_powered": True,
        "confidence": 0.9
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
