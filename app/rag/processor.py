"""
Document processing pipeline with catalog integration.
Handles document ingestion, chunking, and vector store integration.
"""

import os
import json
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from datetime import datetime

from app.models.documents import DocCatalog, ChunkCatalog, create_doc_catalog_entry, create_chunk_catalog_entry
from app.rag.chunking import chunk_document
from app.rag.store import upsert_chunks
from app.models.documents import Chunk


# Database connection
DATABASE_URL = "sqlite:///./.run/audit.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def process_document(
    content: str,
    title: str,
    standard: str = None,
    tags: List[str] = None,
    uploaded_by: str = "system",
    file_size: int = None,
    file_type: str = None
) -> Dict[str, Any]:
    """Process a document through the full pipeline.
    
    Args:
        content: Document content
        title: Document title
        standard: IFRS standard (optional)
        tags: List of tags (optional)
        uploaded_by: User who uploaded the document
        file_size: File size in bytes
        file_type: MIME type
        
    Returns:
        Processing result with document and chunk information
    """
    try:
        # Generate document ID
        doc_id = str(uuid.uuid4())
        
        # Create document catalog entry
        doc_entry = create_doc_catalog_entry(
            doc_id=doc_id,
            title=title,
            content=content,
            standard=standard,
            tags=tags or [],
            uploaded_by=uploaded_by,
            file_size=file_size,
            file_type=file_type
        )
        
        # Save to database
        db = Session(bind=engine)
        try:
            db.add(doc_entry)
            db.commit()
            db.refresh(doc_entry)
            
            # Process document into chunks
            chunks = chunk_document(content, doc_id, standard)
            
            # Create chunk catalog entries
            chunk_entries = []
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_{i}"
                chunk_entry = create_chunk_catalog_entry(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    chunk_text=chunk.content,
                    page_from=chunk.page_from,
                    page_to=chunk.page_to,
                    vector_id=chunk_id
                )
                
                db.add(chunk_entry)
                chunk_entries.append(chunk_entry)
            
            db.commit()
            
            # Upsert chunks into vector store
            upserted_count = upsert_chunks(chunks, "ifrs_documents")
            
            return {
                "status": "success",
                "doc_id": doc_id,
                "title": title,
                "standard": standard,
                "tags": tags or [],
                "chunk_count": len(chunks),
                "upserted_count": upserted_count,
                "uploaded_at": doc_entry.uploaded_at.isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error processing document: {str(e)}"
        }


def reprocess_document(doc_id: str) -> Dict[str, Any]:
    """Reprocess a document that's already in the catalog.
    
    Args:
        doc_id: Document ID to reprocess
        
    Returns:
        Reprocessing result
    """
    try:
        db = Session(bind=engine)
        try:
            # Get document from catalog
            doc = db.query(DocCatalog).filter(DocCatalog.doc_id == doc_id).first()
            if not doc:
                return {"status": "error", "message": "Document not found"}
            
            # Get existing chunks
            existing_chunks = db.query(ChunkCatalog).filter(ChunkCatalog.doc_id == doc_id).all()
            
            # Delete existing chunks from vector store
            from app.rag.store import delete_document
            delete_document(doc_id, "ifrs_documents")
            
            # Delete existing chunk catalog entries
            for chunk in existing_chunks:
                db.delete(chunk)
            
            # Reprocess document
            chunks = chunk_document(doc.content, doc_id, doc.standard)
            
            # Create new chunk catalog entries
            chunk_entries = []
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_{i}"
                chunk_entry = create_chunk_catalog_entry(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    chunk_text=chunk.content,
                    page_from=chunk.page_from,
                    page_to=chunk.page_to,
                    vector_id=chunk_id
                )
                
                db.add(chunk_entry)
                chunk_entries.append(chunk_entry)
            
            db.commit()
            
            # Upsert chunks into vector store
            upserted_count = upsert_chunks(chunks, "ifrs_documents")
            
            return {
                "status": "success",
                "doc_id": doc_id,
                "chunk_count": len(chunks),
                "upserted_count": upserted_count,
                "reprocessed_at": datetime.utcnow().isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        return {"status": "error", "message": f"Error reprocessing document: {str(e)}"}


def get_document_provenance(doc_id: str) -> Dict[str, Any]:
    """Get provenance information for a document.
    
    Args:
        doc_id: Document ID
        
    Returns:
        Provenance information including document and chunk details
    """
    try:
        db = Session(bind=engine)
        try:
            # Get document
            doc = db.query(DocCatalog).filter(DocCatalog.doc_id == doc_id).first()
            if not doc:
                return {"status": "error", "message": "Document not found"}
            
            # Get chunks
            chunks = db.query(ChunkCatalog).filter(ChunkCatalog.doc_id == doc_id).all()
            
            return {
                "status": "success",
                "document": {
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "standard": doc.standard,
                    "tags": json.loads(doc.tags) if doc.tags else [],
                    "uploaded_by": doc.uploaded_by,
                    "uploaded_at": doc.uploaded_at.isoformat(),
                    "file_size": doc.file_size,
                    "file_type": doc.file_type,
                    "status": doc.status
                },
                "chunks": [
                    {
                        "chunk_id": chunk.chunk_id,
                        "page_from": chunk.page_from,
                        "page_to": chunk.page_to,
                        "vector_id": chunk.vector_id,
                        "created_at": chunk.created_at.isoformat()
                    }
                    for chunk in chunks
                ],
                "chunk_count": len(chunks)
            }
            
        finally:
            db.close()
            
    except Exception as e:
        return {"status": "error", "message": f"Error getting provenance: {str(e)}"}
