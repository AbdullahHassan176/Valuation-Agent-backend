"""Pydantic schemas for PoC endpoints."""

from typing import List, Optional, Literal, Union, Dict, Any
from pydantic import BaseModel, Field


class ExtractField(BaseModel):
    """Extracted field from contract."""
    key: str
    value: Union[str, float, None]
    confidence: float = Field(ge=0.0, le=1.0)
    source_span: Optional[str] = None


class ExtractRequest(BaseModel):
    """Request to extract contract terms."""
    text: Optional[str] = None
    file_id: Optional[str] = None
    instrument_hint: Optional[Literal["IRS", "CCS"]] = None
    ccy_hint: Optional[str] = None


class ExtractResponse(BaseModel):
    """Response from contract extraction."""
    status: Literal["OK", "ABSTAIN"]
    instrument: Optional[str] = None
    fields: List[ExtractField] = []
    citations: List[Dict[str, Any]] = []
    confidence: float = Field(ge=0.0, le=1.0)
    warnings: List[str] = []


class IFRSAskRequest(BaseModel):
    """Request for IFRS question answering."""
    question: str
    sources: List[Dict[str, Any]] = Field(..., min_length=1)


class IFRSAnswer(BaseModel):
    """Response for IFRS question."""
    status: Literal["OK", "ABSTAIN"]
    answer: str = ""
    citations: List[Dict[str, str]] = []
    confidence: float = Field(ge=0.0, le=1.0)
    warnings: List[str] = []


class ExplainRunRequest(BaseModel):
    """Request to explain a valuation run."""
    run_id: str
    api_base: str
    extra_context: Optional[str] = None
    sources: List[Dict[str, Any]] = []


class ExplainRunResponse(BaseModel):
    """Response explaining a valuation run."""
    status: Literal["OK", "ABSTAIN"]
    narrative: str = ""
    key_points: List[str] = []
    citations: List[Dict[str, str]] = []
    confidence: float = Field(ge=0.0, le=1.0)
    warnings: List[str] = []


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "OK"
    enabled_features: List[str] = []
    version: str = "1.0.0"
