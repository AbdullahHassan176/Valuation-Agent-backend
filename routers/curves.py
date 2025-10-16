from fastapi import APIRouter, HTTPException, status, Request
import httpx
from typing import Optional
from ..settings import get_settings

router = APIRouter(
    prefix="/curves",
    tags=["curves"],
    responses={404: {"description": "Not found"}},
)

@router.post("/bootstrap")
async def bootstrap_curve(request: Request):
    """Bootstrap a curve by calling the API"""
    settings = get_settings()
    api_url = f"{settings.api_base_url}/curves/bootstrap"
    
    # Get request body
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                api_url, 
                content=body,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.json())
        except httpx.RequestError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"API service unavailable: {e}")

@router.get("/{curve_id}")
async def get_curve(curve_id: str):
    """Get a curve by ID from the API"""
    settings = get_settings()
    api_url = f"{settings.api_base_url}/curves/{curve_id}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(api_url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.json())
        except httpx.RequestError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"API service unavailable: {e}")

@router.get("/")
async def list_curves():
    """List all available curves from the API"""
    settings = get_settings()
    api_url = f"{settings.api_base_url}/curves/"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(api_url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.json())
        except httpx.RequestError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"API service unavailable: {e}")
