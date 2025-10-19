"""Tests for feedback checklist functionality."""

import pytest
from unittest.mock import patch, MagicMock
from app.agents.feedback import analyze_document
from app.agents.schemas import Citation
from app.agents.feedback import Feedback, ChecklistItem


class TestFeedbackChecklist:
    """Test feedback checklist functionality."""
    
    def test_needs_review_when_critical_items_missing(self):
        """Test NEEDS_REVIEW status when critical items are missing."""
        # Mock document content with missing critical items
        mock_document_content = """
        This valuation memo discusses fair value measurement.
        The document mentions hierarchy levels but does not clearly define them.
        Principal market is not identified in this document.
        """
        
        # Mock IFRS agent to return low confidence for critical items
        mock_ifrs_responses = [
            # hierarchy_defined - critical, should fail
            {
                "status": "ABSTAIN",
                "answer": "Hierarchy level is not clearly defined in the document.",
                "citations": [],
                "confidence": 0.3
            },
            # principal_market_identified - critical, should fail  
            {
                "status": "ABSTAIN",
                "answer": "Principal market is not identified in the document.",
                "citations": [],
                "confidence": 0.2
            },
            # Other items - should pass
            {
                "status": "OK",
                "answer": "Day-1 P&L is calculated and disclosed.",
                "citations": [{"standard": "IFRS 13", "paragraph": "4.1.1", "section": "Fair Value"}],
                "confidence": 0.8
            }
        ]
        
        with patch('app.agents.feedback.feedback_agent._load_document_content') as mock_load_doc, \
             patch('app.agents.feedback.feedback_agent.ifrs_agent.answer_ifrs') as mock_answer_ifrs:
            
            mock_load_doc.return_value = mock_document_content
            mock_answer_ifrs.side_effect = mock_ifrs_responses
            
            # Test the function
            result = analyze_document("test-doc-123", "IFRS 13")
            
            # Assertions
            assert isinstance(result, Feedback)
            assert result.status == "NEEDS_REVIEW"
            assert result.confidence < 0.7  # Low confidence due to critical failures
            
            # Check that critical items are marked as not met
            critical_items = [item for item in result.items if item.is_critical]
            failed_critical = [item for item in critical_items if not item.met]
            assert len(failed_critical) > 0
            
            # Check summary mentions critical failures
            assert "critical" in result.summary.lower() or "not met" in result.summary.lower()
    
    def test_ok_status_when_all_critical_items_met(self):
        """Test OK status when all critical items are met."""
        mock_document_content = """
        This comprehensive valuation memo clearly defines fair value hierarchy levels.
        The principal market is identified as the London Stock Exchange.
        Day-1 P&L is calculated and disclosed with proper justification.
        Observable inputs are used to maximum extent possible.
        """
        
        # Mock IFRS agent to return high confidence for all items
        mock_ifrs_responses = [
            {
                "status": "OK",
                "answer": "Hierarchy level is clearly defined as Level 2.",
                "citations": [{"standard": "IFRS 13", "paragraph": "4.1.1", "section": "Fair Value"}],
                "confidence": 0.9
            },
            {
                "status": "OK", 
                "answer": "Principal market is identified as London Stock Exchange.",
                "citations": [{"standard": "IFRS 13", "paragraph": "4.1.2", "section": "Principal Market"}],
                "confidence": 0.9
            },
            {
                "status": "OK",
                "answer": "Day-1 P&L is calculated and disclosed.",
                "citations": [{"standard": "IFRS 13", "paragraph": "4.1.3", "section": "Day-1 P&L"}],
                "confidence": 0.9
            }
        ]
        
        with patch('app.agents.feedback.feedback_agent._load_document_content') as mock_load_doc, \
             patch('app.agents.feedback.feedback_agent.ifrs_agent.answer_ifrs') as mock_answer_ifrs:
            
            mock_load_doc.return_value = mock_document_content
            mock_answer_ifrs.side_effect = mock_ifrs_responses
            
            result = analyze_document("test-doc-123", "IFRS 13")
            
            # Assertions
            assert isinstance(result, Feedback)
            assert result.status == "OK"
            assert result.confidence > 0.7
            
            # Check that critical items are met
            critical_items = [item for item in result.items if item.is_critical]
            met_critical = [item for item in critical_items if item.met]
            assert len(met_critical) == len(critical_items)  # All critical items met
    
    def test_abstain_status_low_confidence(self):
        """Test ABSTAIN status when overall confidence is too low."""
        mock_document_content = "Unclear document with insufficient information."
        
        # Mock IFRS agent to return low confidence for all items
        mock_ifrs_responses = [
            {
                "status": "ABSTAIN",
                "answer": "Insufficient information to assess this requirement.",
                "citations": [],
                "confidence": 0.2
            }
        ] * 5  # Repeat for multiple items
        
        with patch('app.agents.feedback.feedback_agent._load_document_content') as mock_load_doc, \
             patch('app.agents.feedback.feedback_agent.ifrs_agent.answer_ifrs') as mock_answer_ifrs:
            
            mock_load_doc.return_value = mock_document_content
            mock_answer_ifrs.side_effect = mock_ifrs_responses
            
            result = analyze_document("test-doc-123", "IFRS 13")
            
            # Assertions
            assert isinstance(result, Feedback)
            assert result.status == "ABSTAIN"
            assert result.confidence < 0.65
            assert "Low confidence" in result.summary or "insufficient" in result.summary.lower()
    
    def test_checklist_items_generation(self):
        """Test that checklist items are properly generated."""
        mock_document_content = "Test document content."
        
        mock_ifrs_responses = [
            {
                "status": "OK",
                "answer": "Requirement is met.",
                "citations": [{"standard": "IFRS 13", "paragraph": "4.1.1", "section": "Fair Value"}],
                "confidence": 0.8
            }
        ] * 3
        
        with patch('app.agents.feedback.feedback_agent._load_document_content') as mock_load_doc, \
             patch('app.agents.feedback.feedback_agent.ifrs_agent.answer_ifrs') as mock_answer_ifrs:
            
            mock_load_doc.return_value = mock_document_content
            mock_answer_ifrs.side_effect = mock_ifrs_responses
            
            result = analyze_document("test-doc-123", "IFRS 13")
            
            # Check checklist items
            assert len(result.items) > 0
            assert all(isinstance(item, ChecklistItem) for item in result.items)
            
            # Check item properties
            for item in result.items:
                assert hasattr(item, 'id')
                assert hasattr(item, 'key')
                assert hasattr(item, 'description')
                assert hasattr(item, 'met')
                assert hasattr(item, 'is_critical')
                assert isinstance(item.met, bool)
                assert isinstance(item.is_critical, bool)
    
    def test_citations_in_checklist_items(self):
        """Test that citations are properly included in checklist items."""
        mock_document_content = "Test document content."
        
        mock_ifrs_responses = [
            {
                "status": "OK",
                "answer": "Requirement is met with proper justification.",
                "citations": [
                    {"standard": "IFRS 13", "paragraph": "4.1.1", "section": "Fair Value"},
                    {"standard": "IFRS 13", "paragraph": "4.1.2", "section": "Measurement"}
                ],
                "confidence": 0.9
            }
        ]
        
        with patch('app.agents.feedback.feedback_agent._load_document_content') as mock_load_doc, \
             patch('app.agents.feedback.feedback_agent.ifrs_agent.answer_ifrs') as mock_answer_ifrs:
            
            mock_load_doc.return_value = mock_document_content
            mock_answer_ifrs.side_effect = mock_ifrs_responses
            
            result = analyze_document("test-doc-123", "IFRS 13")
            
            # Check that citations are included
            items_with_citations = [item for item in result.items if item.citations]
            assert len(items_with_citations) > 0
            
            # Check citation format
            for item in items_with_citations:
                assert all(isinstance(c, Citation) for c in item.citations)
                assert all(c.standard == "IFRS 13" for c in item.citations)
    
    def test_document_not_found(self):
        """Test handling when document is not found."""
        with patch('app.agents.feedback.feedback_agent._load_document_content') as mock_load_doc:
            mock_load_doc.return_value = None  # Document not found
            
            result = analyze_document("nonexistent-doc", "IFRS 13")
            
            # Should return ABSTAIN
            assert isinstance(result, Feedback)
            assert result.status == "ABSTAIN"
            assert result.confidence == 0.0
            assert "Document not found" in result.summary
    
    def test_error_handling(self):
        """Test error handling in feedback analysis."""
        with patch('app.agents.feedback.feedback_agent._load_document_content') as mock_load_doc:
            mock_load_doc.side_effect = Exception("Database connection failed")
            
            result = analyze_document("test-doc-123", "IFRS 13")
            
            # Should return ABSTAIN on error
            assert isinstance(result, Feedback)
            assert result.status == "ABSTAIN"
            assert result.confidence == 0.0
            assert "Error analyzing document" in result.summary
    
    def test_different_standards(self):
        """Test feedback analysis with different IFRS standards."""
        mock_document_content = "Test document content."
        
        mock_ifrs_responses = [
            {
                "status": "OK",
                "answer": "Requirement is met.",
                "citations": [{"standard": "IFRS 9", "paragraph": "4.1.1", "section": "Classification"}],
                "confidence": 0.8
            }
        ]
        
        with patch('app.agents.feedback.feedback_agent._load_document_content') as mock_load_doc, \
             patch('app.agents.feedback.feedback_agent.ifrs_agent.answer_ifrs') as mock_answer_ifrs:
            
            mock_load_doc.return_value = mock_document_content
            mock_answer_ifrs.side_effect = mock_ifrs_responses
            
            # Test with IFRS 9
            result = analyze_document("test-doc-123", "IFRS 9")
            
            assert isinstance(result, Feedback)
            assert result.status == "OK"
            
            # Check that the correct standard is used
            assert any("IFRS 9" in str(c.standard) for item in result.items for c in item.citations)
    
    def test_compliance_percentage_calculation(self):
        """Test that compliance percentage is calculated correctly."""
        mock_document_content = "Test document content."
        
        # Mock responses: 2 met, 1 not met
        mock_ifrs_responses = [
            {"status": "OK", "answer": "Met", "citations": [], "confidence": 0.8},
            {"status": "OK", "answer": "Met", "citations": [], "confidence": 0.8},
            {"status": "ABSTAIN", "answer": "Not met", "citations": [], "confidence": 0.2}
        ]
        
        with patch('app.agents.feedback.feedback_agent._load_document_content') as mock_load_doc, \
             patch('app.agents.feedback.feedback_agent.ifrs_agent.answer_ifrs') as mock_answer_ifrs:
            
            mock_load_doc.return_value = mock_document_content
            mock_answer_ifrs.side_effect = mock_ifrs_responses
            
            result = analyze_document("test-doc-123", "IFRS 13")
            
            # Check compliance percentage in summary
            assert "66.7%" in result.summary or "67%" in result.summary  # 2/3 = 66.7%
