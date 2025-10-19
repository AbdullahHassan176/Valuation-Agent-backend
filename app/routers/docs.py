"""
Document management router.
Provides access to document catalog and provenance information.
"""

from fastapi import APIRouter, HTTPException, Depends, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from app.models.documents import DocCatalog, ChunkCatalog, ProvenanceLog
from app.core.security import validate_api_key

router = APIRouter(prefix="/docs", tags=["docs"])

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

@router.get("/")
async def list_documents(
    standard: str = Query(None, description="Filter by IFRS standard"),
    status: str = Query("active", description="Filter by status"),
    limit: int = Query(100, description="Maximum number of documents"),
    offset: int = Query(0, description="Number of documents to skip"),
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """List all documents in the catalog."""
    
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
        documents = query.offset(offset).limit(limit).all()
        
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
                    "status": doc.status,
                    "sha256": doc.sha256
                }
                for doc in documents
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@router.get("/{doc_id}")
async def get_document_detail(
    doc_id: str,
    include_chunks: bool = Query(True, description="Include chunk information"),
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific document."""
    
    # Validate API key
    if not validate_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        # Get document
        doc = db.query(DocCatalog).filter(DocCatalog.doc_id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        result = {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "standard": doc.standard,
            "tags": json.loads(doc.tags) if doc.tags else [],
            "uploaded_by": doc.uploaded_by,
            "uploaded_at": doc.uploaded_at.isoformat(),
            "file_size": doc.file_size,
            "file_type": doc.file_type,
            "status": doc.status,
            "sha256": doc.sha256
        }
        
        # Include chunks if requested
        if include_chunks:
            chunks = db.query(ChunkCatalog).filter(ChunkCatalog.doc_id == doc_id).all()
            result["chunks"] = [
                {
                    "chunk_id": chunk.chunk_id,
                    "page_from": chunk.page_from,
                    "page_to": chunk.page_to,
                    "chunk_text": chunk.chunk_text[:200] + "..." if len(chunk.chunk_text) > 200 else chunk.chunk_text,
                    "vector_id": chunk.vector_id,
                    "created_at": chunk.created_at.isoformat(),
                    "sha256": chunk.sha256
                }
                for chunk in chunks
            ]
            result["chunk_count"] = len(chunks)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting document detail: {str(e)}")

@router.get("/{doc_id}/chunks")
async def get_document_chunks(
    doc_id: str,
    limit: int = Query(100, description="Maximum number of chunks"),
    offset: int = Query(0, description="Number of chunks to skip"),
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get all chunks for a specific document."""
    
    # Validate API key
    if not validate_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        # Check if document exists
        doc = db.query(DocCatalog).filter(DocCatalog.doc_id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get chunks
        query = db.query(ChunkCatalog).filter(ChunkCatalog.doc_id == doc_id)
        total_count = query.count()
        
        chunks = query.offset(offset).limit(limit).all()
        
        return {
            "doc_id": doc_id,
            "title": doc.title,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "chunks": [
                {
                    "chunk_id": chunk.chunk_id,
                    "page_from": chunk.page_from,
                    "page_to": chunk.page_to,
                    "chunk_text": chunk.chunk_text,
                    "vector_id": chunk.vector_id,
                    "created_at": chunk.created_at.isoformat(),
                    "sha256": chunk.sha256
                }
                for chunk in chunks
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting document chunks: {str(e)}")

@router.get("/provenance/{answer_id}")
async def get_answer_provenance(
    answer_id: str,
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get provenance information for a specific answer."""
    
    # Validate API key
    if not validate_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        # Get provenance entries
        provenance_entries = db.query(ProvenanceLog).filter(
            ProvenanceLog.answer_id == answer_id
        ).all()
        
        if not provenance_entries:
            raise HTTPException(status_code=404, detail="No provenance found for this answer")
        
        # Get document and chunk details
        result = {
            "answer_id": answer_id,
            "provenance_count": len(provenance_entries),
            "sources": []
        }
        
        for entry in provenance_entries:
            # Get document info
            doc = db.query(DocCatalog).filter(DocCatalog.doc_id == entry.doc_id).first()
            
            # Get chunk info
            chunk = db.query(ChunkCatalog).filter(ChunkCatalog.chunk_id == entry.chunk_id).first()
            
            source_info = {
                "doc_id": entry.doc_id,
                "chunk_id": entry.chunk_id,
                "relevance_score": entry.relevance_score,
                "document": {
                    "title": doc.title if doc else "Unknown",
                    "standard": doc.standard if doc else None,
                    "uploaded_at": doc.uploaded_at.isoformat() if doc else None
                },
                "chunk": {
                    "page_from": chunk.page_from if chunk else None,
                    "page_to": chunk.page_to if chunk else None,
                    "chunk_text": chunk.chunk_text[:200] + "..." if chunk and len(chunk.chunk_text) > 200 else (chunk.chunk_text if chunk else None)
                } if chunk else None
            }
            
            result["sources"].append(source_info)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting provenance: {str(e)}")

@router.get("/standards/")
async def list_standards(
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """List all IFRS standards in the catalog."""
    
    # Validate API key
    if not validate_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        # Get unique standards
        standards = db.query(DocCatalog.standard).filter(
            DocCatalog.standard.isnot(None),
            DocCatalog.status == "active"
        ).distinct().all()
        
        # Get document counts for each standard
        result = []
        for standard in standards:
            count = db.query(DocCatalog).filter(
                DocCatalog.standard == standard[0],
                DocCatalog.status == "active"
            ).count()
            
            result.append({
                "standard": standard[0],
                "document_count": count
            })
        
        return {
            "standards": result,
            "total_standards": len(result)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing standards: {str(e)}")

@router.get("/stats/")
async def get_catalog_stats(
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get catalog statistics."""
    
    # Validate API key
    if not validate_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        # Get document stats
        total_docs = db.query(DocCatalog).count()
        active_docs = db.query(DocCatalog).filter(DocCatalog.status == "active").count()
        
        # Get chunk stats
        total_chunks = db.query(ChunkCatalog).count()
        
        # Get provenance stats
        total_provenance = db.query(ProvenanceLog).count()
        
        # Get standards stats
        standards_count = db.query(DocCatalog.standard).filter(
            DocCatalog.standard.isnot(None)
        ).distinct().count()
        
        # Get recent activity
        recent_docs = db.query(DocCatalog).filter(
            DocCatalog.uploaded_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        return {
            "documents": {
                "total": total_docs,
                "active": active_docs,
                "recent_uploads": recent_docs
            },
            "chunks": {
                "total": total_chunks
            },
            "provenance": {
                "total_entries": total_provenance
            },
            "standards": {
                "unique_count": standards_count
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting catalog stats: {str(e)}")
