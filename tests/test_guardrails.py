#!/usr/bin/env python3
"""Unit tests for IFRS policy guardrails."""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.guards import PolicyGuard, PolicyError, validate_language, apply_policy
from app.agents.schemas import IFRSAnswer, Citation


class TestPolicyGuard:
    """Test cases for policy guardrails."""
    
    def test_disallowed_language_detection(self):
        """Test detection of disallowed overconfident language."""
        guard = PolicyGuard()
        
        # Test cases with disallowed language
        test_cases = [
            ("This is guaranteed to work", ["guarantee"]),
            ("I certainly know this", ["certainly"]),
            ("This will always be true", ["always"]),
            ("This is definitely correct", ["definitely"]),
            ("I am 100% certain", ["100% certain"]),
            ("This is absolutely true", ["absolutely"]),
            ("This will never fail", ["never"]),
            ("It's impossible to be wrong", ["impossible"]),
            ("This must be correct", ["must be"]),
            ("It will always work", ["will always"]),
            ("This is guaranteed success", ["guaranteed"]),
            ("I am certain about this", ["certain"]),
            ("This is definitive proof", ["definitive"]),
            ("This is conclusive evidence", ["conclusive"])
        ]
        
        for text, expected_terms in test_cases:
            violations = guard.validate_language(text)
            assert len(violations) > 0, f"Should detect violations in: {text}"
            # Check that at least one of the expected terms is detected
            violation_text = " ".join(violations).lower()
            # Remove regex markers and check for plain text
            clean_violation_text = violation_text.replace("\\b", "").replace("\\", "")
            found_any = any(term.lower() in clean_violation_text for term in expected_terms)
            assert found_any, f"Should detect one of {expected_terms} in violations for: {text}. Violations: {violations}"
    
    def test_restricted_advice_detection(self):
        """Test detection of restricted advice language."""
        guard = PolicyGuard()
        
        # Test cases with restricted advice language
        test_cases = [
            ("I recommend tax structuring", ["tax structuring"]),
            ("You need legal representation", ["legal representation"]),
            ("This is legal advice", ["legal advice"]),
            ("Here's some tax advice", ["tax advice"]),
            ("This is investment advice", ["investment advice"]),
            ("I recommend financial planning", ["financial planning"]),
            ("You should invest in this", ["should invest"]),
            ("You should buy this stock", ["should buy"]),
            ("You should sell now", ["should sell"]),
            ("Consider tax optimization", ["tax optimization"]),
            ("This is tax avoidance", ["tax avoidance"]),
            ("Here's a legal strategy", ["legal strategy"])
        ]
        
        for text, expected_terms in test_cases:
            violations = guard.validate_language(text)
            assert len(violations) > 0, f"Should detect violations in: {text}"
            # Check that at least one of the expected terms is detected
            violation_text = " ".join(violations).lower()
            # Remove regex markers and check for plain text
            clean_violation_text = violation_text.replace("\\b", "").replace("\\", "")
            found_any = any(term.lower() in clean_violation_text for term in expected_terms)
            assert found_any, f"Should detect one of {expected_terms} in violations for: {text}. Violations: {violations}"
    
    def test_clean_language_passes(self):
        """Test that clean language passes validation."""
        guard = PolicyGuard()
        
        # Test cases with clean language
        clean_texts = [
            "Based on IFRS 13, fair value is measured at market price.",
            "According to paragraph 4.1.1, the measurement should consider market participants.",
            "The standard provides guidance on fair value measurement.",
            "This information is based on the available documentation.",
            "The requirements are outlined in the relevant sections.",
            "Market conditions may affect the measurement approach.",
            "The standard requires consideration of various factors."
        ]
        
        for text in clean_texts:
            violations = guard.validate_language(text)
            assert len(violations) == 0, f"Clean text should pass: {text}"
    
    def test_citation_validation(self):
        """Test citation validation."""
        guard = PolicyGuard()
        
        # Test with proper citations
        good_answer = IFRSAnswer(
            status="OK",
            answer="Based on IFRS 13, fair value is...",
            citations=[
                Citation(standard="IFRS 13", paragraph="4.1.1", section="Fair Value"),
                Citation(standard="IFRS 13", paragraph="4.1.2", section="Measurement")
            ],
            confidence=0.8
        )
        
        violations = guard.validate_citations(good_answer)
        assert len(violations) == 0, "Good citations should pass validation"
        
        # Test with missing citations
        bad_answer = IFRSAnswer(
            status="OK",
            answer="Based on IFRS 13, fair value is...",
            citations=[],
            confidence=0.8
        )
        
        violations = guard.validate_citations(bad_answer)
        assert len(violations) > 0, "Missing citations should fail validation"
        assert "Citations are required" in violations[0]
        
        # Test with incomplete citations
        incomplete_answer = IFRSAnswer(
            status="OK",
            answer="Based on IFRS 13, fair value is...",
            citations=[
                Citation(standard="", paragraph="4.1.1", section="Fair Value"),
                Citation(standard="IFRS 13", paragraph="", section="Measurement")
            ],
            confidence=0.8
        )
        
        violations = guard.validate_citations(incomplete_answer)
        assert len(violations) > 0, "Incomplete citations should fail validation"
    
    def test_confidence_validation(self):
        """Test confidence validation."""
        guard = PolicyGuard()
        
        # Test with high confidence
        high_conf_answer = IFRSAnswer(
            status="OK",
            answer="Based on IFRS 13...",
            citations=[Citation(standard="IFRS 13", paragraph="4.1.1")],
            confidence=0.8
        )
        
        violations = guard.validate_confidence(high_conf_answer)
        assert len(violations) == 0, "High confidence should pass"
        
        # Test with low confidence
        low_conf_answer = IFRSAnswer(
            status="OK",
            answer="Based on IFRS 13...",
            citations=[Citation(standard="IFRS 13", paragraph="4.1.1")],
            confidence=0.5
        )
        
        violations = guard.validate_confidence(low_conf_answer)
        assert len(violations) > 0, "Low confidence should fail validation"
        assert "below minimum threshold" in violations[0]
    
    def test_content_validation(self):
        """Test content validation."""
        guard = PolicyGuard()
        
        # Test with appropriate content
        good_answer = IFRSAnswer(
            status="OK",
            answer="Based on IFRS 13, fair value measurement requires consideration of market participants and orderly transactions.",
            citations=[Citation(standard="IFRS 13", paragraph="4.1.1")],
            confidence=0.8
        )
        
        violations = guard.validate_content(good_answer)
        assert len(violations) == 0, "Good content should pass validation"
        
        # Test with too short answer
        short_answer = IFRSAnswer(
            status="OK",
            answer="Yes.",
            citations=[Citation(standard="IFRS 13", paragraph="4.1.1")],
            confidence=0.8
        )
        
        violations = guard.validate_content(short_answer)
        assert len(violations) > 0, "Too short answer should fail validation"
        assert "too short" in violations[0]
    
    def test_apply_policy_with_violations(self):
        """Test that policy violations result in ABSTAIN."""
        guard = PolicyGuard()
        
        # Create answer with policy violations
        violating_answer = IFRSAnswer(
            status="OK",
            answer="This is guaranteed to be correct and I certainly recommend this approach for tax structuring.",
            citations=[],  # Missing citations
            confidence=0.3  # Low confidence
        )
        
        # Apply policy - should result in ABSTAIN
        result = guard.apply_policy(violating_answer)
        
        assert result.status == "ABSTAIN", "Policy violations should result in ABSTAIN"
        assert "Policy violations detected" in result.answer
        assert result.confidence == 0.0
        assert len(result.citations) == 0
    
    def test_apply_policy_clean_answer(self):
        """Test that clean answers pass policy validation."""
        guard = PolicyGuard()
        
        # Create clean answer
        clean_answer = IFRSAnswer(
            status="OK",
            answer="Based on IFRS 13, fair value measurement requires consideration of market participants and orderly transactions.",
            citations=[
                Citation(standard="IFRS 13", paragraph="4.1.1", section="Fair Value"),
                Citation(standard="IFRS 13", paragraph="4.1.2", section="Measurement")
            ],
            confidence=0.8
        )
        
        # Apply policy - should pass
        result = guard.apply_policy(clean_answer)
        
        assert result.status == "OK", "Clean answer should pass policy validation"
        assert result.confidence == 0.8
        assert len(result.citations) == 2
    
    def test_mock_overconfident_response(self):
        """Test simulation of overconfident model response."""
        # Simulate a model that responds overconfidently
        overconfident_answer = IFRSAnswer(
            status="OK",
            answer="I guarantee this is definitely the correct approach. This will always work and I am 100% certain about this recommendation for tax structuring.",
            citations=[Citation(standard="IFRS 13", paragraph="4.1.1")],
            confidence=0.9  # High confidence but with violations
        )
        
        # Apply policy - should flip to ABSTAIN
        result = apply_policy(overconfident_answer)
        
        assert result.status == "ABSTAIN", "Overconfident response should be flipped to ABSTAIN"
        assert "Policy violations detected" in result.answer
        assert result.confidence == 0.0
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        guard = PolicyGuard()
        
        # Test empty answer
        empty_answer = IFRSAnswer(
            status="OK",
            answer="",
            citations=[],
            confidence=0.0
        )
        
        violations = guard.validate_content(empty_answer)
        assert len(violations) > 0, "Empty answer should fail validation"
        
        # Test very long answer
        long_answer = IFRSAnswer(
            status="OK",
            answer="A" * 3000,  # Very long answer
            citations=[Citation(standard="IFRS 13", paragraph="4.1.1")],
            confidence=0.8
        )
        
        violations = guard.validate_content(long_answer)
        assert len(violations) > 0, "Very long answer should fail validation"
        assert "too long" in violations[0]
    
    def test_case_insensitive_detection(self):
        """Test that language detection is case-insensitive."""
        guard = PolicyGuard()
        
        # Test various cases
        test_cases = [
            "This is GUARANTEED to work",
            "I am CERTAINLY right",
            "This will ALWAYS be true",
            "I am 100% CERTAIN",
            "This is ABSOLUTELY correct"
        ]
        
        for text in test_cases:
            violations = guard.validate_language(text)
            assert len(violations) > 0, f"Should detect violations regardless of case: {text}"


def test_validate_language_function():
    """Test the standalone validate_language function."""
    # Test with violations
    violations = validate_language("This is guaranteed to work and I certainly recommend it.")
    assert len(violations) > 0
    
    # Test with clean text
    violations = validate_language("Based on IFRS 13, fair value measurement is defined as...")
    assert len(violations) == 0


def test_apply_policy_function():
    """Test the standalone apply_policy function."""
    # Test with violating answer
    violating_answer = IFRSAnswer(
        status="OK",
        answer="This is guaranteed to work and I certainly recommend tax structuring.",
        citations=[],
        confidence=0.3
    )
    
    result = apply_policy(violating_answer)
    assert result.status == "ABSTAIN"
    assert "Policy violations detected" in result.answer


if __name__ == "__main__":
    # Run tests
    import subprocess
    result = subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"], 
                          capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    sys.exit(result.returncode)
