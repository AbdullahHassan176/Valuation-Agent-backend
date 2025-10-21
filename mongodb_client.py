"""
MongoDB client for Azure Cosmos DB for MongoDB integration.
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

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
                    import urllib.parse
                    encoded_conn = urllib.parse.quote(self.connection_string, safe='://@')
                    self.client = AsyncIOMotorClient(
                        encoded_conn,
                        serverSelectionTimeoutMS=30000,
                        connectTimeoutMS=30000,
                        socketTimeoutMS=30000,
                        retryWrites=False,
                        tls=True,
                        directConnection=False,
                        maxPoolSize=10,
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
            # Add timestamp
            run_data["created_at"] = datetime.utcnow()
            run_data["updated_at"] = datetime.utcnow()
            
            # Insert into runs collection
            result = await self.db.runs.insert_one(run_data)
            print(f"✅ Run created with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            print(f"❌ Error creating run: {e}")
            raise e
    
    async def get_runs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all valuation runs from MongoDB."""
        try:
            cursor = self.db.runs.find().sort("created_at", -1).limit(limit)
            runs = []
            async for run in cursor:
                # Convert ObjectId to string
                run["_id"] = str(run["_id"])
                runs.append(run)
            return runs
        except Exception as e:
            print(f"❌ Error getting runs: {e}")
            return []
    
    async def get_run_by_id(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific run by ID."""
        try:
            from bson import ObjectId
            run = await self.db.runs.find_one({"_id": ObjectId(run_id)})
            if run:
                run["_id"] = str(run["_id"])
            return run
        except Exception as e:
            print(f"❌ Error getting run {run_id}: {e}")
            return None
    
    async def update_run(self, run_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a run in MongoDB."""
        try:
            from bson import ObjectId
            update_data["updated_at"] = datetime.utcnow()
            result = await self.db.runs.update_one(
                {"_id": ObjectId(run_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Error updating run {run_id}: {e}")
            return False
    
    async def delete_run(self, run_id: str) -> bool:
        """Delete a run from MongoDB."""
        try:
            from bson import ObjectId
            result = await self.db.runs.delete_one({"_id": ObjectId(run_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"❌ Error deleting run {run_id}: {e}")
            return False
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            run_count = await self.db.runs.count_documents({})
            curve_count = await self.db.curves.count_documents({})
            
            # Get recent runs
            recent_runs = []
            cursor = self.db.runs.find().sort("created_at", -1).limit(5)
            async for run in cursor:
                recent_runs.append({
                    "id": str(run["_id"]),
                    "status": run.get("status", "unknown"),
                    "instrument_type": run.get("instrument_type", "unknown"),
                    "currency": run.get("currency", "unknown"),
                    "notional_amount": run.get("notional_amount", 0),
                    "created_at": run.get("created_at", "").isoformat() if run.get("created_at") else ""
                })
            
            return {
                "database_type": "MongoDB (Azure Cosmos DB)",
                "database_name": self.database_name,
                "total_runs": run_count,
                "total_curves": curve_count,
                "recent_runs": recent_runs,
                "message": "Data is stored in Azure Cosmos DB and visible in Data Explorer"
            }
        except Exception as e:
            print(f"❌ Error getting database stats: {e}")
            return {
                "database_type": "MongoDB (Azure Cosmos DB)",
                "database_name": self.database_name,
                "error": str(e),
                "message": "Error connecting to database"
            }
    
    async def create_curve(self, curve_data: Dict[str, Any]) -> str:
        """Create a new yield curve in MongoDB."""
        try:
            # Add timestamp
            curve_data["created_at"] = datetime.utcnow()
            curve_data["updated_at"] = datetime.utcnow()
            
            # Insert into curves collection
            result = await self.db.curves.insert_one(curve_data)
            print(f"✅ Curve created with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            print(f"❌ Error creating curve: {e}")
            raise e
    
    async def get_curves(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all yield curves from MongoDB."""
        try:
            cursor = self.db.curves.find().sort("created_at", -1).limit(limit)
            curves = []
            async for curve in cursor:
                # Convert ObjectId to string
                curve["_id"] = str(curve["_id"])
                curves.append(curve)
            return curves
        except Exception as e:
            print(f"❌ Error getting curves: {e}")
            return []

# Global MongoDB client instance
mongodb_client = MongoDBClient()
