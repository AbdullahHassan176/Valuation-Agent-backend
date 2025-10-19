"""
Backend exports router - proxies to API service
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import httpx
from settings import get_settings

router = APIRouter()

@router.get("/exports/{run_id}/excel")
async def export_excel(run_id: str):
    """
    Export valuation results to Excel (proxy to API)
    
    Args:
        run_id: Run identifier
        
    Returns:
        Excel file stream
    """
    settings = get_settings()
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.api_base_url}/exports/{run_id}/excel")
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
            elif response.status_code == 400:
                raise HTTPException(status_code=400, detail=response.json().get("detail", "Bad request"))
            elif response.status_code != 200:
                raise HTTPException(status_code=500, detail="Error generating Excel export")
            
            # Stream the Excel file
            return StreamingResponse(
                response.iter_bytes(),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=irs_valuation_{run_id}.xlsx"}
            )
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Unable to connect to API service: {str(e)}")

@router.get("/exports/{run_id}/cashflows")
async def export_cashflows(run_id: str):
    """
    Export cashflows as JSON (proxy to API)
    
    Args:
        run_id: Run identifier
        
    Returns:
        Cashflows data
    """
    settings = get_settings()
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.api_base_url}/exports/{run_id}/cashflows")
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
            elif response.status_code == 400:
                raise HTTPException(status_code=400, detail=response.json().get("detail", "Bad request"))
            elif response.status_code != 200:
                raise HTTPException(status_code=500, detail="Error generating cashflow export")
            
            return response.json()
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Unable to connect to API service: {str(e)}")

