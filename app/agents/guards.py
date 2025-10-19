"""Policy guardrails and validation for IFRS responses."""

import re
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path
from app.agents.schemas import IFRSAnswer, Citation
from app.agents.ifrs import _create_abstain_response


class PolicyError(Exception):
    """Exception raised when policy violations are detected."""
    pass


class PolicyGuard:
    """Policy guardrail system for IFRS responses."""
    
    def __init__(self, policy_file: Optional[str] = None):
        """Initialize policy guard with configuration.
        
        Args:
            policy_file: Path to policy YAML file
        """
        if policy_file is None:
            policy_file = Path(__file__).parent.parent / "policy" / "policies.yml"
        
        self.policies = self._load_policies(policy_file)
        self._compile_patterns()
    
    def _load_policies(self, policy_file: str) -> Dict[str, Any]:
        """Load policies from YAML file.
        
        Args:
            policy_file: Path to policy file
            
        Returns:
            Loaded policy configuration
        """
        try:
            with open(policy_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load policies from {policy_file}: {e}")
            return self._get_default_policies()
    
    def _get_default_policies(self) -> Dict[str, Any]:
        """Get default policy configuration.
        
        Returns:
            Default policy configuration
        """
        return {
            "citation_policy": {"require_citations": True, "min_citations": 1},
            "confidence_policy": {"min_confidence": 0.65},
            "language_policy": {
                "disallow_language": ["guarantee", "certainly", "always"],
                "restricted_advice": ["tax structuring", "legal representation"]
            }
        }
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching."""
        # Compile disallowed language patterns
        disallowed = self.policies.get("language_policy", {}).get("disallow_language", [])
        self.disallowed_patterns = [
            re.compile(rf'\b{re.escape(term)}\b', re.IGNORECASE) 
            for term in disallowed
        ]
        
        # Compile restricted advice patterns
        restricted = self.policies.get("language_policy", {}).get("restricted_advice", [])
        self.restricted_patterns = [
            re.compile(rf'\b{re.escape(term)}\b', re.IGNORECASE)
            for term in restricted
        ]
    
    def validate_language(self, text: str) -> List[str]:
        """Validate text against language policy.
        
        Args:
            text: Text to validate
            
        Returns:
            List of policy violations found
        """
        violations = []
        text_lower = text.lower()
        
        # Check for disallowed overconfident language
        for pattern in self.disallowed_patterns:
            if pattern.search(text):
                violations.append(f"Disallowed overconfident language detected: '{pattern.pattern}'")
        
        # Check for restricted advice language
        for pattern in self.restricted_patterns:
            if pattern.search(text):
                violations.append(f"Restricted advice language detected: '{pattern.pattern}'")
        
        return violations
    
    def validate_citations(self, answer: IFRSAnswer) -> List[str]:
        """Validate citations against policy.
        
        Args:
            answer: IFRS answer to validate
            
        Returns:
            List of citation violations
        """
        violations = []
        citation_policy = self.policies.get("citation_policy", {})
        
        # Check if citations are required
        if citation_policy.get("require_citations", True):
            if not answer.citations or len(answer.citations) == 0:
                violations.append("Citations are required but none provided")
            
            # Check minimum citations
            min_citations = citation_policy.get("min_citations", 1)
            if len(answer.citations) < min_citations:
                violations.append(f"Minimum {min_citations} citations required, got {len(answer.citations)}")
        
        # Validate citation format
        for i, citation in enumerate(answer.citations):
            if not citation.standard:
                violations.append(f"Citation {i+1}: Standard is required")
            if not citation.paragraph:
                violations.append(f"Citation {i+1}: Paragraph is required")
        
        return violations
    
    def validate_confidence(self, answer: IFRSAnswer) -> List[str]:
        """Validate confidence against policy.
        
        Args:
            answer: IFRS answer to validate
            
        Returns:
            List of confidence violations
        """
        violations = []
        confidence_policy = self.policies.get("confidence_policy", {})
        min_confidence = confidence_policy.get("min_confidence", 0.65)
        
        if answer.confidence < min_confidence:
            violations.append(f"Confidence {answer.confidence:.2f} below minimum threshold {min_confidence}")
        
        return violations
    
    def validate_content(self, answer: IFRSAnswer) -> List[str]:
        """Validate content against policy.
        
        Args:
            answer: IFRS answer to validate
            
        Returns:
            List of content violations
        """
        violations = []
        content_policy = self.policies.get("content_policy", {})
        
        # Check answer length
        min_length = content_policy.get("min_answer_length", 10)
        max_length = content_policy.get("max_answer_length", 2000)
        
        if len(answer.answer) < min_length:
            violations.append(f"Answer too short: {len(answer.answer)} < {min_length}")
        
        if len(answer.answer) > max_length:
            violations.append(f"Answer too long: {len(answer.answer)} > {max_length}")
        
        # Check for prohibited content
        prohibited = content_policy.get("prohibited_content", [])
        answer_lower = answer.answer.lower()
        for content_type in prohibited:
            if content_type.lower() in answer_lower:
                violations.append(f"Prohibited content detected: '{content_type}'")
        
        return violations
    
    def apply_policy(self, answer: IFRSAnswer) -> IFRSAnswer:
        """Apply all policy checks to an answer.
        
        Args:
            answer: IFRS answer to validate
            
        Returns:
            Validated answer or ABSTAIN response with violations
            
        Raises:
            PolicyError: If policy violations are detected
        """
        all_violations = []
        
        # Validate language
        language_violations = self.validate_language(answer.answer)
        all_violations.extend(language_violations)
        
        # Validate citations
        citation_violations = self.validate_citations(answer)
        all_violations.extend(citation_violations)
        
        # Validate confidence
        confidence_violations = self.validate_confidence(answer)
        all_violations.extend(confidence_violations)
        
        # Validate content
        content_violations = self.validate_content(answer)
        all_violations.extend(content_violations)
        
        # If violations found, convert to ABSTAIN
        if all_violations:
            violation_summary = "; ".join(all_violations)
            return _create_abstain_response(
                "",
                f"Policy violations detected: {violation_summary}"
            )
        
        return answer
    
    def check_policy_compliance(self, answer: IFRSAnswer) -> Dict[str, Any]:
        """Check policy compliance and return detailed results.
        
        Args:
            answer: IFRS answer to check
            
        Returns:
            Compliance check results
        """
        return {
            "is_compliant": len(self.validate_language(answer.answer)) == 0 and
                           len(self.validate_citations(answer)) == 0 and
                           len(self.validate_confidence(answer)) == 0 and
                           len(self.validate_content(answer)) == 0,
            "language_violations": self.validate_language(answer.answer),
            "citation_violations": self.validate_citations(answer),
            "confidence_violations": self.validate_confidence(answer),
            "content_violations": self.validate_content(answer),
            "total_violations": len(self.validate_language(answer.answer)) +
                              len(self.validate_citations(answer)) +
                              len(self.validate_confidence(answer)) +
                              len(self.validate_content(answer))
        }


# Global policy guard instance
policy_guard = PolicyGuard()


def validate_language(text: str) -> List[str]:
    """Validate text against language policy.
    
    Args:
        text: Text to validate
        
    Returns:
        List of violations
    """
    return policy_guard.validate_language(text)


def apply_policy(answer: IFRSAnswer) -> IFRSAnswer:
    """Apply policy guardrails to an answer.
    
    Args:
        answer: IFRS answer to validate
        
    Returns:
        Validated answer or ABSTAIN response
    """
    return policy_guard.apply_policy(answer)


def check_policy_compliance(answer: IFRSAnswer) -> Dict[str, Any]:
    """Check policy compliance for an answer.
    
    Args:
        answer: IFRS answer to check
        
    Returns:
        Compliance check results
    """
    return policy_guard.check_policy_compliance(answer)
