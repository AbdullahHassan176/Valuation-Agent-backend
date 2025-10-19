"""Document retrieval utilities for RAG system."""

import os
import json
from typing import List, Dict, Any, Optional
from app.settings import settings


def build_retriever(collection: Optional[str] = None, k: int = 6, score_threshold: float = 0.2):
    """Build a document retriever for RAG queries.
    
    Args:
        collection: Collection name (defaults to settings.VECTOR_DIR)
        k: Number of documents to retrieve
        score_threshold: Minimum similarity score threshold
        
    Returns:
        Retriever function that takes a query and returns documents
    """
    if collection is None:
        collection = "ifrs_documents"
    
    def retrieve_documents(query: str) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for a query.
        
        Args:
            query: Search query
            
        Returns:
            List of relevant documents with metadata and scores
        """
        try:
            # Get vector store path
            vector_dir = settings.VECTOR_DIR
            collection_file = os.path.join(vector_dir, f"{collection}.json")
            
            if not os.path.exists(collection_file):
                return []
            
            # Load collection
            with open(collection_file, 'r') as f:
                collection_data = json.load(f)
            
            documents = collection_data.get("documents", [])
            
            # Simple text-based retrieval with scoring
            results = []
            query_lower = query.lower()
            
            for doc in documents:
                content = doc.get("content", "")
                metadata = doc.get("metadata", {})
                
                # Calculate simple relevance score
                score = _calculate_relevance_score(query_lower, content)
                
                if score >= score_threshold:
                    results.append({
                        "content": content,
                        "metadata": metadata,
                        "score": score,
                        "doc_id": metadata.get("doc_id", ""),
                        "standard": metadata.get("standard", ""),
                        "section": metadata.get("section", ""),
                        "paragraph": metadata.get("paragraph", ""),
                        "page_from": metadata.get("page_from", 0),
                        "page_to": metadata.get("page_to", 0),
                        "document_id": metadata.get("document_id", metadata.get("doc_id", "")),
                        "chunk_id": metadata.get("chunk_id", "")
                    })
            
            # Sort by score and return top k
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:k]
        
        except Exception as e:
            print(f"Error retrieving documents: {e}")
            return []
    
    return retrieve_documents


def _calculate_relevance_score(query: str, content: str) -> float:
    """Calculate relevance score between query and content.
    
    Args:
        query: Search query (lowercase)
        content: Document content
        
    Returns:
        Relevance score between 0 and 1
    """
    content_lower = content.lower()
    
    # Simple keyword matching with weights
    query_words = set(query.split())
    content_words = set(content_lower.split())
    
    # Calculate word overlap
    common_words = query_words.intersection(content_words)
    if not query_words:
        return 0.0
    
    word_overlap_score = len(common_words) / len(query_words)
    
    # Calculate phrase matching
    phrase_score = 0.0
    if query in content_lower:
        phrase_score = 1.0
    else:
        # Check for partial phrase matches
        query_phrases = [phrase.strip() for phrase in query.split() if len(phrase.strip()) > 2]
        for phrase in query_phrases:
            if phrase in content_lower:
                phrase_score += 0.3
    
    # Combine scores
    total_score = (word_overlap_score * 0.7) + (min(phrase_score, 1.0) * 0.3)
    
    return min(total_score, 1.0)


def get_document_by_id(doc_id: str, collection: str = "ifrs_documents") -> Optional[Dict[str, Any]]:
    """Get a specific document by ID.
    
    Args:
        doc_id: Document identifier
        collection: Collection name
        
    Returns:
        Document data if found, None otherwise
    """
    try:
        vector_dir = settings.VECTOR_DIR
        collection_file = os.path.join(vector_dir, f"{collection}.json")
        
        if not os.path.exists(collection_file):
            return None
        
        with open(collection_file, 'r') as f:
            collection_data = json.load(f)
        
        documents = collection_data.get("documents", [])
        
        for doc in documents:
            metadata = doc.get("metadata", {})
            if metadata.get("doc_id") == doc_id:
                return doc
        
        return None
    
    except Exception as e:
        print(f"Error getting document by ID: {e}")
        return None


def search_documents(
    query: str, 
    collection: str = "ifrs_documents",
    k: int = 6,
    score_threshold: float = 0.2,
    standard_filter: Optional[str] = None,
    section_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Search documents with optional filters.
    
    Args:
        query: Search query
        collection: Collection name
        k: Number of results to return
        score_threshold: Minimum score threshold
        standard_filter: Filter by IFRS standard
        section_filter: Filter by section
        
    Returns:
        List of relevant documents
    """
    retriever = build_retriever(collection, k, score_threshold)
    results = retriever(query)
    
    # Apply filters
    if standard_filter:
        results = [r for r in results if r.get("standard", "").lower() == standard_filter.lower()]
    
    if section_filter:
        results = [r for r in results if r.get("section", "").lower() == section_filter.lower()]
    
    return results
