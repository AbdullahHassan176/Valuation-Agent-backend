"""Pydantic schemas for IFRS agent responses."""

from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Citation reference to IFRS document."""
    
    standard: str = Field(..., description="IFRS standard (e.g., 'IFRS 9', 'IFRS 13')")
    paragraph: Union[str, int] = Field(..., description="Paragraph number or reference")
    section: Optional[str] = Field(None, description="Section title or reference")


class IFRSAnswer(BaseModel):
    """Structured response from IFRS agent."""
    
    status: Literal["OK", "ABSTAIN"] = Field(..., description="Response status")
    answer: str = Field(..., description="Answer text or abstention reason")
    citations: List[Citation] = Field(default_factory=list, description="Source citations")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")


class IFRSQuestion(BaseModel):
    """IFRS question input."""
    
    question: str = Field(..., description="Question about IFRS standards")
    standard_filter: Optional[str] = Field(None, description="Filter by specific IFRS standard")
    section_filter: Optional[str] = Field(None, description="Filter by document section")


class RetrievalResult(BaseModel):
    """Document retrieval result."""
    
    content: str = Field(..., description="Document content")
    metadata: dict = Field(..., description="Document metadata")
    score: float = Field(..., description="Relevance score")
    doc_id: str = Field(..., description="Document identifier")
    standard: str = Field(..., description="IFRS standard")
    section: str = Field(..., description="Document section")
    paragraph: str = Field(..., description="Document paragraph")
    page_from: int = Field(..., description="Starting page")
    page_to: int = Field(..., description="Ending page")
