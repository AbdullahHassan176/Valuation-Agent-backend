"""Simple tests for core functionality."""

import pytest
from app.agents.schemas import IFRSAnswer, Citation
from app.agents.feedback import Feedback, ChecklistItem


class TestBasicFunctionality:
    """Test basic functionality without complex mocking."""
    
    def test_ifrs_answer_creation(self):
        """Test IFRSAnswer model creation."""
        citation = Citation(
            standard="IFRS 13",
            paragraph="4.1.1",
            section="Fair Value"
        )
        
        answer = IFRSAnswer(
            status="OK",
            answer="Fair value is the price that would be received to sell an asset.",
            citations=[citation],
            confidence=0.8
        )
        
        assert answer.status == "OK"
        assert len(answer.citations) == 1
        assert answer.citations[0].standard == "IFRS 13"
        assert answer.confidence == 0.8
    
    def test_feedback_creation(self):
        """Test Feedback model creation."""
        citation = Citation(
            standard="IFRS 13",
            paragraph="4.1.1",
            section="Fair Value"
        )
        
        item = ChecklistItem(
            id="hierarchy_defined",
            key="hierarchy_defined",
            description="Fair value hierarchy is clearly defined",
            met=True,
            notes="Level 2 inputs used",
            citations=[citation]
        )
        
        feedback = Feedback(
            status="OK",
            summary="Document meets IFRS 13 requirements",
            items=[item],
            confidence=0.9
        )
        
        assert feedback.status == "OK"
        assert len(feedback.items) == 1
        assert feedback.items[0].met is True
        assert feedback.confidence == 0.9
    
    def test_citation_creation(self):
        """Test Citation model creation."""
        citation = Citation(
            standard="IFRS 13",
            paragraph="4.1.1",
            section="Fair Value"
        )
        
        assert citation.standard == "IFRS 13"
        assert citation.paragraph == "4.1.1"
        assert citation.section == "Fair Value"
    
    def test_checklist_item_creation(self):
        """Test ChecklistItem model creation."""
        item = ChecklistItem(
            id="test_item",
            key="test_item",
            description="Test description",
            met=False,
            notes="Test notes",
            citations=[]
        )
        
        assert item.id == "test_item"
        assert item.met is False
        assert len(item.citations) == 0
    
    def test_abstain_status(self):
        """Test ABSTAIN status handling."""
        answer = IFRSAnswer(
            status="ABSTAIN",
            answer="No relevant documents found",
            citations=[],
            confidence=0.0
        )
        
        assert answer.status == "ABSTAIN"
        assert answer.confidence == 0.0
        assert len(answer.citations) == 0
    
    def test_needs_review_status(self):
        """Test NEEDS_REVIEW status handling."""
        item = ChecklistItem(
            id="critical_item",
            key="critical_item",
            description="Critical requirement",
            met=False,
            notes="Not met",
            citations=[]
        )
        
        feedback = Feedback(
            status="NEEDS_REVIEW",
            summary="Critical items not met",
            items=[item],
            confidence=0.5
        )
        
        assert feedback.status == "NEEDS_REVIEW"
        assert len(feedback.items) == 1
        assert feedback.items[0].met is False
    
    def test_confidence_ranges(self):
        """Test confidence value validation."""
        # High confidence
        answer_high = IFRSAnswer(
            status="OK",
            answer="High confidence answer",
            citations=[],
            confidence=0.9
        )
        assert answer_high.confidence == 0.9
        
        # Low confidence
        answer_low = IFRSAnswer(
            status="ABSTAIN",
            answer="Low confidence answer",
            citations=[],
            confidence=0.2
        )
        assert answer_low.confidence == 0.2
        
        # Zero confidence
        answer_zero = IFRSAnswer(
            status="ABSTAIN",
            answer="No confidence answer",
            citations=[],
            confidence=0.0
        )
        assert answer_zero.confidence == 0.0
    
    def test_multiple_citations(self):
        """Test multiple citations in response."""
        citation1 = Citation(
            standard="IFRS 13",
            paragraph="4.1.1",
            section="Fair Value"
        )
        
        citation2 = Citation(
            standard="IFRS 13",
            paragraph="4.1.2",
            section="Principal Market"
        )
        
        answer = IFRSAnswer(
            status="OK",
            answer="Answer with multiple citations",
            citations=[citation1, citation2],
            confidence=0.8
        )
        
        assert len(answer.citations) == 2
        assert answer.citations[0].standard == "IFRS 13"
        assert answer.citations[1].standard == "IFRS 13"
        assert answer.citations[0].paragraph == "4.1.1"
        assert answer.citations[1].paragraph == "4.1.2"
    
    def test_empty_citations(self):
        """Test empty citations list."""
        answer = IFRSAnswer(
            status="ABSTAIN",
            answer="No citations available",
            citations=[],
            confidence=0.0
        )
        
        assert len(answer.citations) == 0
        assert answer.status == "ABSTAIN"
    
    def test_string_paragraph(self):
        """Test Citation with string paragraph."""
        citation = Citation(
            standard="IFRS 13",
            paragraph="B2",
            section="Application Guidance"
        )
        
        assert citation.paragraph == "B2"
        assert citation.section == "Application Guidance"
    
    def test_integer_paragraph(self):
        """Test Citation with integer paragraph."""
        citation = Citation(
            standard="IFRS 13",
            paragraph=4,
            section="Fair Value"
        )
        
        assert citation.paragraph == 4
        assert citation.section == "Fair Value"
