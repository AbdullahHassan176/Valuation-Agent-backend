"""IFRS policy validation for PoC."""

from typing import Dict, Any, Tuple
from app.poc.redaction import validate_confidence, validate_citations


# Policy constants
MIN_CONFIDENCE = 0.70
REQUIRE_CITATIONS = True


def validate(answer_dict: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate answer against IFRS policy requirements.
    
    Returns:
        Tuple of (is_valid, reason_if_invalid)
    """
    
    # Check if status is OK
    if answer_dict.get("status") != "OK":
        return True, None  # ABSTAIN is always valid
    
    # Check confidence threshold
    confidence = answer_dict.get("confidence", 0.0)
    if not validate_confidence(confidence, MIN_CONFIDENCE):
        return False, f"Confidence {confidence} below threshold {MIN_CONFIDENCE}"
    
    # Check citations requirement
    citations = answer_dict.get("citations", [])
    if not validate_citations(citations, REQUIRE_CITATIONS):
        return False, "Missing required citations"
    
    # Check for prohibited language
    answer_text = answer_dict.get("answer", "")
    if answer_text:
        from app.poc.redaction import guard_language
        violations = guard_language(answer_text)
        if violations:
            return False, f"Language violations: {'; '.join(violations)}"
    
    return True, None


def force_abstain(answer_dict: Dict[str, Any], reason: str) -> Dict[str, Any]:
    """Force an answer to ABSTAIN status."""
    
    return {
        "status": "ABSTAIN",
        "reason": reason,
        "answer": "",
        "citations": [],
        "confidence": 0.0,
        "warnings": [f"Forced ABSTAIN: {reason}"]
    }


def validate_extract_response(response_dict: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate contract extraction response."""
    
    if response_dict.get("status") != "OK":
        return True, None  # ABSTAIN is always valid
    
    # Check confidence
    confidence = response_dict.get("confidence", 0.0)
    if not validate_confidence(confidence, MIN_CONFIDENCE):
        return False, f"Extraction confidence {confidence} below threshold {MIN_CONFIDENCE}"
    
    # Check fields have reasonable confidence
    fields = response_dict.get("fields", [])
    for field in fields:
        if field.get("confidence", 0.0) < 0.5:  # Lower threshold for individual fields
            return False, f"Field '{field.get('key')}' has low confidence {field.get('confidence')}"
    
    return True, None


def validate_explain_response(response_dict: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate run explanation response."""
    
    if response_dict.get("status") != "OK":
        return True, None  # ABSTAIN is always valid
    
    # Check confidence
    confidence = response_dict.get("confidence", 0.0)
    if not validate_confidence(confidence, MIN_CONFIDENCE):
        return False, f"Explanation confidence {confidence} below threshold {MIN_CONFIDENCE}"
    
    # Check narrative is not empty
    narrative = response_dict.get("narrative", "")
    if not narrative or len(narrative.strip()) < 10:
        return False, "Explanation narrative too short or empty"
    
    return True, None



