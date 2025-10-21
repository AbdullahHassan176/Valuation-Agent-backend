#!/usr/bin/env python3
"""
Ultra-minimal FastAPI app for Azure deployment
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
import aiohttp
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

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
        if mongodb_client:
            print("🔍 Initializing MongoDB connection...")
            db_initialized = await mongodb_client.connect()
            if db_initialized:
                print("✅ MongoDB database initialized successfully")
            else:
                print("⚠️ MongoDB connection failed - using fallback storage")
        else:
            print("⚠️ MongoDB not configured - using fallback storage")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
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
                    print("❌ No MongoDB connection string provided")
                    return False
                    
                print(f"🔍 Connecting to MongoDB...")
                
                # For Azure Cosmos DB, use specific connection parameters
                if "cosmos.azure.com" in self.connection_string or len(self.connection_string) > 100:
                    print("🔍 Detected Azure Cosmos DB - using optimized connection parameters")
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
                print(f"✅ Connected to MongoDB database: {self.database_name}")
                return True
            except Exception as e:
                print(f"❌ MongoDB connection failed: {e}")
                return False
                
        async def create_run(self, run_data: Dict[str, Any]) -> str:
            """Create a new run in MongoDB."""
            try:
                run_data["created_at"] = datetime.now()
                result = await self.db.runs.insert_one(run_data)
                return str(result.inserted_id)
            except Exception as e:
                print(f"❌ Error creating run: {e}")
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
                print(f"❌ Error getting runs: {e}")
                return []
                
        async def create_curve(self, curve_data: Dict[str, Any]) -> str:
            """Create a new curve in MongoDB."""
            try:
                curve_data["created_at"] = datetime.now()
                result = await self.db.curves.insert_one(curve_data)
                return str(result.inserted_id)
            except Exception as e:
                print(f"❌ Error creating curve: {e}")
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
                print(f"❌ Error getting curves: {e}")
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
                print(f"❌ Error getting database stats: {e}")
                return {"error": str(e)}
                
        async def disconnect(self):
            """Disconnect from MongoDB."""
            if self.client:
                self.client.close()
    
    # Initialize MongoDB client
    if USE_MONGODB and MONGODB_CONNECTION_STRING:
        mongodb_client = MongoDBClient()
        print("✅ MongoDB client initialized")
    else:
        print("⚠️ MongoDB not configured - using fallback storage")
        
except ImportError as e:
    print(f"⚠️ MongoDB libraries not available: {e}")
    print("⚠️ Using fallback storage")
    mongodb_client = None

# In-memory storage (fallback)
fallback_runs = [
    {
        "id": "run-001",
        "asOf": "2024-01-15",
        "spec": {
            "ccy": "USD",
            "notional": 10000000,
            "fixedRate": 0.035,
            "effective": "2024-01-01",
            "maturity": "2029-01-01"
        },
        "pv_base_ccy": 125000.50,
        "status": "completed",
        "created_at": datetime.now().isoformat()
    },
    {
        "id": "run-002", 
        "asOf": "2024-01-15",
        "spec": {
            "ccy": "EUR",
            "notional": 5000000,
            "fixedRate": 0.025,
            "effective": "2024-01-01",
            "maturity": "2027-01-01"
        },
        "pv_base_ccy": -75000.25,
        "status": "completed",
        "created_at": datetime.now().isoformat()
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

# Runs endpoints
@app.get("/api/valuation/runs")
async def get_runs():
    """Get all valuation runs."""
    try:
        if db_initialized and mongodb_client:
            print("📊 Fetching runs from MongoDB...")
            runs = await mongodb_client.get_runs()
            print(f"✅ Retrieved {len(runs)} runs from MongoDB")
            return runs
        else:
            print("📊 Using fallback runs storage")
            return fallback_runs
    except Exception as e:
        print(f"❌ Error getting runs: {e}")
        return fallback_runs

@app.post("/api/valuation/runs")
async def create_run(request: dict):
    """Create a new valuation run."""
    try:
        new_run = {
            "id": f"run-{len(fallback_runs) + 1:03d}",
            "asOf": request.get("asOf", datetime.now().strftime("%Y-%m-%d")),
            "spec": request.get("spec", {}),
            "pv_base_ccy": 100000.0,  # Mock PV
            "status": "completed",
            "created_at": datetime.now().isoformat()
        }
        
        if db_initialized and mongodb_client:
            print("💾 Storing run in MongoDB...")
            mongo_id = await mongodb_client.create_run(new_run)
            if mongo_id:
                new_run["mongo_id"] = mongo_id
                print(f"✅ Run stored in MongoDB with ID: {mongo_id}")
            else:
                print("⚠️ Failed to store in MongoDB, using fallback")
                fallback_runs.append(new_run)
        else:
            print("💾 Storing run in fallback storage...")
            fallback_runs.append(new_run)
            
        return new_run
    except Exception as e:
        print(f"❌ Error creating run: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Curves endpoint
@app.get("/api/valuation/curves")
async def get_curves():
    """Get all yield curves."""
    try:
        if db_initialized and mongodb_client:
            print("📈 Fetching curves from MongoDB...")
            curves = await mongodb_client.get_curves()
            print(f"✅ Retrieved {len(curves)} curves from MongoDB")
            return curves if curves else fallback_curves
        else:
            print("📈 Using fallback curves storage")
            return fallback_curves
    except Exception as e:
        print(f"❌ Error getting curves: {e}")
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
                    print(f"❌ Groq API error: {response.status}")
                    return None
                    
    except Exception as e:
        print(f"❌ Groq LLM error: {e}")
        return None

# Chat endpoint
@app.post("/poc/chat")
async def chat_endpoint(request: dict):
    """AI chat endpoint with Groq LLM integration."""
    message = request.get("message", "")
    print(f"💬 Chat message received: {message[:50]}...")
    
    # Try Groq LLM first
    llm_response = await call_groq_llm(message)
    
    if llm_response:
        print(f"✅ Groq LLM response generated")
        return {
            "response": llm_response,
            "llm_powered": True,
            "version": "1.0.0",
            "model": GROQ_MODEL,
            "timestamp": datetime.now().isoformat()
        }
    else:
        print(f"⚠️ Using fallback response")
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
    try:
        if db_initialized and mongodb_client:
            print("📊 Getting MongoDB database status...")
            stats = await mongodb_client.get_database_stats()
            return stats
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
        print(f"❌ Error getting database status: {e}")
        return {
            "database_type": "error",
            "status": "error",
            "error": str(e)
        }

# MongoDB test endpoint
@app.get("/api/test/mongodb")
async def test_mongodb():
    """Test MongoDB connection and create a test run."""
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
        print(f"❌ MongoDB test error: {e}")
        return {
            "mongodb_available": False,
            "error": str(e),
            "connection_string_present": bool(MONGODB_CONNECTION_STRING),
            "use_mongodb": USE_MONGODB
        }

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

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
