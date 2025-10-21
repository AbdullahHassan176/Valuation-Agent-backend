"""PII redaction and language guardrails for PoC."""

import re
from typing import List


def redact(text: str) -> str:
    """Remove PII from text before sending to LLM."""
    if not text:
        return text
    
    # Email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]', text)
    
    # Phone numbers (various formats)
    text = re.sub(r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b', '[PHONE_REDACTED]', text)
    
    # IBAN (basic pattern)
    text = re.sub(r'\b[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{7}([A-Z0-9]?){0,16}\b', '[IBAN_REDACTED]', text)
    
    # Credit card numbers (basic pattern)
    text = re.sub(r'\b[0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{4}\b', '[CARD_REDACTED]', text)
    
    # SSN (US format)
    text = re.sub(r'\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b', '[SSN_REDACTED]', text)
    
    return text


def guard_language(text: str) -> List[str]:
    """Check for disallowed language patterns."""
    violations = []
    
    # Prohibited words
    prohibited_words = [
        "guaranteed", "always", "certainly", "definitely", "absolutely",
        "100%", "never fails", "risk-free", "sure thing"
    ]
    
    text_lower = text.lower()
    for word in prohibited_words:
        if word in text_lower:
            violations.append(f"Prohibited word detected: '{word}'")
    
    # Overly confident language patterns
    confidence_patterns = [
        r'\b(guarantee|guaranteed)\b',
        r'\b(always|never)\b',
        r'\b(certainly|definitely)\b',
        r'\b(100%|never fails)\b'
    ]
    
    for pattern in confidence_patterns:
        if re.search(pattern, text_lower):
            violations.append(f"Overly confident language detected: {pattern}")
    
    return violations


def validate_confidence(confidence: float, min_threshold: float = 0.7) -> bool:
    """Validate confidence meets minimum threshold."""
    return confidence >= min_threshold


def validate_citations(citations: List[dict], require_citations: bool = True) -> bool:
    """Validate citations are present when required."""
    if not require_citations:
        return True
    
    if not citations:
        return False
    
    # Check that citations have required fields
    for citation in citations:
        if not citation.get('source_id') or not citation.get('section'):
            return False
    
    return True




