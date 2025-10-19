"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.settings import settings
from app.middleware.audit import AuditMiddleware
from app.middleware.security import RequestSizeLimitMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware
from app.routers import health, ingest, ifrs, feedback, chat, policy, docs, security, monitoring
from app.poc.routers import router as poc_router

# Create FastAPI application
app = FastAPI(
    title=settings.API_NAME,
    description="Valuation Agent Backend API",
    version="0.1.0",
    debug=settings.DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security middleware (order matters)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60, burst_size=10)
app.add_middleware(RequestSizeLimitMiddleware, max_size=10 * 1024 * 1024)  # 10MB
app.add_middleware(AuditMiddleware)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(ingest.router, prefix="/api/v1", tags=["ingest"])
app.include_router(ifrs.router, prefix="/api/v1", tags=["ifrs"])
app.include_router(feedback.router, prefix="/api/v1", tags=["feedback"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(policy.router, prefix="/api/v1", tags=["policy"])
app.include_router(docs.router, prefix="/api/v1", tags=["docs"])
app.include_router(security.router, prefix="/api/v1", tags=["security"])
app.include_router(monitoring.router, prefix="/api/v1", tags=["monitoring"])
app.include_router(poc_router, tags=["poc"])


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "Valuation Agent Backend API",
        "version": "0.1.0",
        "docs": "/docs"
    }
