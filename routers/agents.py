"""
Agent endpoints for contract parsing and processing.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
import logging

from agents.contract_parser import parse_contract_node
from agents.pdf_processor import PDFProcessor

router = APIRouter(prefix="/agents", tags=["agents"])
logger = logging.getLogger(__name__)


@router.post("/parse_contract")
async def parse_contract_endpoint(
    file: UploadFile = File(...)
) -> JSONResponse:
    """
    Parse uploaded PDF contract and extract financial instrument fields.
    
    Args:
        file: Uploaded PDF file
        
    Returns:
        JSON response with extracted fields and confidence scores
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400, 
                detail="Only PDF files are supported"
            )
        
        # Read file content
        pdf_content = await file.read()
        
        # Validate PDF
        is_valid, error_msg = PDFProcessor.validate_pdf(pdf_content)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid PDF file: {error_msg}"
            )
        
        # Extract text from PDF
        text = PDFProcessor.extract_text_from_pdf(pdf_content)
        
        if not text or len(text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="PDF appears to be empty or contains no extractable text"
            )
        
        # Parse contract using LangGraph node
        extraction_result = parse_contract_node(text)
        
        # Generate proposed spec JSON
        proposed_spec = _generate_proposed_spec(extraction_result)
        
        return JSONResponse(content={
            "success": True,
            "extraction": extraction_result,
            "proposed_spec": proposed_spec,
            "filename": file.filename,
            "text_length": len(text)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing contract: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal error during contract parsing: {str(e)}"
        )


def _generate_proposed_spec(extraction_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate proposed IRSSpec or CCSSpec JSON from extraction results.
    
    Args:
        extraction_result: Result from contract parsing
        
    Returns:
        Proposed spec dictionary
    """
    fields = {f["field_name"]: f for f in extraction_result["fields"]}
    instrument_type = extraction_result["instrument_type"]
    
    if instrument_type == "IRS":
        spec = {
            "type": "IRS",
            "notional": fields.get("notional", {}).get("value", 1000000),
            "currency": fields.get("currency", {}).get("value", "USD"),
            "payFixed": True,  # Default assumption
            "fixedRate": fields.get("fixed_rate", {}).get("value", 0.05),
            "floatIndex": fields.get("floating_index", {}).get("value", "SOFR"),
            "effective": fields.get("effective_date", {}).get("value", "2024-01-01"),
            "maturity": fields.get("maturity_date", {}).get("value", "2025-01-01"),
            "dcFixed": fields.get("day_count", {}).get("value", "ACT/360"),
            "dcFloat": fields.get("day_count", {}).get("value", "ACT/360"),
            "freqFixed": fields.get("frequency", {}).get("value", "3M"),
            "freqFloat": fields.get("frequency", {}).get("value", "3M"),
            "calendar": "USD_CALENDAR",
            "bdc": fields.get("business_day_convention", {}).get("value", "FOLLOWING"),
            "csa": None
        }
    else:  # CCS
        spec = {
            "type": "CCS",
            "ccy1": fields.get("currency", {}).get("value", "USD"),
            "ccy2": "EUR",  # Default assumption for CCS
            "notional1": fields.get("notional", {}).get("value", 1000000),
            "notional2": fields.get("notional", {}).get("value", 1000000) * 0.85,  # Rough EUR conversion
            "index1": fields.get("floating_index", {}).get("value", "SOFR"),
            "index2": "EURIBOR",  # Default for EUR
            "effective": fields.get("effective_date", {}).get("value", "2024-01-01"),
            "maturity": fields.get("maturity_date", {}).get("value", "2025-01-01"),
            "freq1": fields.get("frequency", {}).get("value", "3M"),
            "freq2": fields.get("frequency", {}).get("value", "3M"),
            "calendar": "USD_EUR_CALENDAR",
            "bdc": fields.get("business_day_convention", {}).get("value", "FOLLOWING"),
            "reportingCcy": "USD"
        }
    
    return spec


@router.get("/parse_contract/status")
async def get_parse_status() -> JSONResponse:
    """Get the status of the contract parsing service."""
    return JSONResponse(content={
        "service": "contract_parser",
        "status": "active",
        "supported_formats": ["PDF"],
        "max_file_size": "10MB",
        "features": [
            "Field extraction with confidence scores",
            "IRS and CCS instrument detection", 
            "Automatic spec generation",
            "Validation with confidence thresholds"
        ]
    })

