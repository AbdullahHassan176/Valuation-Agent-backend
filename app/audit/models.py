"""Audit models for persisting interactions and citations."""

from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, create_engine, Session
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import relationship


class InteractionBase(SQLModel):
    """Base interaction model."""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user: str = Field(default="anonymous", description="User identifier")
    question: str = Field(..., description="User question or request")
    intent: str = Field(..., description="Classified intent (ask_ifrs, analyze_doc, search_docs, unknown)")
    response: str = Field(..., description="Generated response text")
    status: str = Field(..., description="Response status (OK, ABSTAIN, NEEDS_REVIEW)")
    confidence: float = Field(..., description="Confidence score 0-1")
    model: str = Field(default="valuation-agent", description="Model version used")
    vector_dir: str = Field(default="", description="Vector store directory used")
    tool_used: Optional[str] = Field(default=None, description="Tool used for response")
    doc_id: Optional[str] = Field(default=None, description="Document ID if applicable")


class Interaction(InteractionBase, table=True):
    """Interaction audit table."""
    
    __tablename__ = "interactions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    citations: List["InteractionCitation"] = Relationship(back_populates="interaction")
    documents: List["InteractionDocument"] = Relationship(back_populates="interaction")


class InteractionCitationBase(SQLModel):
    """Base citation model."""
    
    standard: str = Field(..., description="IFRS standard (e.g., IFRS 13)")
    paragraph: str = Field(..., description="Paragraph reference")
    section: Optional[str] = Field(default=None, description="Section reference")


class InteractionCitation(InteractionCitationBase, table=True):
    """Interaction citations table."""
    
    __tablename__ = "interaction_citations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    interaction_id: int = Field(foreign_key="interactions.id")
    
    # Relationships
    interaction: Optional[Interaction] = Relationship(back_populates="citations")


class InteractionDocumentBase(SQLModel):
    """Base document model."""
    
    doc_id: str = Field(..., description="Document identifier")


class InteractionDocument(InteractionDocumentBase, table=True):
    """Interaction documents table."""
    
    __tablename__ = "interaction_documents"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    interaction_id: int = Field(foreign_key="interactions.id")
    
    # Relationships
    interaction: Optional[Interaction] = Relationship(back_populates="documents")


class AuditDatabase:
    """Audit database manager."""
    
    def __init__(self, database_url: str):
        """Initialize audit database.
        
        Args:
            database_url: SQLite database URL
        """
        self.engine = create_engine(database_url, echo=False)
        self.database_url = database_url
    
    def create_tables(self):
        """Create all audit tables."""
        SQLModel.metadata.create_all(self.engine)
    
    def get_session(self) -> Session:
        """Get database session.
        
        Returns:
            Database session
        """
        return Session(self.engine)
    
    def log_interaction(
        self,
        user: str,
        question: str,
        intent: str,
        response: str,
        status: str,
        confidence: float,
        model: str = "valuation-agent",
        vector_dir: str = "",
        tool_used: Optional[str] = None,
        doc_id: Optional[str] = None,
        citations: Optional[List[dict]] = None,
        documents: Optional[List[str]] = None
    ) -> int:
        """Log an interaction to the audit database.
        
        Args:
            user: User identifier
            question: User question
            intent: Classified intent
            response: Generated response
            status: Response status
            confidence: Confidence score
            model: Model version
            vector_dir: Vector store directory
            tool_used: Tool used for response
            doc_id: Document ID if applicable
            citations: List of citation dictionaries
            documents: List of document IDs
            
        Returns:
            Interaction ID
        """
        with self.get_session() as session:
            # Create interaction record
            interaction = Interaction(
                user=user,
                question=question,
                intent=intent,
                response=response,
                status=status,
                confidence=confidence,
                model=model,
                vector_dir=vector_dir,
                tool_used=tool_used,
                doc_id=doc_id
            )
            
            session.add(interaction)
            session.commit()
            session.refresh(interaction)
            
            interaction_id = interaction.id
            
            # Add citations if provided
            if citations:
                for citation in citations:
                    citation_record = InteractionCitation(
                        interaction_id=interaction_id,
                        standard=citation.get("standard", ""),
                        paragraph=citation.get("paragraph", ""),
                        section=citation.get("section")
                    )
                    session.add(citation_record)
            
            # Add documents if provided
            if documents:
                for doc in documents:
                    doc_record = InteractionDocument(
                        interaction_id=interaction_id,
                        doc_id=doc
                    )
                    session.add(doc_record)
            
            session.commit()
            return interaction_id
    
    def get_interactions(self, limit: int = 100) -> List[Interaction]:
        """Get recent interactions.
        
        Args:
            limit: Maximum number of interactions to return
            
        Returns:
            List of interactions
        """
        with self.get_session() as session:
            return session.query(Interaction).order_by(Interaction.timestamp.desc()).limit(limit).all()
    
    def get_interaction_stats(self) -> dict:
        """Get interaction statistics.
        
        Returns:
            Statistics dictionary
        """
        with self.get_session() as session:
            total_interactions = session.query(Interaction).count()
            ok_responses = session.query(Interaction).filter(Interaction.status == "OK").count()
            abstain_responses = session.query(Interaction).filter(Interaction.status == "ABSTAIN").count()
            avg_confidence = session.query(Interaction).with_entities(
                session.query(Interaction).with_entities(Interaction.confidence).label('avg_conf')
            ).scalar() or 0.0
            
            return {
                "total_interactions": total_interactions,
                "ok_responses": ok_responses,
                "abstain_responses": abstain_responses,
                "average_confidence": avg_confidence,
                "success_rate": (ok_responses / total_interactions * 100) if total_interactions > 0 else 0
            }


# Global audit database instance
audit_db: Optional[AuditDatabase] = None


def get_audit_db() -> AuditDatabase:
    """Get audit database instance.
    
    Returns:
        Audit database instance
    """
    global audit_db
    if audit_db is None:
        from app.settings import settings
        audit_db = AuditDatabase(settings.LOG_DB)
        audit_db.create_tables()
    return audit_db


def log_interaction(
    user: str,
    question: str,
    intent: str,
    response: str,
    status: str,
    confidence: float,
    model: str = "valuation-agent",
    vector_dir: str = "",
    tool_used: Optional[str] = None,
    doc_id: Optional[str] = None,
    citations: Optional[List[dict]] = None,
    documents: Optional[List[str]] = None
) -> int:
    """Log an interaction to the audit database.
    
    Args:
        user: User identifier
        question: User question
        intent: Classified intent
        response: Generated response
        status: Response status
        confidence: Confidence score
        model: Model version
        vector_dir: Vector store directory
        tool_used: Tool used for response
        doc_id: Document ID if applicable
        citations: List of citation dictionaries
        documents: List of document IDs
        
    Returns:
        Interaction ID
    """
    db = get_audit_db()
    return db.log_interaction(
        user=user,
        question=question,
        intent=intent,
        response=response,
        status=status,
        confidence=confidence,
        model=model,
        vector_dir=vector_dir,
        tool_used=tool_used,
        doc_id=doc_id,
        citations=citations,
        documents=documents
    )
