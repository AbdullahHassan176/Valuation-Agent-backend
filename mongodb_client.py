"""
MongoDB client for Azure Cosmos DB for MongoDB.
Fixed version with proper indentation.
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import urllib.parse

class MongoDBClient:
    """MongoDB client for Azure Cosmos DB for MongoDB."""
    
    def __init__(self):
        # Get MongoDB connection string from environment
        self.connection_string = os.getenv(
            "MONGODB_CONNECTION_STRING", 
            "mongodb://localhost:27017"  # Default for local development
        )
        self.database_name = os.getenv("MONGODB_DATABASE", "valuation-backend-server")
        self.client = None
        self.db = None
        
        # Validate connection string
        self._validate_connection_string()
    
    def _validate_connection_string(self):
        """Validate and potentially fix the connection string."""
        if not self.connection_string:
            print("❌ No MongoDB connection string provided")
            return False
            
        # Check for common issues
        if len(self.connection_string) > 200:
            print(f"⚠️ Connection string is very long ({len(self.connection_string)} chars)")
            
        # Check for special characters that might cause issues
        if any(char in self.connection_string for char in ['<', '>', '"', "'", '&']):
            print("⚠️ Connection string contains special characters that might cause issues")
            
        # Check if it's a valid MongoDB URI format
        if not self.connection_string.startswith(('mongodb://', 'mongodb+srv://')):
            print("❌ Connection string doesn't start with mongodb:// or mongodb+srv://")
            return False
            
        print(f"✅ Connection string format looks valid (length: {len(self.connection_string)})")
        return True
        
    async def connect(self):
        """Connect to MongoDB."""
        try:
            # Handle long connection strings by truncating for logging
            conn_preview = self.connection_string[:50] + "..." if len(self.connection_string) > 50 else self.connection_string
            print(f"🔍 Connecting to MongoDB: {conn_preview}")
            
            # For Azure Cosmos DB, use specific connection parameters
            if "cosmos.azure.com" in self.connection_string or len(self.connection_string) > 100:
                print("🔍 Detected Azure Cosmos DB - using optimized connection parameters")
                try:
                    # Try with minimal parameters first
                    self.client = AsyncIOMotorClient(
                        self.connection_string,
                        serverSelectionTimeoutMS=30000,
                        connectTimeoutMS=30000,
                        socketTimeoutMS=30000,
                        retryWrites=False,
                        tls=True,
                        directConnection=True,  # Try direct connection first
                        maxPoolSize=1,
                        minPoolSize=1
                    )
                except UnicodeError as unicode_err:
                    print(f"❌ Unicode error with connection string: {unicode_err}")
                    print("🔍 Trying with URL encoding...")
                    # Try to encode the connection string properly
                    encoded_conn = urllib.parse.quote(self.connection_string, safe='://@')
                    self.client = AsyncIOMotorClient(
                        encoded_conn,
                        serverSelectionTimeoutMS=30000,
                        connectTimeoutMS=30000,
                        socketTimeoutMS=30000,
                        retryWrites=False,
                        tls=True,
                        directConnection=True,
                        maxPoolSize=1,
                        minPoolSize=1
                    )
            else:
                # Standard MongoDB connection
                self.client = AsyncIOMotorClient(
                    self.connection_string,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000,
                    socketTimeoutMS=5000
                )
            
            self.db = self.client[self.database_name]
            
            # Test connection with a simple ping
            await self.client.admin.command('ping')
            print(f"✅ Connected to MongoDB database: {self.database_name}")
            return True
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            print(f"❌ Connection string length: {len(self.connection_string)}")
            print(f"❌ Error type: {type(e).__name__}")
            
            # Try alternative connection method for Azure Cosmos DB
            try:
                print("🔍 Trying alternative connection method...")
                # Close existing client
                if self.client:
                    self.client.close()
                
                # Try with minimal parameters for Cosmos DB
                self.client = AsyncIOMotorClient(
                    self.connection_string,
                    serverSelectionTimeoutMS=60000,  # 60 second timeout
                    connectTimeoutMS=60000,
                    socketTimeoutMS=60000,
                    retryWrites=False,
                    directConnection=True,  # Try direct connection
                    maxPoolSize=1,
                    minPoolSize=1
                )
                self.db = self.client[self.database_name]
                
                # Test connection
                await self.client.admin.command('ping')
                print(f"✅ Connected to MongoDB database (alternative method): {self.database_name}")
                return True
            except Exception as e2:
                print(f"❌ Alternative connection also failed: {e2}")
                return False
            
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
    
    async def create_run(self, run_data: Dict[str, Any]) -> str:
        """Create a new valuation run in MongoDB."""
        try:
            if not self.db:
                await self.connect()
            
            # Insert the run
            result = await self.db.runs.insert_one(run_data)
            print(f"✅ Created run with ID: {result.inserted_id}")
            
            # Convert ObjectId to string for JSON serialization
            run_data["_id"] = str(result.inserted_id)
            return str(result.inserted_id)
        except Exception as e:
            print(f"❌ Error creating run: {e}")
            return None
    
    async def get_runs(self) -> List[Dict[str, Any]]:
        """Get all valuation runs from MongoDB."""
        try:
            if not self.db:
                await self.connect()
            
            # Get all runs, sorted by creation time
            cursor = self.db.runs.find().sort("metadata.calculation_timestamp", -1)
            runs = []
            async for run in cursor:
                # Convert ObjectId to string for JSON serialization
                run["_id"] = str(run["_id"])
                runs.append(run)
            
            print(f"✅ Retrieved {len(runs)} runs from MongoDB")
            return runs
        except Exception as e:
            print(f"❌ Error getting runs: {e}")
            return []
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            if not self.db:
                await self.connect()
            
            # Get collection stats
            runs_count = await self.db.runs.count_documents({})
            curves_count = await self.db.curves.count_documents({})
            
            # Get recent runs
            recent_runs = []
            cursor = self.db.runs.find().sort("metadata.calculation_timestamp", -1).limit(5)
            async for run in cursor:
                recent_runs.append({
                    "id": run.get("id", "Unknown"),
                    "instrument_type": run.get("instrument_type", "Unknown"),
                    "pv_base_ccy": run.get("pv_base_ccy", 0),
                    "timestamp": run.get("metadata", {}).get("calculation_timestamp", "Unknown")
                })
            
            return {
                "total_runs": runs_count,
                "total_curves": curves_count,
                "recent_runs": recent_runs,
                "database_name": self.database_name,
                "connection_status": "connected" if self.client else "disconnected"
            }
        except Exception as e:
            print(f"❌ Error getting database stats: {e}")
            return {
                "total_runs": 0,
                "total_curves": 0,
                "recent_runs": [],
                "database_name": self.database_name,
                "connection_status": "error",
                "error": str(e)
            }
    
    async def create_curve(self, curve_data: Dict[str, Any]) -> str:
        """Create a new yield curve in MongoDB."""
        try:
            if not self.db:
                await self.connect()
            
            # Insert the curve
            result = await self.db.curves.insert_one(curve_data)
            print(f"✅ Created curve with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            print(f"❌ Error creating curve: {e}")
            return None
    
    async def get_curves(self) -> List[Dict[str, Any]]:
        """Get all yield curves from MongoDB."""
        try:
            if not self.db:
                await self.connect()
            
            # Get all curves
            cursor = self.db.curves.find()
            curves = []
            async for curve in cursor:
                # Convert ObjectId to string for JSON serialization
                curve["_id"] = str(curve["_id"])
                curves.append(curve)
            
            print(f"✅ Retrieved {len(curves)} curves from MongoDB")
            return curves
        except Exception as e:
            print(f"❌ Error getting curves: {e}")
            return []

# Global MongoDB client instance
mongodb_client = MongoDBClient()
