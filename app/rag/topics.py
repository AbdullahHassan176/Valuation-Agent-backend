"""
Domain-specific retrievers for IFRS topics.
"""

from typing import Literal, Optional, List, Dict, Any
from app.rag.store import get_vector_store
from app.rag.retriever import build_retriever

# Topic to standard mapping
TOPIC_MAPPING = {
    "ifrs9_impairment": "IFRS 9",
    "ifrs16_leases": "IFRS 16", 
    "ifrs13_measurement": "IFRS 13"
}

def build_topic_retriever(topic: Literal["ifrs9_impairment", "ifrs16_leases", "ifrs13_measurement"]) -> Any:
    """
    Build a topic-specific retriever that filters by IFRS standard.
    
    Args:
        topic: The IFRS topic to retrieve documents for
        
    Returns:
        A retriever configured for the specific topic
    """
    if topic not in TOPIC_MAPPING:
        raise ValueError(f"Unknown topic: {topic}. Must be one of {list(TOPIC_MAPPING.keys())}")
    
    standard = TOPIC_MAPPING[topic]
    
    # Create a topic-specific vector store with metadata filtering
    topic_store = get_vector_store(persist_directory=".vector/ifrs")
    
    # Build retriever with topic-specific filtering
    retriever = build_retriever(
        vector_store=topic_store,
        k=5,  # Retrieve top 5 documents
        filter_metadata={"standard": standard}  # Filter by IFRS standard
    )
    
    return retriever

def get_topic_standards() -> Dict[str, str]:
    """
    Get the mapping of topics to IFRS standards.
    
    Returns:
        Dictionary mapping topic names to IFRS standard names
    """
    return TOPIC_MAPPING.copy()

def get_available_topics() -> List[str]:
    """
    Get list of available topics.
    
    Returns:
        List of available topic names
    """
    return list(TOPIC_MAPPING.keys())

def get_standard_for_topic(topic: str) -> Optional[str]:
    """
    Get the IFRS standard for a given topic.
    
    Args:
        topic: The topic name
        
    Returns:
        The IFRS standard name, or None if topic not found
    """
    return TOPIC_MAPPING.get(topic)
