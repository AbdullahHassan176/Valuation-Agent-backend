"""Health check endpoints."""

from fastapi import APIRouter, Depends
from app.settings import Settings, get_settings

router = APIRouter()


@router.get("/healthz")
async def health_check(settings: Settings = Depends(get_settings)) -> dict:
    """Health check endpoint."""
    return {
        "ok": True,
        "service": settings.API_NAME,
        "environment": settings.ENVIRONMENT
    }
