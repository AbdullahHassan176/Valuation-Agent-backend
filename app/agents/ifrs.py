"""IFRS question-answering agent with RAG capabilities."""

import json
import re
from typing import List, Dict, Any, Optional, Literal
from app.settings import settings
from app.rag.retriever import build_retriever
from app.rag.topics import build_topic_retriever
from app.agents.schemas import IFRSAnswer, Citation
from app.agents.prompts import create_question_prompt, get_abstain_prompt


def answer_ifrs(question: str, standard_filter: Optional[str] = None, topic: Optional[Literal["ifrs9_impairment", "ifrs16_leases", "ifrs13_measurement"]] = None) -> IFRSAnswer:
    """Answer an IFRS question using RAG.
    
    Args:
        question: User's question about IFRS
        standard_filter: Optional filter by IFRS standard
        topic: Optional topic-specific retrieval (ifrs9_impairment, ifrs16_leases, ifrs13_measurement)
        
    Returns:
        Structured IFRS answer with citations and confidence
    """
    try:
        # Build retriever based on topic or use default
        if topic:
            retriever = build_topic_retriever(topic)
        else:
            retriever = build_retriever(k=6, score_threshold=0.2)
        
        # Retrieve relevant documents
        documents = retriever(question)
        
        # Filter by standard if specified
        if standard_filter:
            documents = [
                doc for doc in documents 
                if doc.get("standard", "").lower() == standard_filter.lower()
            ]
        
        # Check if we have sufficient sources
        if not documents or len(documents) == 0:
            return _create_abstain_response(
                question, 
                "No relevant IFRS documents found. Please upload IFRS standards first."
            )
        
        # Check if sources are too weak
        avg_score = sum(doc.get("score", 0) for doc in documents) / len(documents)
        if avg_score < 0.2:
            return _create_abstain_response(
                question,
                f"Retrieved sources are not sufficiently relevant (avg score: {avg_score:.2f}). Please provide more specific question or upload relevant IFRS documents."
            )
        
        # Create prompt with retrieved documents
        prompt = create_question_prompt(question, documents)
        
        # For now, use a simple rule-based approach since we don't have LLM access
        # In production, this would call the actual LLM
        answer = _generate_answer_with_llm(prompt, documents)
        
        # Parse the response
        return _parse_llm_response(answer, documents)
        
    except Exception as e:
        return _create_abstain_response(
            question,
            f"Error processing question: {str(e)}"
        )


def _generate_answer_with_llm(prompt: str, documents: List[Dict[str, Any]]) -> str:
    """Generate answer using LLM (mock implementation for now).
    
    Args:
        prompt: Complete prompt for the LLM
        documents: Retrieved documents
        
    Returns:
        LLM response
    """
    # Mock LLM response for testing
    # In production, this would call OpenAI/Azure LLM
    
    # Simple rule-based response for testing
    if not documents:
        return json.dumps({
            "status": "ABSTAIN",
            "answer": "No relevant sources found.",
            "citations": [],
            "confidence": 0.0
        })
    
    # Create citations from documents with provenance
    citations = []
    for doc in documents[:3]:  # Use top 3 documents
        metadata = doc.get("metadata", {})
        citation = {
            "standard": metadata.get("standard", "IFRS"),
            "paragraph": metadata.get("paragraph", "N/A"),
            "section": metadata.get("section", "N/A"),
            "document_id": metadata.get("document_id", "unknown"),
            "chunk_id": metadata.get("chunk_id", "unknown")
        }
        citations.append(citation)
    
    # Calculate confidence based on document scores
    scores = [doc.get("score", 0) for doc in documents]
    confidence = sum(scores) / len(scores) if scores else 0.0
    
    # Simple answer generation
    answer_text = f"Based on the retrieved IFRS documentation, here is the relevant information:"
    
    for i, doc in enumerate(documents[:2], 1):
        content = doc.get("content", "")
        # Truncate content for response
        if len(content) > 200:
            content = content[:200] + "..."
        answer_text += f"\n\nSource {i}: {content}"
    
    return json.dumps({
        "status": "OK" if confidence >= 0.65 else "ABSTAIN",
        "answer": answer_text,
        "citations": citations,
        "confidence": confidence
    })


def _parse_llm_response(response: str, documents: List[Dict[str, Any]]) -> IFRSAnswer:
    """Parse LLM response into IFRSAnswer.
    
    Args:
        response: LLM response string
        documents: Retrieved documents for fallback
        
    Returns:
        Parsed IFRSAnswer
    """
    try:
        # Try to parse JSON response
        if response.strip().startswith('{'):
            data = json.loads(response)
        else:
            # Fallback: create response from documents
            return _create_fallback_response(documents)
        
        # Extract fields
        status = data.get("status", "ABSTAIN")
        answer = data.get("answer", "No answer provided")
        confidence = float(data.get("confidence", 0.0))
        
        # Parse citations with provenance
        citations = []
        for cit_data in data.get("citations", []):
            citation = Citation(
                standard=cit_data.get("standard", "IFRS"),
                paragraph=cit_data.get("paragraph", "N/A"),
                section=cit_data.get("section"),
                document_id=cit_data.get("document_id", "unknown"),
                chunk_id=cit_data.get("chunk_id", "unknown")
            )
            citations.append(citation)
        
        # Validate confidence and status
        if confidence < 0.5 or not citations:
            status = "ABSTAIN"
            if not citations:
                answer = "Insufficient source citations available."
            else:
                answer = f"Confidence too low ({confidence:.2f}). {answer}"
        
        return IFRSAnswer(
            status=status,
            answer=answer,
            citations=citations,
            confidence=confidence
        )
        
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        # Fallback to document-based response
        return _create_fallback_response(documents)


def _create_fallback_response(documents: List[Dict[str, Any]]) -> IFRSAnswer:
    """Create fallback response from documents.
    
    Args:
        documents: Retrieved documents
        
    Returns:
        IFRSAnswer with document-based response
    """
    if not documents:
        return _create_abstain_response("", "No relevant documents found")
    
    # Create citations from documents with provenance
    citations = []
    for doc in documents[:3]:
        metadata = doc.get("metadata", {})
        citation = Citation(
            standard=metadata.get("standard", "IFRS"),
            paragraph=metadata.get("paragraph", "N/A"),
            section=metadata.get("section"),
            document_id=metadata.get("document_id", "unknown"),
            chunk_id=metadata.get("chunk_id", "unknown")
        )
        citations.append(citation)
    
    # Calculate confidence
    scores = [doc.get("score", 0) for doc in documents]
    confidence = sum(scores) / len(scores) if scores else 0.0
    
    # Create answer from document content
    answer_parts = []
    for i, doc in enumerate(documents[:2], 1):
        content = doc.get("content", "")
        if content:
            # Truncate long content
            if len(content) > 300:
                content = content[:300] + "..."
            answer_parts.append(f"Source {i}: {content}")
    
    answer = "Based on the available IFRS documentation:\n\n" + "\n\n".join(answer_parts)
    
    return IFRSAnswer(
        status="OK" if confidence >= 0.5 else "ABSTAIN",
        answer=answer,
        citations=citations,
        confidence=confidence
    )


def _create_abstain_response(question: str, reason: str) -> IFRSAnswer:
    """Create an abstain response.
    
    Args:
        question: Original question
        reason: Reason for abstaining
        
    Returns:
        IFRSAnswer with ABSTAIN status
    """
    return IFRSAnswer(
        status="ABSTAIN",
        answer=f"Cannot answer: {reason}",
        citations=[],
        confidence=0.0
    )
