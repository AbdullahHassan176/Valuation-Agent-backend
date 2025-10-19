"""Text chunking utilities for document processing."""

from typing import List, Optional
from app.models.documents import Page, Chunk


def chunk_pages(
    pages: List[Page], 
    doc_id: str,
    standard: Optional[str] = None,
    section: Optional[str] = None,
    paragraph: Optional[str] = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 150
) -> List[Chunk]:
    """Split pages into chunks with metadata enrichment.
    
    Args:
        pages: List of Page objects to chunk
        doc_id: Document identifier
        standard: IFRS standard reference
        section: Document section
        paragraph: Document paragraph
        chunk_size: Maximum chunk size in characters
        chunk_overlap: Overlap between chunks in characters
        
    Returns:
        List of Chunk objects with enriched metadata
    """
    chunks = []
    
    for page in pages:
        # Simple text splitting without langchain
        page_chunks = _split_text(page.content, chunk_size, chunk_overlap)
        
        for i, chunk_text in enumerate(page_chunks):
            # Create chunk with enriched metadata
            chunk = Chunk(
                content=chunk_text,
                doc_id=doc_id,
                page_from=page.page_number,
                page_to=page.page_number,
                standard=standard,
                section=section,
                paragraph=paragraph,
                metadata={
                    'chunk_index': i,
                    'page_number': page.page_number,
                    'source_metadata': page.metadata,
                    'chunk_size': len(chunk_text),
                    'doc_id': doc_id
                }
            )
            chunks.append(chunk)
    
    return chunks


def _split_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """Simple text splitting function."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at a sentence or paragraph boundary
        if end < len(text):
            # Look for sentence endings
            for i in range(end, max(start, end - 100), -1):
                if text[i] in '.!?':
                    end = i + 1
                    break
            else:
                # Look for paragraph breaks
                for i in range(end, max(start, end - 50), -1):
                    if text[i] == '\n':
                        end = i
                        break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position with overlap
        start = end - chunk_overlap
        if start >= len(text):
            break
    
    return chunks


def chunk_text(
    text: str,
    doc_id: str,
    standard: Optional[str] = None,
    section: Optional[str] = None,
    paragraph: Optional[str] = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 150
) -> List[Chunk]:
    """Split text into chunks with metadata enrichment.
    
    Args:
        text: Text content to chunk
        doc_id: Document identifier
        standard: IFRS standard reference
        section: Document section
        paragraph: Document paragraph
        chunk_size: Maximum chunk size in characters
        chunk_overlap: Overlap between chunks in characters
        
    Returns:
        List of Chunk objects with enriched metadata
    """
    # Split the text into chunks
    text_chunks = _split_text(text, chunk_size, chunk_overlap)
    
    chunks = []
    for i, chunk_text in enumerate(text_chunks):
        # Create chunk with enriched metadata
        chunk = Chunk(
            content=chunk_text,
            doc_id=doc_id,
            page_from=1,  # Default to page 1 for single text
            page_to=1,
            standard=standard,
            section=section,
            paragraph=paragraph,
            metadata={
                'chunk_index': i,
                'chunk_size': len(chunk_text),
                'doc_id': doc_id
            }
        )
        chunks.append(chunk)
    
    return chunks
