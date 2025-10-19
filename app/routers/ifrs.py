"""IFRS question-answering endpoints."""

from typing import Optional, Literal
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.agents.ifrs import answer_ifrs
from app.agents.schemas import IFRSAnswer, IFRSQuestion
from app.agents.guards import apply_policy, check_policy_compliance, PolicyError
from app.settings import get_settings, Settings
from app.deps import require_api_key

router = APIRouter()


class AskRequest(BaseModel):
    """Request model for IFRS questions."""
    
    question: str
    standard_filter: Optional[str] = None
    topic: Optional[Literal["ifrs9_impairment", "ifrs16_leases", "ifrs13_measurement"]] = None


@router.post("/ifrs/ask", response_model=IFRSAnswer)
async def ask_ifrs_question(
    request: AskRequest,
    settings: Settings = Depends(get_settings),
    _: bool = Depends(require_api_key)
) -> IFRSAnswer:
    """Ask a question about IFRS standards.
    
    Args:
        request: Question request with optional filters
        settings: Application settings
        
    Returns:
        Structured IFRS answer with citations and confidence
        
    Raises:
        HTTPException: If question processing fails
    """
    try:
        if not request.question.strip():
            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty"
            )
        
        # Answer the question using RAG
        answer = answer_ifrs(
            question=request.question,
            standard_filter=request.standard_filter,
            topic=request.topic
        )
        
        # Apply policy guardrails
        try:
            validated_answer = apply_policy(answer)
            return validated_answer
        except PolicyError as e:
            # Policy violation - return ABSTAIN with policy reason
            return IFRSAnswer(
                status="ABSTAIN",
                answer=f"Policy violation: {str(e)}",
                citations=[],
                confidence=0.0
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing IFRS question: {str(e)}"
        )


@router.get("/ifrs/health")
async def ifrs_health_check() -> dict:
    """Health check for IFRS service.
    
    Returns:
        Service status information
    """
    return {
        "status": "healthy",
        "service": "ifrs-agent",
        "message": "IFRS question-answering service is running",
        "capabilities": [
            "IFRS 9 - Financial Instruments",
            "IFRS 13 - Fair Value Measurement", 
            "IFRS 16 - Leases"
        ]
    }


@router.get("/ifrs/standards")
async def get_available_standards() -> dict:
    """Get list of available IFRS standards.
    
    Returns:
        Available standards information
    """
    return {
        "standards": [
            {
                "code": "IFRS 9",
                "name": "Financial Instruments",
                "description": "Classification, measurement, and recognition of financial instruments"
            },
            {
                "code": "IFRS 13", 
                "name": "Fair Value Measurement",
                "description": "Framework for measuring fair value and disclosure requirements"
            },
            {
                "code": "IFRS 16",
                "name": "Leases", 
                "description": "Recognition, measurement, presentation and disclosure of leases"
            }
        ],
        "message": "These standards are available for question-answering when documents are uploaded"
    }


@router.post("/ifrs/validate-policy")
async def validate_policy_compliance(answer: IFRSAnswer) -> dict:
    """Validate an IFRS answer against policy guardrails.
    
    Args:
        answer: IFRS answer to validate
        
    Returns:
        Policy compliance check results
    """
    try:
        compliance_results = check_policy_compliance(answer)
        return {
            "is_compliant": compliance_results["is_compliant"],
            "violations": {
                "language": compliance_results["language_violations"],
                "citations": compliance_results["citation_violations"],
                "confidence": compliance_results["confidence_violations"],
                "content": compliance_results["content_violations"]
            },
            "total_violations": compliance_results["total_violations"],
            "recommendation": "PASS" if compliance_results["is_compliant"] else "ABSTAIN"
        }
    except Exception as e:
        return {
            "is_compliant": False,
            "error": f"Policy validation failed: {str(e)}",
            "recommendation": "ABSTAIN"
        }
