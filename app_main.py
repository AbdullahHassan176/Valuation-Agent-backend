#!/usr/bin/env python3
"""
Main FastAPI application with database integration.
"""

import os
import sys
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import database and routers
from app.database.connection import db_manager
from app.routers.valuation import router as valuation_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Valuation Agent Backend...")
    try:
        await db_manager.connect()
        logger.info("✅ Database connected successfully")
    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        # Continue without database for now
    
    yield
    
    # Shutdown
    logger.info("Shutting down Valuation Agent Backend...")
    await db_manager.disconnect()
    logger.info("✅ Database disconnected")

# Create FastAPI application
app = FastAPI(
    title="Valuation Agent Backend API",
    description="Backend API for financial valuation and risk management",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(valuation_router)

# Health check endpoint
@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        db_status = "connected" if db_manager.db else "disconnected"
        
        return {
            "status": "healthy",
            "service": "valuation-backend",
            "version": "1.0.0",
            "database": db_status,
            "timestamp": os.environ.get("TIMESTAMP", "unknown")
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Valuation Agent Backend API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/healthz"
    }

# Simple endpoints for testing
@app.get("/api/test")
async def test_endpoint():
    """Test endpoint."""
    return {
        "message": "API is working",
        "database": "connected" if db_manager.db else "disconnected"
    }

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment
    port = int(os.environ.get("PORT", 8000))
    
    # Run the application
    uvicorn.run(
        "app_main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False
    )




