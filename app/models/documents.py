"""
Document catalog and provenance models.
Tracks source documents and chunk lineage for transparency.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import hashlib

Base = declarative_base()


class Page(Base):
    """Page model for document pages."""
    
    __tablename__ = "pages"
    
    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(String(255), ForeignKey("doc_catalog.doc_id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Chunk(Base):
    """Chunk model for document chunks."""
    
    __tablename__ = "chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(String(255), ForeignKey("doc_catalog.doc_id"), nullable=False)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=True)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DocCatalog(Base):
    """Document catalog table for tracking source documents."""
    
    __tablename__ = "doc_catalog"
    
    doc_id = Column(String(255), primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    standard = Column(String(100), nullable=True)  # IFRS 13, IFRS 9, etc.
    tags = Column(Text, nullable=True)  # JSON string of tags
    sha256 = Column(String(64), nullable=False, unique=True)
    uploaded_by = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String(50), nullable=True)
    status = Column(String(50), default='active', nullable=False)
    
    # Relationships
    chunks = relationship("ChunkCatalog", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DocCatalog(doc_id='{self.doc_id}', title='{self.title}', standard='{self.standard}')>"


class ChunkCatalog(Base):
    """Chunk catalog table for tracking document chunks."""
    
    __tablename__ = "chunk_catalog"
    
    chunk_id = Column(String(255), primary_key=True, index=True)
    doc_id = Column(String(255), ForeignKey('doc_catalog.doc_id'), nullable=False)
    page_from = Column(Integer, nullable=True)
    page_to = Column(Integer, nullable=True)
    chunk_text = Column(Text, nullable=False)
    sha256 = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    vector_id = Column(String(255), nullable=True, index=True)  # Reference to vector store
    
    # Relationships
    document = relationship("DocCatalog", back_populates="chunks")
    
    def __repr__(self):
        return f"<ChunkCatalog(chunk_id='{self.chunk_id}', doc_id='{self.doc_id}', pages={self.page_from}-{self.page_to})>"


class ProvenanceLog(Base):
    """Provenance log for tracking data lineage in answers."""
    
    __tablename__ = "provenance_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    answer_id = Column(String(255), nullable=False, index=True)
    doc_id = Column(String(255), ForeignKey('doc_catalog.doc_id'), nullable=False)
    chunk_id = Column(String(255), ForeignKey('chunk_catalog.chunk_id'), nullable=False)
    relevance_score = Column(String(20), nullable=True)  # High, Medium, Low
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("DocCatalog")
    chunk = relationship("ChunkCatalog")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_answer_doc', 'answer_id', 'doc_id'),
        Index('idx_answer_chunk', 'answer_id', 'chunk_id'),
    )
    
    def __repr__(self):
        return f"<ProvenanceLog(answer_id='{self.answer_id}', doc_id='{self.doc_id}', chunk_id='{self.chunk_id}')>"


def calculate_sha256(content: str) -> str:
    """Calculate SHA256 hash of content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def create_doc_catalog_entry(
    doc_id: str,
    title: str,
    content: str,
    standard: str = None,
    tags: list = None,
    uploaded_by: str = "system",
    file_size: int = None,
    file_type: str = None
) -> DocCatalog:
    """Create a new document catalog entry."""
    sha256 = calculate_sha256(content)
    
    return DocCatalog(
        doc_id=doc_id,
        title=title,
        standard=standard,
        tags=json.dumps(tags) if tags else None,
        sha256=sha256,
        uploaded_by=uploaded_by,
        file_size=file_size,
        file_type=file_type
    )


def create_chunk_catalog_entry(
    chunk_id: str,
    doc_id: str,
    chunk_text: str,
    page_from: int = None,
    page_to: int = None,
    vector_id: str = None
) -> ChunkCatalog:
    """Create a new chunk catalog entry."""
    sha256 = calculate_sha256(chunk_text)
    
    return ChunkCatalog(
        chunk_id=chunk_id,
        doc_id=doc_id,
        chunk_text=chunk_text,
        page_from=page_from,
        page_to=page_to,
        sha256=sha256,
        vector_id=vector_id
    )


def create_provenance_entry(
    answer_id: str,
    doc_id: str,
    chunk_id: str,
    relevance_score: str = None
) -> ProvenanceLog:
    """Create a new provenance log entry."""
    return ProvenanceLog(
        answer_id=answer_id,
        doc_id=doc_id,
        chunk_id=chunk_id,
        relevance_score=relevance_score
    )


# Import json for the create_doc_catalog_entry function
import json