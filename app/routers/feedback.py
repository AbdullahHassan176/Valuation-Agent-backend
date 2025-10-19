"""Document feedback analysis endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.agents.feedback import analyze_document, Feedback, ChecklistItem
from app.settings import get_settings, Settings
from app.deps import require_api_key

router = APIRouter()


class AnalyzeRequest(BaseModel):
    """Request model for document analysis."""
    
    doc_id: str
    standard: Optional[str] = "IFRS 13"


@router.post("/feedback/analyze", response_model=Feedback)
async def analyze_document_feedback(
    request: AnalyzeRequest,
    settings: Settings = Depends(get_settings),
    _: bool = Depends(require_api_key)
) -> Feedback:
    """Analyze a document against IFRS standards.
    
    Args:
        request: Analysis request with document ID and standard
        settings: Application settings
        
    Returns:
        Structured feedback with checklist items and citations
        
    Raises:
        HTTPException: If analysis fails
    """
    try:
        if not request.doc_id.strip():
            raise HTTPException(
                status_code=400,
                detail="Document ID cannot be empty"
            )
        
        # Analyze the document
        feedback = analyze_document(
            doc_id=request.doc_id,
            focus_standard=request.standard
        )
        
        return feedback
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing document: {str(e)}"
        )


@router.get("/feedback/health")
async def feedback_health_check() -> dict:
    """Health check for feedback service.
    
    Returns:
        Service status information
    """
    return {
        "status": "healthy",
        "service": "document-feedback",
        "message": "Document feedback analysis service is running",
        "supported_standards": ["IFRS 13", "IFRS 9", "IFRS 16"],
        "features": [
            "Structured checklist analysis",
            "Citation extraction",
            "Compliance scoring",
            "Critical item identification"
        ]
    }


@router.get("/feedback/checklist/{standard}")
async def get_checklist(standard: str = "IFRS 13") -> dict:
    """Get checklist items for a specific IFRS standard.
    
    Args:
        standard: IFRS standard (e.g., "IFRS 13")
        
    Returns:
        Checklist configuration
    """
    try:
        # For now, return IFRS 13 checklist
        if standard.upper() == "IFRS 13":
            return {
                "standard": "IFRS 13",
                "name": "Fair Value Measurement Compliance",
                "description": "Comprehensive checklist for IFRS 13 fair value measurement requirements",
                "categories": [
                    "hierarchy",
                    "market", 
                    "day1_pnl",
                    "risk",
                    "observability",
                    "valuation",
                    "disclosure",
                    "assumptions"
                ],
                "total_items": 20,
                "critical_items": 14,
                "message": "Checklist items will be analyzed against uploaded document content"
            }
        else:
            return {
                "standard": standard,
                "message": f"Checklist for {standard} not yet implemented. Currently supports IFRS 13."
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving checklist: {str(e)}"
        )


@router.get("/feedback/standards")
async def get_supported_standards() -> dict:
    """Get list of supported IFRS standards for feedback analysis.
    
    Returns:
        Supported standards information
    """
    return {
        "supported_standards": [
            {
                "code": "IFRS 13",
                "name": "Fair Value Measurement",
                "description": "Framework for measuring fair value and disclosure requirements",
                "checklist_items": 20,
                "critical_items": 14,
                "categories": 8
            }
        ],
        "message": "Additional standards (IFRS 9, IFRS 16) coming soon"
    }
