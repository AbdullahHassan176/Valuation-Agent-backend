"""Application settings using Pydantic BaseSettings."""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    API_NAME: str = "valuation-backend"
    PORT: int = 8000
    
    # Vector and Document Storage
    VECTOR_DIR: str = "./.vector/ifrs"
    DOC_STORE: str = "./.docs"
    
    # AI Model Configuration
    EMBEDDINGS_MODEL: str = "text-embedding-3-large"
    LLM_MODEL: str = "gpt-4o-mini"
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_API_VERSION: Optional[str] = None
    
    # CORS Configuration
    ALLOW_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"]
    
    # Security Configuration
    API_KEY: Optional[str] = None
    
    # Logging and Audit
    LOG_DB: str = "sqlite:///./.run/audit.db"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
