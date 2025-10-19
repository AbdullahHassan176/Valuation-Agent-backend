from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
import httpx
import json
import asyncio
from settings import get_settings
from sdk.models import RunRequest, RunStatus, PVBreakdown

router = APIRouter(prefix="/runs", tags=["runs"])
settings = get_settings()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_run(request):
    """Create a new valuation run by proxying to API"""
    async with httpx.AsyncClient() as client:
        try:
            # Forward request to API
            response = await client.post(
                f"{settings.api_base_url}/runs",
                json=request.dict(),
                timeout=30.0
            )
            response.raise_for_status()
            
            # Parse and return the response
            run_status_data = response.json()
            return RunStatus(**run_status_data)
            
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"API error: {e.response.text}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to connect to API: {str(e)}"
            )

@router.get("/{run_id}", response_model=RunStatus)
async def get_run(run_id: str) -> RunStatus:
    """Get the status of a valuation run by proxying to API"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.api_base_url}/runs/{run_id}",
                timeout=30.0
            )
            response.raise_for_status()
            
            run_status_data = response.json()
            return RunStatus(**run_status_data)
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Run {run_id} not found"
                )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"API error: {e.response.text}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to connect to API: {str(e)}"
            )

@router.get("/{run_id}/result", response_model=PVBreakdown)
async def get_run_result(run_id: str) -> PVBreakdown:
    """Get the result of a valuation run by proxying to API"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.api_base_url}/runs/{run_id}/result",
                timeout=30.0
            )
            response.raise_for_status()
            
            result_data = response.json()
            return PVBreakdown(**result_data)
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Run {run_id} not found"
                )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"API error: {e.response.text}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to connect to API: {str(e)}"
            )
