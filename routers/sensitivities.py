"""
Backend sensitivities router - proxies to API service
"""
from fastapi import APIRouter, HTTPException
import httpx
from settings import get_settings

router = APIRouter()

@router.get("/runs/{run_id}/sensitivities")
async def get_sensitivities(run_id: str):
    """
    Get sensitivity analysis for a run (proxy to API)
    
    Args:
        run_id: Run identifier
        
    Returns:
        Sensitivity analysis results
    """
    settings = get_settings()
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.api_base_url}/runs/{run_id}/sensitivities")
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
            elif response.status_code == 400:
                raise HTTPException(status_code=400, detail=response.json().get("detail", "Bad request"))
            elif response.status_code != 200:
                raise HTTPException(status_code=500, detail="Error calculating sensitivities")
            
            return response.json()
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Unable to connect to API service: {str(e)}")

