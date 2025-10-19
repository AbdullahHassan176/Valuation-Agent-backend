"""Vector store utilities (simplified version without ChromaDB)."""

import os
import json
from typing import List, Dict, Any, Optional
from app.models.documents import Chunk
from app.settings import settings


def get_vector_store(persist_directory: Optional[str] = None):
    """Get or create simple file-based vector store.
    
    Args:
        persist_directory: Directory to persist the database
        
    Returns:
        Dictionary representing the store
    """
    if persist_directory is None:
        persist_directory = settings.VECTOR_DIR
    
    # Ensure directory exists
    os.makedirs(persist_directory, exist_ok=True)
    
    # Return a simple dictionary for now
    return {"path": persist_directory}


def get_collection(client: dict, collection_name: str = "ifrs_documents"):
    """Get or create a collection in the vector store.
    
    Args:
        client: Store client
        collection_name: Name of the collection
        
    Returns:
        Collection metadata
    """
    collection_file = os.path.join(client["path"], f"{collection_name}.json")
    
    if os.path.exists(collection_file):
        with open(collection_file, 'r') as f:
            return json.load(f)
    else:
        collection = {
            "name": collection_name,
            "metadata": {"description": "IFRS documents and standards"},
            "documents": []
        }
        with open(collection_file, 'w') as f:
            json.dump(collection, f, indent=2)
        return collection


def upsert_chunks(chunks: List[Chunk], collection_name: str = "ifrs_documents") -> int:
    """Upsert chunks into the vector store.
    
    Args:
        chunks: List of Chunk objects to upsert
        collection_name: Name of the collection
        
    Returns:
        Number of chunks upserted
        
    Raises:
        Exception: If upsert fails
    """
    try:
        # Get vector store and collection
        client = get_vector_store()
        collection = get_collection(client, collection_name)
        
        # Prepare data for upsert
        for i, chunk in enumerate(chunks):
            # Create unique ID for each chunk
            chunk_id = f"{chunk.doc_id}_{i}"
            
            # Prepare metadata with provenance
            metadata = {
                "doc_id": chunk.doc_id,
                "document_id": chunk.doc_id,  # For provenance tracking
                "chunk_id": chunk_id,  # For provenance tracking
                "page_from": chunk.page_from,
                "page_to": chunk.page_to,
                "chunk_index": i,
                "chunk_size": len(chunk.content)
            }
            
            # Add optional metadata
            if chunk.standard:
                metadata["standard"] = chunk.standard
            if chunk.section:
                metadata["section"] = chunk.section
            if chunk.paragraph:
                metadata["paragraph"] = chunk.paragraph
            
            # Add any additional metadata from chunk
            if chunk.metadata:
                metadata.update(chunk.metadata)
            
            # Add document to collection
            document = {
                "id": chunk_id,
                "content": chunk.content,
                "metadata": metadata
            }
            
            collection["documents"].append(document)
        
        # Save collection back to file
        collection_file = os.path.join(client["path"], f"{collection_name}.json")
        with open(collection_file, 'w') as f:
            json.dump(collection, f, indent=2)
        
        return len(chunks)
    
    except Exception as e:
        raise Exception(f"Error upserting chunks: {e}")


def search_similar(
    query: str,
    collection_name: str = "ifrs_documents",
    n_results: int = 5,
    where: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Search for similar documents in the vector store.
    
    Args:
        query: Search query
        collection_name: Name of the collection
        n_results: Number of results to return
        where: Optional metadata filter
        
    Returns:
        List of search results with metadata
        
    Raises:
        Exception: If search fails
    """
    try:
        # Get vector store and collection
        client = get_vector_store()
        collection = get_collection(client, collection_name)
        
        # Simple text search for now
        results = []
        for doc in collection["documents"]:
            if query.lower() in doc["content"].lower():
                result = {
                    'content': doc["content"],
                    'metadata': doc["metadata"]
                }
                results.append(result)
        
        return results[:n_results]
    
    except Exception as e:
        raise Exception(f"Error searching vector store: {e}")


def get_collection_count(collection_name: str = "ifrs_documents") -> int:
    """Get the number of documents in the collection.
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        Number of documents in the collection
        
    Raises:
        Exception: If count fails
    """
    try:
        # Get vector store and collection
        client = get_vector_store()
        collection = get_collection(client, collection_name)
        
        # Get count
        return len(collection["documents"])
    
    except Exception as e:
        raise Exception(f"Error getting collection count: {e}")


def delete_document(doc_id: str, collection_name: str = "ifrs_documents") -> bool:
    """Delete all chunks for a specific document.
    
    Args:
        doc_id: Document identifier
        collection_name: Name of the collection
        
    Returns:
        True if deletion was successful
        
    Raises:
        Exception: If deletion fails
    """
    try:
        # Get vector store and collection
        client = get_vector_store()
        collection = get_collection(client, collection_name)
        
        # Filter out documents with matching doc_id
        original_count = len(collection["documents"])
        collection["documents"] = [
            doc for doc in collection["documents"] 
            if doc["metadata"].get("doc_id") != doc_id
        ]
        
        # Save collection back to file
        collection_file = os.path.join(client["path"], f"{collection_name}.json")
        with open(collection_file, 'w') as f:
            json.dump(collection, f, indent=2)
        
        return len(collection["documents"]) < original_count
    
    except Exception as e:
        raise Exception(f"Error deleting document {doc_id}: {e}")
