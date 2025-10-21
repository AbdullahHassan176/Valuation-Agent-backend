"""
Database connection and session management.
"""

import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.database_url = os.environ.get('DATABASE_URL', 'mongodb://localhost:27017')
        
    async def connect(self):
        """Connect to the database."""
        try:
            if self.database_url.startswith('mongodb://') or self.database_url.startswith('mongodb+srv://'):
                self.client = AsyncIOMotorClient(self.database_url)
                self.db = self.client.valuation_db
                logger.info(f"Connected to MongoDB: {self.database_url}")
            else:
                # Fallback to local MongoDB
                self.client = AsyncIOMotorClient("mongodb://localhost:27017")
                self.db = self.client.valuation_db
                logger.info("Connected to local MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from the database."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from database")
    
    def get_collection(self, collection_name: str):
        """Get a collection from the database."""
        if not self.db:
            raise Exception("Database not connected")
        return self.db[collection_name]

# Global database manager instance
db_manager = DatabaseManager()

async def get_database():
    """Get the database instance."""
    if not db_manager.db:
        await db_manager.connect()
    return db_manager.db

async def get_collection(collection_name: str):
    """Get a collection from the database."""
    if not db_manager.db:
        await db_manager.connect()
    return db_manager.get_collection(collection_name)




