"""
Database connection and session management for MongoDB.
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from app.settings import get_settings

settings = get_settings()

# MongoDB connection
if settings.DATABASE_URL:
    # Use MongoDB connection string from environment
    client = AsyncIOMotorClient(settings.DATABASE_URL)
    db = client.valuation_db
else:
    # Local MongoDB for development
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.valuation_db


def get_database():
    """Get MongoDB database instance."""
    return db


def get_client():
    """Get MongoDB client."""
    return client


def create_tables():
    """Initialize MongoDB collections."""
    try:
        # MongoDB collections are created automatically when first document is inserted
        # We'll create indexes for better performance
        print("MongoDB database and collections initialized")
        
        # Create indexes for better query performance
        # db.documents.create_index("title")
        # db.pages.create_index("document_id")
        # db.chunks.create_index("page_id")
        
    except Exception as e:
        print(f"Warning: Could not initialize MongoDB: {e}")


def get_database_url():
    """Get the database URL."""
    return settings.DATABASE_URL or "mongodb://localhost:27017"
