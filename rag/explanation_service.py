"""
Explanation service for generating retrieval-augmented explanations
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json

from .vector_store import VectorStore, DocumentProcessor


@dataclass
class ExplanationContext:
    """Context for generating explanations"""
    run_id: str
    instrument_type: str  # IRS, CCS, etc.
    valuation_approach: List[str]
    market_data_profile: str
    as_of_date: str
    total_pv: float
    components: Dict[str, float]
    xva_components: Optional[Dict[str, float]] = None
    sensitivities: Optional[Dict[str, Any]] = None
    ifrs13_assessment: Optional[Dict[str, Any]] = None


@dataclass
class Citation:
    """Document citation"""
    doc_name: str
    section_id: str
    paragraph_id: str
    content: str
    relevance_score: float


@dataclass
class Explanation:
    """Generated explanation with citations"""
    run_id: str
    explanation_text: str
    citations: List[Citation]
    generated_at: datetime
    confidence_score: float
    has_sufficient_policy: bool


class ExplanationService:
    """Service for generating retrieval-augmented explanations"""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self._initialize_documents()
    
    def _initialize_documents(self):
        """Initialize the vector store with sample documents"""
        # Check if documents already exist
        existing_docs = self.vector_store.get_all_documents()
        if not existing_docs:
            # Load sample documents
            sample_docs = DocumentProcessor.create_sample_documents()
            for doc in sample_docs:
                self.vector_store.add_document(doc)
    
    def generate_explanation(self, context: ExplanationContext) -> Explanation:
        """Generate explanation for a valuation run"""
        
        # Build query based on context
        query_parts = []
        
        # Add instrument type
        if context.instrument_type == "IRS":
            query_parts.append("Interest Rate Swap valuation methodology")
        elif context.instrument_type == "CCS":
            query_parts.append("Cross Currency Swap valuation methodology")
        
        # Add approach-specific terms
        for approach in context.valuation_approach:
            if approach == "discount_curve":
                query_parts.append("discount curve methodology")
            elif approach == "forward_curve":
                query_parts.append("forward curve projection")
            elif approach == "basis_adjustment":
                query_parts.append("basis adjustment")
        
        # Add XVA terms if present
        if context.xva_components:
            query_parts.append("XVA Credit Value Adjustment Debit Value Adjustment Funding Value Adjustment")
        
        # Add sensitivity terms if present
        if context.sensitivities:
            query_parts.append("sensitivity analysis risk management")
        
        # Add IFRS-13 terms if present
        if context.ifrs13_assessment:
            query_parts.append("IFRS-13 fair value hierarchy compliance")
        
        # Combine query parts
        query = " ".join(query_parts)
        
        # Search for relevant documents
        search_results = self.vector_store.search_documents(
            query=query,
            n_results=5
        )
        
        # Generate explanation
        explanation_text, citations = self._synthesize_explanation(
            context, search_results
        )
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(search_results)
        
        # Check if we have sufficient policy coverage
        has_sufficient_policy = len(search_results) >= 2 and confidence_score > 0.3
        
        return Explanation(
            run_id=context.run_id,
            explanation_text=explanation_text,
            citations=citations,
            generated_at=datetime.utcnow(),
            confidence_score=confidence_score,
            has_sufficient_policy=has_sufficient_policy
        )
    
    def _synthesize_explanation(
        self, 
        context: ExplanationContext, 
        search_results: List[Dict[str, Any]]
    ) -> tuple[str, List[Citation]]:
        """Synthesize explanation from search results"""
        
        citations = []
        explanation_parts = []
        
        if not search_results:
            return (
                "Unable to generate explanation due to insufficient policy documentation. Please ensure relevant methodology documents are available.",
                []
            )
        
        # Build explanation based on context and search results
        explanation_parts.append(f"This {context.instrument_type} valuation was performed using the following methodology:")
        
        # Add methodology explanation
        for result in search_results:
            if result['metadata']['content_type'] == 'methodology':
                explanation_parts.append(f"• {result['content']}")
                citations.append(Citation(
                    doc_name=result['metadata']['doc_name'],
                    section_id=result['metadata']['section_id'],
                    paragraph_id=result['metadata']['paragraph_id'],
                    content=result['content'],
                    relevance_score=result['similarity_score']
                ))
        
        # Add XVA explanation if present
        if context.xva_components:
            explanation_parts.append("\nXVA adjustments were applied:")
            for result in search_results:
                if 'XVA' in result['metadata']['doc_name']:
                    explanation_parts.append(f"• {result['content']}")
                    citations.append(Citation(
                        doc_name=result['metadata']['doc_name'],
                        section_id=result['metadata']['section_id'],
                        paragraph_id=result['metadata']['paragraph_id'],
                        content=result['content'],
                        relevance_score=result['similarity_score']
                    ))
        
        # Add risk management explanation if sensitivities present
        if context.sensitivities:
            explanation_parts.append("\nRisk analysis was performed according to policy:")
            for result in search_results:
                if 'Risk' in result['metadata']['doc_name']:
                    explanation_parts.append(f"• {result['content']}")
                    citations.append(Citation(
                        doc_name=result['metadata']['doc_name'],
                        section_id=result['metadata']['section_id'],
                        paragraph_id=result['metadata']['paragraph_id'],
                        content=result['content'],
                        relevance_score=result['similarity_score']
                    ))
        
        # Add IFRS-13 explanation if present
        if context.ifrs13_assessment:
            explanation_parts.append("\nIFRS-13 compliance was assessed:")
            for result in search_results:
                if 'IFRS13' in result['metadata']['doc_name']:
                    explanation_parts.append(f"• {result['content']}")
                    citations.append(Citation(
                        doc_name=result['metadata']['doc_name'],
                        section_id=result['metadata']['section_id'],
                        paragraph_id=result['metadata']['paragraph_id'],
                        content=result['content'],
                        relevance_score=result['similarity_score']
                    ))
        
        # Add valuation summary
        explanation_parts.append(f"\nThe total present value of {context.total_pv:,.2f} was calculated using the {context.market_data_profile} market data profile as of {context.as_of_date}.")
        
        if context.components:
            explanation_parts.append("Component breakdown:")
            for component, value in context.components.items():
                explanation_parts.append(f"• {component}: {value:,.2f}")
        
        explanation_text = "\n".join(explanation_parts)
        
        return explanation_text, citations
    
    def _calculate_confidence(self, search_results: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on search results"""
        if not search_results:
            return 0.0
        
        # Average similarity score
        avg_similarity = sum(result['similarity_score'] for result in search_results) / len(search_results)
        
        # Bonus for multiple relevant documents
        diversity_bonus = min(0.2, len(search_results) * 0.05)
        
        return min(1.0, avg_similarity + diversity_bonus)
    
    def get_document_by_citation(self, doc_name: str, section_id: str, paragraph_id: str) -> Optional[Dict[str, Any]]:
        """Get full document content by citation"""
        # Search for documents with matching metadata
        all_docs = self.vector_store.get_all_documents()
        for doc in all_docs:
            if (doc['metadata']['doc_name'] == doc_name and 
                doc['metadata']['section_id'] == section_id and
                doc['metadata']['paragraph_id'] == paragraph_id):
                return doc
        return None
    
    def search_specific_document(self, doc_name: str, query: str) -> List[Dict[str, Any]]:
        """Search within a specific document"""
        return self.vector_store.search_documents(
            query=query,
            n_results=3,
            doc_filter=doc_name
        )

