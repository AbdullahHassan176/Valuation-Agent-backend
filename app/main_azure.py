"""FastAPI application entry point for Azure deployment."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.settings import settings

# Create FastAPI application
app = FastAPI(
    title="Valuation Agent Backend API",
    description="Valuation Agent Backend API for Azure",
    version="0.1.0",
    debug=False
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "valuation-backend"}

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Valuation Agent Backend API", "status": "running"}

# Include routers
try:
    from app.routers import health, chat
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(chat.router, prefix="/api", tags=["chat"])
except ImportError as e:
    print(f"Warning: Could not import some routers: {e}")

# Include PoC routers
try:
    from app.poc.routers import router as poc_router
    app.include_router(poc_router, prefix="/api", tags=["poc"])
except ImportError as e:
    print(f"Warning: Could not import PoC router: {e}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
