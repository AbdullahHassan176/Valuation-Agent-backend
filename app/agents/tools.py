"""Constrained chat agent tools for IFRS and document analysis."""

from typing import List, Dict, Any, Optional
from app.agents.ifrs import answer_ifrs
from app.agents.feedback import analyze_document
from app.agents.schemas import IFRSAnswer
from app.agents.feedback import Feedback
from app.rag.store import get_collection, get_vector_store


def tool_ifrs_ask(question: str, standard_filter: Optional[str] = None) -> IFRSAnswer:
    """Ask a question about IFRS standards.
    
    Args:
        question: Question about IFRS standards
        standard_filter: Optional filter by IFRS standard
        
    Returns:
        IFRS answer with citations and confidence
    """
    try:
        return answer_ifrs(question, standard_filter)
    except Exception as e:
        return IFRSAnswer(
            status="ABSTAIN",
            answer=f"Error asking IFRS question: {str(e)}",
            citations=[],
            confidence=0.0
        )


def tool_analyze_document(doc_id: str, standard: str = "IFRS 13") -> Feedback:
    """Analyze a document against IFRS standards.
    
    Args:
        doc_id: Document identifier
        standard: IFRS standard to analyze against
        
    Returns:
        Document feedback with checklist items and citations
    """
    try:
        return analyze_document(doc_id, standard)
    except Exception as e:
        from app.agents.feedback import Feedback
        return Feedback(
            status="ABSTAIN",
            summary=f"Error analyzing document: {str(e)}",
            items=[],
            confidence=0.0
        )


def tool_search_documents(term: str) -> List[Dict[str, Any]]:
    """Search for documents matching a term.
    
    Args:
        term: Search term
        
    Returns:
        List of matching documents with metadata
    """
    try:
        # Get collection
        client = get_vector_store()
        collection = get_collection(client, "ifrs_documents")
        
        # Search for documents containing the term
        matching_docs = []
        seen_doc_ids = set()
        
        for doc in collection.get("documents", []):
            content = doc.get("content", "").lower()
            metadata = doc.get("metadata", {})
            doc_id = metadata.get("doc_id", "")
            
            # Check if term appears in content and we haven't seen this doc_id
            if term.lower() in content and doc_id and doc_id not in seen_doc_ids:
                seen_doc_ids.add(doc_id)
                
                # Extract title from content (first line or first 50 chars)
                title = content.split('\n')[0][:50] if content else "Untitled Document"
                if len(title) > 50:
                    title = title[:47] + "..."
                
                # Extract tags from metadata
                tags = []
                if metadata.get("standard"):
                    tags.append(metadata["standard"])
                if metadata.get("section"):
                    tags.append(metadata["section"])
                if metadata.get("paragraph"):
                    tags.append(f"Para {metadata['paragraph']}")
                
                matching_docs.append({
                    "doc_id": doc_id,
                    "title": title,
                    "tags": tags,
                    "relevance_score": content.count(term.lower()) / len(content) if content else 0
                })
        
        # Sort by relevance score
        matching_docs.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return matching_docs[:10]  # Return top 10 matches
        
    except Exception as e:
        return [{
            "doc_id": "error",
            "title": f"Search error: {str(e)}",
            "tags": ["error"],
            "relevance_score": 0
        }]


def get_available_tools() -> Dict[str, Any]:
    """Get information about available tools.
    
    Returns:
        Dictionary describing available tools
    """
    return {
        "tools": [
            {
                "name": "ifrs_ask",
                "description": "Ask questions about IFRS standards",
                "parameters": {
                    "question": "string - Question about IFRS standards",
                    "standard_filter": "string (optional) - Filter by IFRS standard"
                }
            },
            {
                "name": "analyze_document", 
                "description": "Analyze a document against IFRS standards",
                "parameters": {
                    "doc_id": "string - Document identifier",
                    "standard": "string - IFRS standard (default: IFRS 13)"
                }
            },
            {
                "name": "search_documents",
                "description": "Search for documents matching a term",
                "parameters": {
                    "term": "string - Search term"
                }
            }
        ],
        "usage": {
            "ifrs_ask": "Use for general IFRS questions and compliance queries",
            "analyze_document": "Use when user wants to analyze a specific document",
            "search_documents": "Use when user wants to find documents or explore available content"
        }
    }
