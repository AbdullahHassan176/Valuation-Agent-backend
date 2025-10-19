"""Embedding utilities for vector storage (simplified version)."""

from typing import List, Optional
from app.settings import settings


def get_embeddings():
    """Get embeddings model based on configuration.
    
    Returns:
        Embeddings model instance (simplified for now)
        
    Raises:
        ValueError: If no valid API key is configured
    """
    # For now, return a simple mock embeddings model
    # In production, this would use actual OpenAI/Azure embeddings
    return MockEmbeddings()


class MockEmbeddings:
    """Mock embeddings model for testing."""
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Mock embedding of documents."""
        # Return simple hash-based embeddings for testing
        import hashlib
        embeddings = []
        for text in texts:
            # Create a simple hash-based embedding
            hash_obj = hashlib.md5(text.encode())
            hash_bytes = hash_obj.digest()
            # Convert to float vector
            embedding = [float(b) / 255.0 for b in hash_bytes[:8]]  # Use first 8 bytes
            embeddings.append(embedding)
        return embeddings
    
    def embed_query(self, query: str) -> List[float]:
        """Mock embedding of query."""
        return self.embed_documents([query])[0]


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a list of texts.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        List of embedding vectors
        
    Raises:
        Exception: If embedding fails
    """
    try:
        embeddings_model = get_embeddings()
        return embeddings_model.embed_documents(texts)
    except Exception as e:
        raise Exception(f"Error embedding texts: {e}")


def embed_query(query: str) -> List[float]:
    """Embed a single query string.
    
    Args:
        query: Query string to embed
        
    Returns:
        Embedding vector
        
    Raises:
        Exception: If embedding fails
    """
    try:
        embeddings_model = get_embeddings()
        return embeddings_model.embed_query(query)
    except Exception as e:
        raise Exception(f"Error embedding query: {e}")
