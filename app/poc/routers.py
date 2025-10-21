"""PoC API routers for constrained ChatGPT integration."""

import json
import hashlib
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse

from app.poc.schemas import (
    ExtractRequest, ExtractResponse, ExtractField,
    IFRSAskRequest, IFRSAnswer,
    ExplainRunRequest, ExplainRunResponse,
    HealthResponse
)
from app.poc.openai_client import openai_client
from app.poc.redaction import redact, guard_language
from app.poc.ifrs_policy import validate, force_abstain, validate_extract_response, validate_explain_response
from app.settings import get_settings

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/poc", tags=["PoC"])

# Load system prompt
def load_system_prompt() -> str:
    """Load system prompt from file."""
    try:
        with open("app/poc/system_prompt.md", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "You are a constrained valuation assistant. Follow all instructions carefully."


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint showing enabled features."""
    settings = get_settings()
    
    enabled_features = []
    if settings.POC_ENABLE_IFRS:
        enabled_features.append("ifrs_ask")
    if settings.POC_ENABLE_PARSE:
        enabled_features.append("parse_contract")
    if settings.POC_ENABLE_EXPLAIN:
        enabled_features.append("explain_run")
    
    return HealthResponse(
        status="OK",
        enabled_features=enabled_features,
        version="1.0.0"
    )


@router.post("/parse_contract", response_model=ExtractResponse)
async def parse_contract(
    request: ExtractRequest = None,
    file: Optional[UploadFile] = File(None)
):
    """Extract contract terms from text or PDF."""
    
    settings = get_settings()
    if not settings.POC_ENABLE_PARSE:
        raise HTTPException(status_code=503, detail={"status": "DISABLED"})
    
    # Get text content
    text = ""
    if file:
        # Process uploaded file
        content = await file.read()
        text = content.decode('utf-8', errors='ignore')
        
        # Log file info (not content)
        file_hash = hashlib.sha256(content).hexdigest()
        logger.info(f"Processing file: {file.filename}, size: {len(content)}, hash: {file_hash[:16]}")
    elif request and request.text:
        text = request.text
    else:
        raise HTTPException(status_code=400, detail="No text or file provided")
    
    # Limit text length
    if len(text) > 16000:
        text = text[:16000] + "..."
        logger.warning("Text truncated to 16k characters")
    
    # Redact PII
    redacted_text = redact(text)
    
    # Check for language violations
    violations = guard_language(redacted_text)
    if violations:
        return ExtractResponse(
            status="ABSTAIN",
            warnings=violations
        )
    
    # Build prompt
    system_prompt = load_system_prompt()
    user_prompt = {
        "task": "extract_terms",
        "instrument_hint": request.instrument_hint if request else None,
        "ccy_hint": request.ccy_hint if request else None,
        "text_excerpt": redacted_text[:1000]  # First 1000 chars for context
    }
    
    try:
        # Call LLM
        response_text = await openai_client.call_llm_with_retry(
            system_prompt=system_prompt,
            user_json=user_prompt
        )
        
        # Parse response
        response_dict = json.loads(response_text)
        
        # Validate response
        is_valid, reason = validate_extract_response(response_dict)
        if not is_valid:
            response_dict = force_abstain(response_dict, reason)
        
        # Log the interaction
        logger.info(f"Parse contract: status={response_dict.get('status')}, confidence={response_dict.get('confidence')}")
        
        return ExtractResponse(**response_dict)
        
    except Exception as e:
        logger.error(f"Error in parse_contract: {str(e)}")
        return ExtractResponse(
            status="ABSTAIN",
            warnings=[f"Processing error: {str(e)}"]
        )


@router.post("/ifrs_ask", response_model=IFRSAnswer)
async def ifrs_ask(request: IFRSAskRequest):
    """Answer IFRS questions using provided sources."""
    
    settings = get_settings()
    if not settings.POC_ENABLE_IFRS:
        raise HTTPException(status_code=503, detail={"status": "DISABLED"})
    
    # Validate sources
    if not request.sources:
        return IFRSAnswer(
            status="ABSTAIN",
            warnings=["No sources provided"]
        )
    
    # Limit source text length
    for source in request.sources:
        if len(source.get('text', '')) > 2000:
            source['text'] = source['text'][:2000] + "..."
    
    # Build prompt
    system_prompt = load_system_prompt()
    user_prompt = {
        "task": "ifrs_answer",
        "question": request.question,
        "sources": request.sources
    }
    
    try:
        # Call LLM
        response_text = await openai_client.call_llm_with_retry(
            system_prompt=system_prompt,
            user_json=user_prompt
        )
        
        # Parse response
        response_dict = json.loads(response_text)
        
        # Validate response
        is_valid, reason = validate(response_dict)
        if not is_valid:
            response_dict = force_abstain(response_dict, reason)
        
        # Log the interaction
        logger.info(f"IFRS ask: status={response_dict.get('status')}, confidence={response_dict.get('confidence')}")
        
        return IFRSAnswer(**response_dict)
        
    except Exception as e:
        logger.error(f"Error in ifrs_ask: {str(e)}")
        return IFRSAnswer(
            status="ABSTAIN",
            warnings=[f"Processing error: {str(e)}"]
        )


@router.post("/explain_run", response_model=ExplainRunResponse)
async def explain_run(request: ExplainRunRequest):
    """Explain a valuation run result."""
    
    settings = get_settings()
    if not settings.POC_ENABLE_EXPLAIN:
        raise HTTPException(status_code=503, detail={"status": "DISABLED"})
    
    try:
        # Fetch run result from API
        import httpx
        async with httpx.AsyncClient() as client:
            api_response = await client.get(f"{request.api_base}/runs/{request.run_id}/result")
            
            if api_response.status_code != 200:
                return ExplainRunResponse(
                    status="ABSTAIN",
                    warnings=[f"Failed to fetch run result: {api_response.status_code}"]
                )
            
            run_result = api_response.json()
        
        # Build structured context
        result_summary = {
            "run_id": request.run_id,
            "pv_base_ccy": run_result.get("pv_base_ccy"),
            "currency": run_result.get("currency"),
            "legs": run_result.get("legs", []),
            "sensitivities": run_result.get("sensitivities", []),
            "as_of": run_result.get("as_of")
        }
        
        # Build prompt
        system_prompt = load_system_prompt()
        user_prompt = {
            "task": "explain_run",
            "result_summary": result_summary,
            "extra_context": request.extra_context,
            "sources": request.sources
        }
        
        # Call LLM
        response_text = await openai_client.call_llm_with_retry(
            system_prompt=system_prompt,
            user_json=user_prompt
        )
        
        # Parse response
        response_dict = json.loads(response_text)
        
        # Validate response
        is_valid, reason = validate_explain_response(response_dict)
        if not is_valid:
            response_dict = force_abstain(response_dict, reason)
        
        # Log the interaction
        logger.info(f"Explain run: status={response_dict.get('status')}, confidence={response_dict.get('confidence')}")
        
        return ExplainRunResponse(**response_dict)
        
    except Exception as e:
        logger.error(f"Error in explain_run: {str(e)}")
        return ExplainRunResponse(
            status="ABSTAIN",
            warnings=[f"Processing error: {str(e)}"]
        )




