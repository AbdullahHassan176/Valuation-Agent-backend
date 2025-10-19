"""
Document ingestion router with catalog integration.
Handles document upload and catalog management.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Header
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from datetime import datetime
import uuid
import hashlib
import json
from pathlib import Path

from app.models.documents import (
    DocCatalog, ChunkCatalog, ProvenanceLog,
    create_doc_catalog_entry, create_chunk_catalog_entry
)
from app.rag.processor import process_document, reprocess_document, get_document_provenance
from app.core.security import validate_api_key

router = APIRouter(prefix="/ingest", tags=["ingest"])

# Database connection
DATABASE_URL = "sqlite:///./.run/audit.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def get_db():
    """Get database session."""
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    standard: str = None,
    tags: str = None,
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """Upload and catalog a new document."""
    
    # Validate API key
    if not validate_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Parse tags if provided
        tag_list = []
        if tags:
            try:
                tag_list = json.loads(tags)
            except json.JSONDecodeError:
                tag_list = [tags]
        
        # Process document through full pipeline
        result = process_document(
            content=content_str,
            title=file.filename,
            standard=standard,
            tags=tag_list,
            uploaded_by="api_user",  # In real implementation, get from auth
            file_size=len(content),
            file_type=file.content_type
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        return result
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

@router.post("/chunk")
async def create_chunk(
    doc_id: str,
    chunk_text: str,
    page_from: int = None,
    page_to: int = None,
    vector_id: str = None,
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """Create a new chunk for a document."""
    
    # Validate API key
    if not validate_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        # Check if document exists
        doc = db.query(DocCatalog).filter(DocCatalog.doc_id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Generate chunk ID
        chunk_id = str(uuid.uuid4())
        
        # Create chunk catalog entry
        chunk_entry = create_chunk_catalog_entry(
            chunk_id=chunk_id,
            doc_id=doc_id,
            chunk_text=chunk_text,
            page_from=page_from,
            page_to=page_to,
            vector_id=vector_id
        )
        
        # Save to database
        db.add(chunk_entry)
        db.commit()
        db.refresh(chunk_entry)
        
        return {
            "status": "success",
            "chunk_id": chunk_id,
            "doc_id": doc_id,
            "page_range": f"{page_from}-{page_to}" if page_from and page_to else None,
            "vector_id": vector_id,
            "created_at": chunk_entry.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating chunk: {str(e)}")

@router.post("/provenance")
async def log_provenance(
    answer_id: str,
    doc_ids: List[str],
    chunk_ids: List[str],
    relevance_scores: List[str] = None,
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """Log provenance information for an answer."""
    
    # Validate API key
    if not validate_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        # Ensure we have matching lengths
        if len(doc_ids) != len(chunk_ids):
            raise HTTPException(status_code=400, detail="doc_ids and chunk_ids must have same length")
        
        if relevance_scores and len(relevance_scores) != len(doc_ids):
            raise HTTPException(status_code=400, detail="relevance_scores must have same length as doc_ids")
        
        # Create provenance entries
        provenance_entries = []
        for i, (doc_id, chunk_id) in enumerate(zip(doc_ids, chunk_ids)):
            relevance_score = relevance_scores[i] if relevance_scores else None
            
            entry = ProvenanceLog(
                answer_id=answer_id,
                doc_id=doc_id,
                chunk_id=chunk_id,
                relevance_score=relevance_score
            )
            
            db.add(entry)
            provenance_entries.append(entry)
        
        db.commit()
        
        return {
            "status": "success",
            "answer_id": answer_id,
            "provenance_count": len(provenance_entries),
            "logged_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error logging provenance: {str(e)}")

@router.get("/status/{doc_id}")
async def get_document_status(
    doc_id: str,
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get the status of a document and its chunks."""
    
    # Validate API key
    if not validate_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        # Get document
        doc = db.query(DocCatalog).filter(DocCatalog.doc_id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get chunks
        chunks = db.query(ChunkCatalog).filter(ChunkCatalog.doc_id == doc_id).all()
        
        return {
            "doc_id": doc_id,
            "title": doc.title,
            "standard": doc.standard,
            "status": doc.status,
            "uploaded_at": doc.uploaded_at.isoformat(),
            "chunk_count": len(chunks),
            "chunks": [
                {
                    "chunk_id": chunk.chunk_id,
                    "page_range": f"{chunk.page_from}-{chunk.page_to}" if chunk.page_from and chunk.page_to else None,
                    "vector_id": chunk.vector_id,
                    "created_at": chunk.created_at.isoformat()
                }
                for chunk in chunks
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting document status: {str(e)}")

@router.delete("/document/{doc_id}")
async def delete_document(
    doc_id: str,
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """Delete a document and all its chunks."""
    
    # Validate API key
    if not validate_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        # Get document
        doc = db.query(DocCatalog).filter(DocCatalog.doc_id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete chunks (cascade should handle this)
        db.query(ChunkCatalog).filter(ChunkCatalog.doc_id == doc_id).delete()
        
        # Delete document
        db.delete(doc)
        db.commit()
        
        return {
            "status": "success",
            "doc_id": doc_id,
            "deleted_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@router.get("/catalog")
async def get_catalog(
    standard: str = None,
    status: str = "active",
    limit: int = 100,
    offset: int = 0,
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get document catalog with optional filtering."""
    
    # Validate API key
    if not validate_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        # Build query
        query = db.query(DocCatalog).filter(DocCatalog.status == status)
        
        if standard:
            query = query.filter(DocCatalog.standard == standard)
        
        # Get total count
        total_count = query.count()
        
        # Get paginated results
        docs = query.offset(offset).limit(limit).all()
        
        return {
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "documents": [
                {
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "standard": doc.standard,
                    "tags": json.loads(doc.tags) if doc.tags else [],
                    "uploaded_by": doc.uploaded_by,
                    "uploaded_at": doc.uploaded_at.isoformat(),
                    "file_size": doc.file_size,
                    "file_type": doc.file_type,
                    "status": doc.status
                }
                for doc in docs
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting catalog: {str(e)}")

@router.post("/reprocess/{doc_id}")
async def reprocess_document_endpoint(
    doc_id: str,
    x_api_key: str = Header(None)
):
    """Reprocess a document that's already in the catalog."""
    
    # Validate API key
    if not validate_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        result = reprocess_document(doc_id)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reprocessing document: {str(e)}")

@router.get("/provenance/{doc_id}")
async def get_document_provenance_endpoint(
    doc_id: str,
    x_api_key: str = Header(None)
):
    """Get provenance information for a document."""
    
    # Validate API key
    if not validate_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        result = get_document_provenance(doc_id)
        
        if result["status"] == "error":
            raise HTTPException(status_code=404, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting provenance: {str(e)}")