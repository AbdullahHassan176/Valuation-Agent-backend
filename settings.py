from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    api_base_url: str = "http://api:9000"
    
    # Server Configuration
    port: int = 8000
    host: str = "0.0.0.0"
    
    # Database Configuration (for future use)
    database_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Get the global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
