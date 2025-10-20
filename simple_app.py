#!/usr/bin/env python3
"""
Simple FastAPI backend for Azure App Service
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any

# Initialize in-memory database
def init_database():
    """Initialize SQLite database for storing runs and data."""
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # Create runs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            instrument_type TEXT,
            currency TEXT,
            notional_amount REAL,
            as_of_date TEXT,
            created_at TEXT,
            completed_at TEXT,
            pv_base_ccy REAL,
            metadata TEXT
        )
    ''')
    
    # Create curves table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS curves (
            id TEXT PRIMARY KEY,
            currency TEXT NOT NULL,
            curve_type TEXT NOT NULL,
            as_of_date TEXT NOT NULL,
            nodes TEXT NOT NULL,
            created_at TEXT
        )
    ''')
    
    conn.commit()
    return conn

# Initialize database
db_conn = init_database()

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

@app.get("/api/valuation/runs")
async def get_runs():
    """Get all valuation runs from database."""
    cursor = db_conn.cursor()
    cursor.execute('SELECT * FROM runs ORDER BY created_at DESC')
    rows = cursor.fetchall()
    
    runs = []
    for row in rows:
        runs.append({
            "id": row[0],
            "status": row[1],
            "instrument_type": row[2],
            "currency": row[3],
            "notional_amount": row[4],
            "as_of_date": row[5],
            "created_at": row[6],
            "completed_at": row[7],
            "pv_base_ccy": row[8],
            "metadata": json.loads(row[9]) if row[9] else {}
        })
    
    return runs

@app.post("/api/valuation/runs")
async def create_run(request: dict = None):
    """Create a new valuation run."""
    run_id = f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    current_time = datetime.now().isoformat()
    
    # Extract data from request
    instrument_type = "IRS"  # Default
    currency = "USD"  # Default
    notional_amount = 1000000.0  # Default
    as_of_date = datetime.now().strftime('%Y-%m-%d')
    
    if request:
        instrument_type = request.get("instrument_type", instrument_type)
        currency = request.get("currency", currency)
        notional_amount = request.get("notional_amount", notional_amount)
        as_of_date = request.get("as_of_date", as_of_date)
    
    # Calculate realistic PV (simplified)
    pv_base_ccy = notional_amount * (0.95 + (hash(run_id) % 100) / 1000)  # Simulate realistic PV
    
    # Insert into database
    cursor = db_conn.cursor()
    cursor.execute('''
        INSERT INTO runs (id, status, instrument_type, currency, notional_amount, 
                         as_of_date, created_at, pv_base_ccy, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (run_id, "completed", instrument_type, currency, notional_amount, 
          as_of_date, current_time, pv_base_ccy, json.dumps({"source": "backend"})))
    
    db_conn.commit()
    
    return {
        "message": "Run created successfully",
        "status": "success",
        "id": run_id,
        "pv_base_ccy": pv_base_ccy
    }

@app.get("/poc/chat")
async def chat_get():
    return {"message": "Chat endpoint active", "status": "ready"}

@app.post("/poc/chat")
async def chat_post():
    return {"response": "Chat endpoint working", "status": "success"}

# POC endpoints for advanced functionality
@app.get("/api/valuation/curves")
async def get_curves():
    """Get available yield curves from database."""
    cursor = db_conn.cursor()
    cursor.execute('SELECT * FROM curves ORDER BY created_at DESC')
    rows = cursor.fetchall()
    
    curves = []
    for row in rows:
        curves.append({
            "id": row[0],
            "currency": row[1],
            "type": row[2],
            "as_of": row[3],
            "nodes": json.loads(row[4]) if row[4] else [],
            "created_at": row[5]
        })
    
    # If no curves in database, add some sample curves
    if not curves:
        sample_curves = [
            {
                "id": "USD_OIS_2024-01-15",
                "currency": "USD",
                "type": "OIS",
                "as_of": "2024-01-15",
                "nodes": [
                    {"tenor": "1M", "rate": 0.0525},
                    {"tenor": "3M", "rate": 0.0530},
                    {"tenor": "6M", "rate": 0.0535},
                    {"tenor": "1Y", "rate": 0.0540},
                    {"tenor": "2Y", "rate": 0.0545},
                    {"tenor": "5Y", "rate": 0.0550}
                ],
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "EUR_OIS_2024-01-15",
                "currency": "EUR",
                "type": "OIS",
                "as_of": "2024-01-15",
                "nodes": [
                    {"tenor": "1M", "rate": 0.0325},
                    {"tenor": "3M", "rate": 0.0330},
                    {"tenor": "6M", "rate": 0.0335},
                    {"tenor": "1Y", "rate": 0.0340},
                    {"tenor": "2Y", "rate": 0.0345},
                    {"tenor": "5Y", "rate": 0.0350}
                ],
                "created_at": datetime.now().isoformat()
            }
        ]
        
        # Insert sample curves into database
        for curve in sample_curves:
            cursor.execute('''
                INSERT INTO curves (id, currency, curve_type, as_of_date, nodes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (curve["id"], curve["currency"], curve["type"], curve["as_of"], 
                  json.dumps(curve["nodes"]), curve["created_at"]))
        
        db_conn.commit()
        curves = sample_curves
    
    return {
        "curves": curves,
        "total_curves": len(curves),
        "message": "Available yield curves for valuation"
    }

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
