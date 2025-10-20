"""Security utilities for API key validation."""

from typing import Optional
from app.settings import get_settings


def validate_api_key(api_key: Optional[str]) -> bool:
    """Validate API key against configured key.
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if valid, False otherwise
    """
    settings = get_settings()
    
    if not api_key:
        return False
        
    if not settings.API_KEY:
        # If no API key is configured, allow all requests in development
        return True
        
    return api_key == settings.API_KEY



