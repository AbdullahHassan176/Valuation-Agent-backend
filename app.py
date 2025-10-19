import os
from fastapi import FastAPI
from routers import runs, curves, exports, sensitivities, agents, explanations, chat
from settings import get_settings

# Import generated SDK (placeholder for now)
try:
    from sdk import Client, IRSSpec, CCSSpec, RunRequest, RunStatus, PVBreakdown
    sdk_available = True
except ImportError:
    sdk_available = False

app = FastAPI(
    title="Valuation Agent Backend",
    description="Backend orchestrator for Valuation Agent Workspace",
    version="1.0.0"
)

# Include routers
app.include_router(runs.router)
app.include_router(curves.router)
app.include_router(exports.router)
app.include_router(sensitivities.router)
app.include_router(agents.router)
app.include_router(explanations.router)
app.include_router(chat.router)

@app.get("/healthz")
def health_check():
    settings = get_settings()
    return {
        "ok": True, 
        "service": "backend", 
        "api_base_url": settings.api_base_url,
        "sdk_available": sdk_available
    }
