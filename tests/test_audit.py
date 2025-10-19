"""Unit tests for the audit system."""

import pytest
import os
import tempfile
from datetime import datetime
from app.audit.models import AuditDatabase, Interaction, InteractionCitation, InteractionDocument, log_interaction, get_audit_db


class TestAuditDatabase:
    """Test audit database functionality."""
    
    def setup_method(self):
        """Set up test database."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_url = f"sqlite:///{self.temp_db.name}"
        
        # Create audit database
        self.audit_db = AuditDatabase(self.db_url)
        self.audit_db.create_tables()
    
    def teardown_method(self):
        """Clean up test database."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_create_tables(self):
        """Test table creation."""
        # Tables should be created without error
        assert True  # If we get here, no exception was raised
    
    def test_log_interaction_basic(self):
        """Test basic interaction logging."""
        interaction_id = self.audit_db.log_interaction(
            user="test_user",
            question="What is fair value measurement?",
            intent="ask_ifrs",
            response="Fair value measurement is...",
            status="OK",
            confidence=0.85,
            model="test-model",
            vector_dir="/test/vector",
            tool_used="ifrs_ask"
        )
        
        assert interaction_id is not None
        assert interaction_id > 0
    
    def test_log_interaction_with_citations(self):
        """Test interaction logging with citations."""
        citations = [
            {"standard": "IFRS 13", "paragraph": "4.1.1", "section": "Fair Value"},
            {"standard": "IFRS 13", "paragraph": "4.1.2", "section": "Measurement"}
        ]
        
        interaction_id = self.audit_db.log_interaction(
            user="test_user",
            question="What is fair value measurement?",
            intent="ask_ifrs",
            response="Fair value measurement is...",
            status="OK",
            confidence=0.85,
            citations=citations
        )
        
        assert interaction_id is not None
        
        # Verify citations were stored
        with self.audit_db.get_session() as session:
            stored_citations = session.query(InteractionCitation).filter(
                InteractionCitation.interaction_id == interaction_id
            ).all()
            
            assert len(stored_citations) == 2
            assert stored_citations[0].standard == "IFRS 13"
            assert stored_citations[0].paragraph == "4.1.1"
            assert stored_citations[1].standard == "IFRS 13"
            assert stored_citations[1].paragraph == "4.1.2"
    
    def test_log_interaction_with_documents(self):
        """Test interaction logging with documents."""
        documents = ["doc1", "doc2", "doc3"]
        
        interaction_id = self.audit_db.log_interaction(
            user="test_user",
            question="Analyze document for compliance",
            intent="analyze_doc",
            response="Document analysis complete",
            status="NEEDS_REVIEW",
            confidence=0.75,
            documents=documents
        )
        
        assert interaction_id is not None
        
        # Verify documents were stored
        with self.audit_db.get_session() as session:
            stored_docs = session.query(InteractionDocument).filter(
                InteractionDocument.interaction_id == interaction_id
            ).all()
            
            assert len(stored_docs) == 3
            doc_ids = [doc.doc_id for doc in stored_docs]
            assert "doc1" in doc_ids
            assert "doc2" in doc_ids
            assert "doc3" in doc_ids
    
    def test_get_interactions(self):
        """Test retrieving interactions."""
        # Log multiple interactions
        for i in range(5):
            self.audit_db.log_interaction(
                user=f"user_{i}",
                question=f"Question {i}",
                intent="ask_ifrs",
                response=f"Response {i}",
                status="OK",
                confidence=0.8
            )
        
        # Retrieve interactions
        interactions = self.audit_db.get_interactions(limit=3)
        
        assert len(interactions) == 3
        assert interactions[0].question == "Question 4"  # Most recent first
        assert interactions[1].question == "Question 3"
        assert interactions[2].question == "Question 2"
    
    def test_get_interaction_stats(self):
        """Test interaction statistics."""
        # Log various interactions
        self.audit_db.log_interaction(
            user="user1", question="Q1", intent="ask_ifrs", 
            response="R1", status="OK", confidence=0.9
        )
        self.audit_db.log_interaction(
            user="user2", question="Q2", intent="ask_ifrs", 
            response="R2", status="ABSTAIN", confidence=0.3
        )
        self.audit_db.log_interaction(
            user="user3", question="Q3", intent="analyze_doc", 
            response="R3", status="OK", confidence=0.8
        )
        
        stats = self.audit_db.get_interaction_stats()
        
        assert stats["total_interactions"] == 3
        assert stats["ok_responses"] == 2
        assert stats["abstain_responses"] == 1
        assert stats["success_rate"] == (2/3) * 100


class TestLogInteraction:
    """Test log_interaction function."""
    
    def setup_method(self):
        """Set up test database."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_url = f"sqlite:///{self.temp_db.name}"
        
        # Mock the global audit_db
        import app.audit.models
        app.audit.models.audit_db = AuditDatabase(self.db_url)
        app.audit.models.audit_db.create_tables()
    
    def teardown_method(self):
        """Clean up test database."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_log_interaction_function(self):
        """Test log_interaction function."""
        interaction_id = log_interaction(
            user="test_user",
            question="What is fair value?",
            intent="ask_ifrs",
            response="Fair value is...",
            status="OK",
            confidence=0.85,
            citations=[{"standard": "IFRS 13", "paragraph": "4.1.1", "section": "Fair Value"}]
        )
        
        assert interaction_id is not None
        assert interaction_id > 0


class TestAuditIntegration:
    """Test audit system integration."""
    
    def setup_method(self):
        """Set up test database."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_url = f"sqlite:///{self.temp_db.name}"
        
        # Mock the global audit_db
        import app.audit.models
        app.audit.models.audit_db = AuditDatabase(self.db_url)
        app.audit.models.audit_db.create_tables()
    
    def teardown_method(self):
        """Clean up test database."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_ifrs_interaction_logging(self):
        """Test IFRS interaction logging."""
        # Simulate IFRS request/response
        request_data = {
            "question": "What is fair value measurement?",
            "standard_filter": "IFRS 13"
        }
        
        response_data = {
            "status": "OK",
            "answer": "Fair value measurement is the price that would be received...",
            "citations": [
                {"standard": "IFRS 13", "paragraph": "4.1.1", "section": "Fair Value"}
            ],
            "confidence": 0.85
        }
        
        interaction_id = log_interaction(
            user="test_user",
            question=request_data["question"],
            intent="ask_ifrs",
            response=response_data["answer"],
            status=response_data["status"],
            confidence=response_data["confidence"],
            tool_used="ifrs_ask",
            citations=response_data["citations"]
        )
        
        assert interaction_id is not None
        
        # Verify interaction was stored correctly
        with get_audit_db().get_session() as session:
            interaction = session.query(Interaction).filter(
                Interaction.id == interaction_id
            ).first()
            
            assert interaction is not None
            assert interaction.question == "What is fair value measurement?"
            assert interaction.intent == "ask_ifrs"
            assert interaction.status == "OK"
            assert interaction.confidence == 0.85
            assert interaction.tool_used == "ifrs_ask"
    
    def test_chat_interaction_logging(self):
        """Test chat interaction logging."""
        # Simulate chat request/response
        request_data = {
            "message": "Analyze document valuation-memo-2023",
            "doc_id": "valuation-memo-2023",
            "standard": "IFRS 13"
        }
        
        response_data = {
            "message": "Document analysis complete. 15 items met, 6 items failed.",
            "status": "NEEDS_REVIEW",
            "confidence": 0.75,
            "tool_used": "analyze_document",
            "citations": [
                {"standard": "IFRS 13", "paragraph": "4.1.1", "section": "Fair Value"}
            ]
        }
        
        interaction_id = log_interaction(
            user="test_user",
            question=request_data["message"],
            intent="chat",
            response=response_data["message"],
            status=response_data["status"],
            confidence=response_data["confidence"],
            tool_used=response_data["tool_used"],
            doc_id=request_data["doc_id"],
            citations=response_data["citations"]
        )
        
        assert interaction_id is not None
        
        # Verify interaction was stored correctly
        with get_audit_db().get_session() as session:
            interaction = session.query(Interaction).filter(
                Interaction.id == interaction_id
            ).first()
            
            assert interaction is not None
            assert interaction.question == "Analyze document valuation-memo-2023"
            assert interaction.intent == "chat"
            assert interaction.status == "NEEDS_REVIEW"
            assert interaction.confidence == 0.75
            assert interaction.tool_used == "analyze_document"
            assert interaction.doc_id == "valuation-memo-2023"
    
    def test_feedback_interaction_logging(self):
        """Test feedback interaction logging."""
        # Simulate feedback request/response
        request_data = {
            "doc_id": "valuation-memo-2023",
            "standard": "IFRS 13"
        }
        
        response_data = {
            "status": "NEEDS_REVIEW",
            "summary": "Document analysis complete. 15 items met, 6 items failed.",
            "confidence": 0.75,
            "items": [
                {
                    "id": "hierarchy_defined",
                    "description": "Fair value hierarchy level is clearly defined",
                    "met": True,
                    "citations": [{"standard": "IFRS 13", "paragraph": "4.1.1", "section": "Fair Value"}]
                },
                {
                    "id": "principal_market_identified",
                    "description": "Principal market for the asset is identified",
                    "met": False,
                    "citations": []
                }
            ]
        }
        
        # Extract citations from feedback items
        citations = []
        for item in response_data["items"]:
            citations.extend(item.get("citations", []))
        
        interaction_id = log_interaction(
            user="test_user",
            question=f"Analyze document {request_data['doc_id']} for {request_data['standard']} compliance",
            intent="analyze_doc",
            response=response_data["summary"],
            status=response_data["status"],
            confidence=response_data["confidence"],
            tool_used="analyze_document",
            doc_id=request_data["doc_id"],
            citations=citations,
            documents=[request_data["doc_id"]]
        )
        
        assert interaction_id is not None
        
        # Verify interaction was stored correctly
        with get_audit_db().get_session() as session:
            interaction = session.query(Interaction).filter(
                Interaction.id == interaction_id
            ).first()
            
            assert interaction is not None
            assert interaction.intent == "analyze_doc"
            assert interaction.status == "NEEDS_REVIEW"
            assert interaction.confidence == 0.75
            assert interaction.tool_used == "analyze_document"
            assert interaction.doc_id == "valuation-memo-2023"
            
            # Verify citations were stored
            stored_citations = session.query(InteractionCitation).filter(
                InteractionCitation.interaction_id == interaction_id
            ).all()
            
            assert len(stored_citations) == 1
            assert stored_citations[0].standard == "IFRS 13"
            assert stored_citations[0].paragraph == "4.1.1"
            
            # Verify documents were stored
            stored_docs = session.query(InteractionDocument).filter(
                InteractionDocument.interaction_id == interaction_id
            ).all()
            
            assert len(stored_docs) == 1
            assert stored_docs[0].doc_id == "valuation-memo-2023"


if __name__ == "__main__":
    pytest.main([__file__])
