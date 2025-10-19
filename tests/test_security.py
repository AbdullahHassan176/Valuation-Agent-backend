"""
Security tests for PII redaction and API key enforcement.
"""

import pytest
import re
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import redact_pii, validate_api_key

class TestPIIRedaction:
    """Test PII redaction functionality."""
    
    def test_email_redaction(self):
        """Test email address redaction."""
        test_cases = [
            ("Contact us at john.doe@company.com for support", "Contact us at [REDACTED] for support"),
            ("Email: admin@example.org", "Email: [REDACTED]"),
            ("Multiple emails: user1@test.com and user2@test.org", "Multiple emails: [REDACTED] and [REDACTED]"),
        ]
        
        for input_text, expected in test_cases:
            result = redact_pii(input_text)
            assert result == expected, f"Failed for input: {input_text}"
    
    def test_iban_redaction(self):
        """Test IBAN redaction."""
        test_cases = [
            ("Account: GB29 NWBK 6016 1331 9268 19", "Account: [REDACTED]"),
            ("IBAN: DE89370400440532013000", "IBAN: [REDACTED]"),
            ("Transfer to FR1420041010050500013M02606", "Transfer to [REDACTED]"),
        ]
        
        for input_text, expected in test_cases:
            result = redact_pii(input_text)
            assert result == expected, f"Failed for input: {input_text}"
    
    def test_phone_redaction(self):
        """Test phone number redaction."""
        test_cases = [
            ("Call us at +1-555-123-4567", "Call us at [REDACTED]"),
            ("Phone: +44 20 7946 0958", "Phone: [REDACTED]"),
            ("Contact: 555-123-4567", "Contact: [REDACTED]"),
        ]
        
        for input_text, expected in test_cases:
            result = redact_pii(input_text)
            assert result == expected, f"Failed for input: {input_text}"
    
    def test_credit_card_redaction(self):
        """Test credit card number redaction."""
        test_cases = [
            ("Card: 4532-1234-5678-9012", "Card: [REDACTED]"),
            ("Payment: 4532123456789012", "Payment: [REDACTED]"),
            ("Visa: 4532 1234 5678 9012", "Visa: [REDACTED]"),
        ]
        
        for input_text, expected in test_cases:
            result = redact_pii(input_text)
            assert result == expected, f"Failed for input: {input_text}"
    
    def test_ssn_redaction(self):
        """Test Social Security Number redaction."""
        test_cases = [
            ("SSN: 123-45-6789", "SSN: [REDACTED]"),
            ("Social: 123456789", "Social: [REDACTED]"),
            ("Tax ID: 123-45-6789", "Tax ID: [REDACTED]"),
        ]
        
        for input_text, expected in test_cases:
            result = redact_pii(input_text)
            assert result == expected, f"Failed for input: {input_text}"
    
    def test_multiple_pii_types(self):
        """Test redaction of multiple PII types in one text."""
        input_text = """
        Contact John Doe at john.doe@company.com
        Phone: +1-555-123-4567
        Account: GB29 NWBK 6016 1331 9268 19
        SSN: 123-45-6789
        """
        
        result = redact_pii(input_text)
        
        # Should redact all PII types
        assert "[REDACTED]" in result
        assert "john.doe@company.com" not in result
        assert "+1-555-123-4567" not in result
        assert "GB29 NWBK 6016 1331 9268 19" not in result
        assert "123-45-6789" not in result
    
    def test_no_pii_preservation(self):
        """Test that non-PII text is preserved."""
        input_text = "This is a normal business document with no sensitive information."
        result = redact_pii(input_text)
        assert result == input_text
    
    def test_edge_cases(self):
        """Test edge cases for PII redaction."""
        test_cases = [
            ("", ""),  # Empty string
            ("No PII here", "No PII here"),  # No PII
            ("@symbol", "@symbol"),  # Just @ symbol
            ("123", "123"),  # Just numbers
        ]
        
        for input_text, expected in test_cases:
            result = redact_pii(input_text)
            assert result == expected, f"Failed for input: {input_text}"


class TestAPIKeyEnforcement:
    """Test API key enforcement."""
    
    def test_protected_endpoint_without_key(self):
        """Test that protected endpoints reject requests without API key."""
        client = TestClient(app)
        
        # Test various protected endpoints
        protected_endpoints = [
            "/api/v1/ifrs/ask",
            "/api/v1/docs/upload",
            "/api/v1/docs/ingest",
            "/api/v1/runs/create",
            "/api/v1/metrics/summary",
        ]
        
        for endpoint in protected_endpoints:
            response = client.post(endpoint, json={"test": "data"})
            assert response.status_code == 401, f"Endpoint {endpoint} should require API key"
            assert "API key required" in response.json()["detail"].lower()
    
    def test_protected_endpoint_with_invalid_key(self):
        """Test that protected endpoints reject requests with invalid API key."""
        client = TestClient(app)
        
        headers = {"X-API-Key": "invalid-key"}
        
        response = client.post(
            "/api/v1/ifrs/ask",
            json={"question": "What is IFRS 13?"},
            headers=headers
        )
        
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]
    
    def test_protected_endpoint_with_valid_key(self):
        """Test that protected endpoints accept requests with valid API key."""
        client = TestClient(app)
        
        headers = {"X-API-Key": "test-key"}
        
        # Mock the IFRS agent to avoid actual processing
        with patch('app.agents.ifrs.answer_ifrs') as mock_answer:
            mock_answer.return_value = {
                "answer": "Test answer",
                "status": "OK",
                "confidence": 0.9,
                "citations": []
            }
            
            response = client.post(
                "/api/v1/ifrs/ask",
                json={"question": "What is IFRS 13?"},
                headers=headers
            )
            
            assert response.status_code == 200
    
    def test_health_endpoint_no_key_required(self):
        """Test that health endpoint doesn't require API key."""
        client = TestClient(app)
        
        response = client.get("/healthz")
        assert response.status_code == 200
    
    def test_docs_endpoint_no_key_required(self):
        """Test that OpenAPI docs endpoint doesn't require API key."""
        client = TestClient(app)
        
        response = client.get("/docs")
        assert response.status_code == 200


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limit_enforcement(self):
        """Test that rate limiting is enforced."""
        client = TestClient(app)
        
        headers = {"X-API-Key": "test-key"}
        
        # Make multiple requests quickly
        responses = []
        for i in range(105):  # Exceed rate limit of 100/min
            response = client.post(
                "/api/v1/ifrs/ask",
                json={"question": f"Test question {i}"},
                headers=headers
            )
            responses.append(response)
        
        # Check that some requests were rate limited
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) > 0, "Rate limiting should be enforced"
    
    def test_rate_limit_headers(self):
        """Test that rate limit headers are present."""
        client = TestClient(app)
        
        headers = {"X-API-Key": "test-key"}
        
        response = client.post(
            "/api/v1/ifrs/ask",
            json={"question": "Test question"},
            headers=headers
        )
        
        # Check for rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers


class TestRequestSizeLimits:
    """Test request size limits."""
    
    def test_large_request_rejection(self):
        """Test that large requests are rejected."""
        client = TestClient(app)
        
        headers = {"X-API-Key": "test-key"}
        
        # Create a large request (over 10MB limit)
        large_data = "x" * (11 * 1024 * 1024)  # 11MB
        
        response = client.post(
            "/api/v1/docs/upload",
            data={"file": large_data},
            headers=headers
        )
        
        assert response.status_code == 413  # Payload too large
    
    def test_normal_request_acceptance(self):
        """Test that normal-sized requests are accepted."""
        client = TestClient(app)
        
        headers = {"X-API-Key": "test-key"}
        
        # Create a normal-sized request
        normal_data = "x" * (1024 * 1024)  # 1MB
        
        with patch('app.routers.docs.upload_document') as mock_upload:
            mock_upload.return_value = {"status": "success"}
            
            response = client.post(
                "/api/v1/docs/upload",
                data={"file": normal_data},
                headers=headers
            )
            
            # Should not be rejected due to size
            assert response.status_code != 413


class TestSecurityHeaders:
    """Test security headers."""
    
    def test_security_headers_present(self):
        """Test that security headers are present in responses."""
        client = TestClient(app)
        
        response = client.get("/healthz")
        
        # Check for security headers
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
        ]
        
        for header in security_headers:
            assert header in response.headers, f"Security header {header} should be present"
    
    def test_cors_headers(self):
        """Test CORS headers."""
        client = TestClient(app)
        
        response = client.options("/api/v1/ifrs/ask")
        
        # Check for CORS headers
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers


class TestInputValidation:
    """Test input validation and sanitization."""
    
    def test_sql_injection_prevention(self):
        """Test that SQL injection attempts are handled safely."""
        client = TestClient(app)
        
        headers = {"X-API-Key": "test-key"}
        
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "UNION SELECT * FROM users",
        ]
        
        for malicious_input in malicious_inputs:
            response = client.post(
                "/api/v1/ifrs/ask",
                json={"question": malicious_input},
                headers=headers
            )
            
            # Should not cause server errors
            assert response.status_code in [200, 400, 422], f"SQL injection attempt should be handled safely: {malicious_input}"
    
    def test_xss_prevention(self):
        """Test that XSS attempts are handled safely."""
        client = TestClient(app)
        
        headers = {"X-API-Key": "test-key"}
        
        xss_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
        ]
        
        for xss_input in xss_inputs:
            response = client.post(
                "/api/v1/ifrs/ask",
                json={"question": xss_input},
                headers=headers
            )
            
            # Should not cause server errors
            assert response.status_code in [200, 400, 422], f"XSS attempt should be handled safely: {xss_input}"
            
            # Response should not contain unescaped script tags
            if response.status_code == 200:
                response_text = str(response.json())
                assert "<script>" not in response_text, "XSS should be prevented"


if __name__ == "__main__":
    pytest.main([__file__])
