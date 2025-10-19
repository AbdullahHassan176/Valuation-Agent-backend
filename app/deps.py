"""Dependency injection for security and authentication."""

from typing import Optional
from fastapi import HTTPException, Depends, Header
from app.settings import get_settings, Settings


def get_api_key(settings: Settings = Depends(get_settings)) -> Optional[str]:
    """Get API key from settings.
    
    Returns:
        API key if configured, None otherwise
    """
    return getattr(settings, 'API_KEY', None)


def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings)
) -> bool:
    """Verify API key from request header.
    
    Args:
        x_api_key: API key from X-API-Key header
        settings: Application settings
        
    Returns:
        True if API key is valid or not required
        
    Raises:
        HTTPException: 401 if API key is required but missing/invalid
    """
    # Get configured API key
    configured_key = get_api_key(settings)
    
    # If no API key is configured, allow all requests
    if not configured_key:
        return True
    
    # If API key is configured but not provided, deny access
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Please provide X-API-Key header."
        )
    
    # If API key is provided but doesn't match, deny access
    if x_api_key != configured_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key. Please check your X-API-Key header."
        )
    
    return True


def require_api_key() -> bool:
    """Dependency that requires valid API key.
    
    Returns:
        True if API key is valid
        
    Raises:
        HTTPException: 401 if API key is missing or invalid
    """
    return Depends(verify_api_key)