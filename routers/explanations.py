"""
Explanation endpoints for retrieval-augmented explanations
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from datetime import datetime
import requests

from rag.vector_store import VectorStore
from rag.explanation_service import ExplanationService, ExplanationContext

router = APIRouter(prefix="/explain", tags=["explanations"])

# Initialize vector store and explanation service
vector_store = VectorStore()
explanation_service = ExplanationService(vector_store)


@router.get("/{run_id}")
async def explain_valuation(run_id: str) -> Dict[str, Any]:
    """
    Generate explanation for a valuation run with document citations
    
    Args:
        run_id: Run identifier
        
    Returns:
        Explanation with citations
    """
    try:
        # Get run details from API
        api_response = requests.get(f"http://127.0.0.1:9000/runs/{run_id}")
        if api_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run {run_id} not found"
            )
        
        run_data = api_response.json()
        
        # Get run result if available
        result_data = None
        try:
            result_response = requests.get(f"http://127.0.0.1:9000/runs/{run_id}/result")
            if result_response.status_code == 200:
                result_data = result_response.json()
        except Exception:
            pass
        
        # Build explanation context
        context = _build_explanation_context(run_data, result_data)
        
        # Generate explanation
        explanation = explanation_service.generate_explanation(context)
        
        # Format response
        return {
            "run_id": run_id,
            "explanation": explanation.explanation_text,
            "citations": [
                {
                    "doc_name": citation.doc_name,
                    "section_id": citation.section_id,
                    "paragraph_id": citation.paragraph_id,
                    "content": citation.content,
                    "relevance_score": citation.relevance_score
                }
                for citation in explanation.citations
            ],
            "confidence_score": explanation.confidence_score,
            "has_sufficient_policy": explanation.has_sufficient_policy,
            "generated_at": explanation.generated_at.isoformat(),
            "warning": None if explanation.has_sufficient_policy else "Insufficient policy documentation available for comprehensive explanation"
        }
        
    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to connect to API service: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating explanation: {str(e)}"
        )


@router.get("/{run_id}/citations/{doc_name}/{section_id}/{paragraph_id}")
async def get_citation_details(
    run_id: str, 
    doc_name: str, 
    section_id: str, 
    paragraph_id: str
) -> Dict[str, Any]:
    """
    Get detailed information about a specific citation
    
    Args:
        run_id: Run identifier
        doc_name: Document name
        section_id: Section identifier
        paragraph_id: Paragraph identifier
        
    Returns:
        Detailed citation information
    """
    try:
        # Get document details
        doc_details = explanation_service.get_document_by_citation(
            doc_name, section_id, paragraph_id
        )
        
        if not doc_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Citation not found"
            )
        
        return {
            "run_id": run_id,
            "citation": {
                "doc_name": doc_name,
                "section_id": section_id,
                "paragraph_id": paragraph_id,
                "content": doc_details['content'],
                "metadata": doc_details['metadata']
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving citation: {str(e)}"
        )


@router.get("/documents")
async def list_documents() -> Dict[str, Any]:
    """
    List all available documents in the vector store
    
    Returns:
        List of available documents
    """
    try:
        documents = vector_store.get_all_documents()
        
        # Group by document name
        doc_groups = {}
        for doc in documents:
            doc_name = doc['metadata']['doc_name']
            if doc_name not in doc_groups:
                doc_groups[doc_name] = {
                    "doc_name": doc_name,
                    "sections": []
                }
            
            doc_groups[doc_name]["sections"].append({
                "section_id": doc['metadata']['section_id'],
                "paragraph_id": doc['metadata']['paragraph_id'],
                "content_type": doc['metadata'].get('content_type', 'text')
            })
        
        return {
            "documents": list(doc_groups.values()),
            "total_documents": len(doc_groups),
            "total_sections": len(documents)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing documents: {str(e)}"
        )


def _build_explanation_context(run_data: Dict[str, Any], result_data: Optional[Dict[str, Any]]) -> ExplanationContext:
    """Build explanation context from run data"""
    
    # Extract instrument type
    spec = run_data['request']['spec']
    if 'payFixed' in spec:
        instrument_type = "IRS"
    elif 'ccy2' in spec:
        instrument_type = "CCS"
    else:
        instrument_type = "Unknown"
    
    # Extract components
    components = {}
    if result_data and 'components' in result_data:
        components = result_data['components']
    
    # Extract XVA components
    xva_components = None
    if result_data and 'xva' in result_data and result_data['xva']:
        xva_data = result_data['xva']
        xva_components = {
            'cva': xva_data.get('cva', 0),
            'dva': xva_data.get('dva', 0),
            'fva': xva_data.get('fva', 0),
            'total_xva': xva_data.get('total_xva', 0)
        }
    
    # Extract sensitivities (placeholder)
    sensitivities = None
    if result_data and 'sensitivities' in result_data:
        sensitivities = result_data['sensitivities']
    
    # Extract IFRS-13 assessment
    ifrs13_assessment = None
    if 'ifrs13_assessment' in run_data and run_data['ifrs13_assessment']:
        ifrs13_assessment = run_data['ifrs13_assessment']
    
    return ExplanationContext(
        run_id=run_data['id'],
        instrument_type=instrument_type,
        valuation_approach=run_data['request']['approach'],
        market_data_profile=run_data['request']['marketDataProfile'],
        as_of_date=run_data['request']['asOf'],
        total_pv=result_data.get('total_pv', 0) if result_data else 0,
        components=components,
        xva_components=xva_components,
        sensitivities=sensitivities,
        ifrs13_assessment=ifrs13_assessment
    )
