"""
Database CRUD operations for valuation data.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from app.database.models import ValuationRun, Curve, User, AuditLog
from app.database.connection import get_collection
import logging

logger = logging.getLogger(__name__)

class ValuationRunCRUD:
    """CRUD operations for valuation runs."""
    
    @staticmethod
    async def create_run(run_data: dict) -> str:
        """Create a new valuation run."""
        try:
            collection = await get_collection("valuation_runs")
            result = await collection.insert_one(run_data)
            logger.info(f"Created valuation run: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create valuation run: {e}")
            raise
    
    @staticmethod
    async def get_run(run_id: str) -> Optional[dict]:
        """Get a valuation run by ID."""
        try:
            collection = await get_collection("valuation_runs")
            run = await collection.find_one({"run_id": run_id})
            return run
        except Exception as e:
            logger.error(f"Failed to get valuation run {run_id}: {e}")
            return None
    
    @staticmethod
    async def update_run(run_id: str, update_data: dict) -> bool:
        """Update a valuation run."""
        try:
            collection = await get_collection("valuation_runs")
            update_data["updated_at"] = datetime.utcnow()
            result = await collection.update_one(
                {"run_id": run_id}, 
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update valuation run {run_id}: {e}")
            return False
    
    @staticmethod
    async def list_runs(limit: int = 100, skip: int = 0) -> List[dict]:
        """List valuation runs."""
        try:
            collection = await get_collection("valuation_runs")
            cursor = collection.find().sort("created_at", -1).skip(skip).limit(limit)
            runs = await cursor.to_list(length=limit)
            return runs
        except Exception as e:
            logger.error(f"Failed to list valuation runs: {e}")
            return []

class CurveCRUD:
    """CRUD operations for curves."""
    
    @staticmethod
    async def create_curve(curve_data: dict) -> str:
        """Create a new curve."""
        try:
            collection = await get_collection("curves")
            result = await collection.insert_one(curve_data)
            logger.info(f"Created curve: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create curve: {e}")
            raise
    
    @staticmethod
    async def get_curve(curve_id: str) -> Optional[dict]:
        """Get a curve by ID."""
        try:
            collection = await get_collection("curves")
            curve = await collection.find_one({"id": curve_id})
            return curve
        except Exception as e:
            logger.error(f"Failed to get curve {curve_id}: {e}")
            return None
    
    @staticmethod
    async def list_curves(currency: Optional[str] = None, curve_type: Optional[str] = None) -> List[dict]:
        """List curves with optional filtering."""
        try:
            collection = await get_collection("curves")
            filter_dict = {}
            if currency:
                filter_dict["currency"] = currency
            if curve_type:
                filter_dict["curve_type"] = curve_type
            
            cursor = collection.find(filter_dict).sort("created_at", -1)
            curves = await cursor.to_list(length=None)
            return curves
        except Exception as e:
            logger.error(f"Failed to list curves: {e}")
            return []

class AuditCRUD:
    """CRUD operations for audit logs."""
    
    @staticmethod
    async def log_action(action: str, resource_type: str, resource_id: str, 
                        old_values: Optional[dict] = None, new_values: Optional[dict] = None,
                        user_id: str = "system", ip_address: Optional[str] = None):
        """Log an audit action."""
        try:
            collection = await get_collection("audit_logs")
            audit_entry = {
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "old_values": old_values,
                "new_values": new_values,
                "created_by": user_id,
                "ip_address": ip_address,
                "created_at": datetime.utcnow()
            }
            await collection.insert_one(audit_entry)
            logger.info(f"Logged audit action: {action} on {resource_type}:{resource_id}")
        except Exception as e:
            logger.error(f"Failed to log audit action: {e}")

# Initialize CRUD instances
valuation_runs = ValuationRunCRUD()
curves = CurveCRUD()
audit = AuditCRUD()
