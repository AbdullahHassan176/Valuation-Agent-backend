"""
Valuation API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
import uuid
import logging

from app.database.crud import valuation_runs, curves, audit
from app.database.models import ValuationRun, IRSSpec, CCSSpec, PVBreakdown

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/valuation", tags=["valuation"])

@router.post("/runs", response_model=dict)
async def create_valuation_run(
    as_of_date: datetime,
    valuation_type: str,
    spec: dict,
    market_data_profile: str = "synthetic",
    user_id: str = "system"
):
    """Create a new valuation run."""
    try:
        run_id = str(uuid.uuid4())
        
        # Create run data
        run_data = {
            "run_id": run_id,
            "as_of_date": as_of_date,
            "valuation_type": valuation_type,
            "spec": spec,
            "market_data_profile": market_data_profile,
            "status": "pending",
            "created_by": user_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Save to database
        await valuation_runs.create_run(run_data)
        
        # Log audit action
        await audit.log_action(
            action="create",
            resource_type="valuation_run",
            resource_id=run_id,
            new_values=run_data,
            user_id=user_id
        )
        
        logger.info(f"Created valuation run: {run_id}")
        
        return {
            "run_id": run_id,
            "status": "created",
            "message": "Valuation run created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create valuation run: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/runs/{run_id}", response_model=dict)
async def get_valuation_run(run_id: str):
    """Get a valuation run by ID."""
    try:
        run = await valuation_runs.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Valuation run not found")
        
        # Convert ObjectId to string for JSON serialization
        run["_id"] = str(run["_id"])
        
        return run
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get valuation run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/runs", response_model=List[dict])
async def list_valuation_runs(
    limit: int = 100,
    skip: int = 0,
    status: Optional[str] = None
):
    """List valuation runs."""
    try:
        runs = await valuation_runs.list_runs(limit=limit, skip=skip)
        
        # Filter by status if provided
        if status:
            runs = [run for run in runs if run.get("status") == status]
        
        # Convert ObjectIds to strings
        for run in runs:
            run["_id"] = str(run["_id"])
        
        return runs
        
    except Exception as e:
        logger.error(f"Failed to list valuation runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/runs/{run_id}/status", response_model=dict)
async def update_run_status(
    run_id: str,
    status: str,
    result: Optional[dict] = None,
    error_message: Optional[str] = None
):
    """Update the status of a valuation run."""
    try:
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if result:
            update_data["result"] = result
        if error_message:
            update_data["error_message"] = error_message
        
        success = await valuation_runs.update_run(run_id, update_data)
        
        if not success:
            raise HTTPException(status_code=404, detail="Valuation run not found")
        
        # Log audit action
        await audit.log_action(
            action="update_status",
            resource_type="valuation_run",
            resource_id=run_id,
            new_values=update_data
        )
        
        return {
            "run_id": run_id,
            "status": status,
            "message": "Status updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update run status {run_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/curves", response_model=dict)
async def create_curve(
    name: str,
    currency: str,
    curve_type: str,
    as_of_date: datetime,
    nodes: List[dict],
    user_id: str = "system"
):
    """Create a new curve."""
    try:
        curve_id = str(uuid.uuid4())
        
        curve_data = {
            "id": curve_id,
            "name": name,
            "currency": currency,
            "curve_type": curve_type,
            "as_of_date": as_of_date,
            "nodes": nodes,
            "status": "active",
            "version": "1.0.0",
            "created_by": user_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await curves.create_curve(curve_data)
        
        # Log audit action
        await audit.log_action(
            action="create",
            resource_type="curve",
            resource_id=curve_id,
            new_values=curve_data,
            user_id=user_id
        )
        
        logger.info(f"Created curve: {curve_id}")
        
        return {
            "curve_id": curve_id,
            "status": "created",
            "message": "Curve created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create curve: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/curves", response_model=List[dict])
async def list_curves(
    currency: Optional[str] = None,
    curve_type: Optional[str] = None
):
    """List curves with optional filtering."""
    try:
        curves_list = await curves.list_curves(currency=currency, curve_type=curve_type)
        
        # Convert ObjectIds to strings
        for curve in curves_list:
            curve["_id"] = str(curve["_id"])
        
        return curves_list
        
    except Exception as e:
        logger.error(f"Failed to list curves: {e}")
        raise HTTPException(status_code=500, detail=str(e))




