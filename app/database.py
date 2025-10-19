"""
Database connection and session management.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.settings import get_settings

settings = get_settings()

# Database URL configuration
if settings.DATABASE_URL:
    # Use PostgreSQL for production
    DATABASE_URL = settings.DATABASE_URL
    engine = create_engine(DATABASE_URL)
else:
    # Use SQLite for development
    DATABASE_URL = "sqlite:///./.run/valuation.db"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create database tables."""
    Base.metadata.create_all(bind=engine)


def get_database_url():
    """Get the database URL."""
    return DATABASE_URL
