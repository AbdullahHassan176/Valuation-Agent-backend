"""PII sanitization utilities for prompts and logs."""

import re
from typing import Dict, List, Tuple


class PIISanitizer:
    """PII sanitization utility."""
    
    def __init__(self):
        """Initialize PII sanitizer with regex patterns."""
        self.patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'),
            'iban': re.compile(r'\b[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{7}([A-Z0-9]?){0,16}\b'),
            'ssn': re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
            'credit_card': re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
            'ip_address': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            'url': re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+'),
            'mac_address': re.compile(r'\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b'),
        }
        
        self.replacements = {
            'email': '[EMAIL_REDACTED]',
            'phone': '[PHONE_REDACTED]',
            'iban': '[IBAN_REDACTED]',
            'ssn': '[SSN_REDACTED]',
            'credit_card': '[CARD_REDACTED]',
            'ip_address': '[IP_REDACTED]',
            'url': '[URL_REDACTED]',
            'mac_address': '[MAC_REDACTED]',
        }
    
    def sanitize_text(self, text: str) -> Tuple[str, List[Dict[str, str]]]:
        """Sanitize text by redacting PII.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Tuple of (sanitized_text, redaction_log)
        """
        if not text:
            return text, []
        
        sanitized_text = text
        redaction_log = []
        
        for pii_type, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                # Replace with redaction placeholder
                sanitized_text = pattern.sub(
                    self.replacements[pii_type],
                    sanitized_text
                )
                
                # Log redactions (without exposing actual values)
                redaction_log.append({
                    'type': pii_type,
                    'count': len(matches),
                    'replacement': self.replacements[pii_type]
                })
        
        return sanitized_text, redaction_log
    
    def sanitize_prompt(self, prompt: str) -> str:
        """Sanitize a prompt for LLM calls.
        
        Args:
            prompt: Prompt text to sanitize
            
        Returns:
            Sanitized prompt text
        """
        sanitized, _ = self.sanitize_text(prompt)
        return sanitized
    
    def sanitize_log_entry(self, log_entry: str) -> Tuple[str, List[Dict[str, str]]]:
        """Sanitize a log entry.
        
        Args:
            log_entry: Log entry to sanitize
            
        Returns:
            Tuple of (sanitized_log, redaction_log)
        """
        return self.sanitize_text(log_entry)
    
    def get_redaction_summary(self, redaction_log: List[Dict[str, str]]) -> str:
        """Get a summary of redactions made.
        
        Args:
            redaction_log: List of redaction records
            
        Returns:
            Summary string of redactions
        """
        if not redaction_log:
            return "No PII detected"
        
        summary_parts = []
        for redaction in redaction_log:
            summary_parts.append(
                f"{redaction['count']} {redaction['type']} redacted"
            )
        
        return ", ".join(summary_parts)


# Global sanitizer instance
pii_sanitizer = PIISanitizer()


def sanitize_prompt(prompt: str) -> str:
    """Sanitize a prompt for LLM calls.
    
    Args:
        prompt: Prompt text to sanitize
        
    Returns:
        Sanitized prompt text
    """
    return pii_sanitizer.sanitize_prompt(prompt)


def sanitize_log_entry(log_entry: str) -> Tuple[str, List[Dict[str, str]]]:
    """Sanitize a log entry.
    
    Args:
        log_entry: Log entry to sanitize
        
    Returns:
        Tuple of (sanitized_log, redaction_log)
    """
    return pii_sanitizer.sanitize_log_entry(log_entry)


def get_redaction_summary(redaction_log: List[Dict[str, str]]) -> str:
    """Get a summary of redactions made.
    
    Args:
        redaction_log: List of redaction records
        
    Returns:
        Summary string of redactions
    """
    return pii_sanitizer.get_redaction_summary(redaction_log)
