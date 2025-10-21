"""
Security validation system for the Valuation Agent platform
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import hashlib
import secrets
import re

class SecurityLevel(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class SecurityStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    INFO = "INFO"

@dataclass
class SecurityCheck:
    """Individual security check result"""
    id: str
    name: str
    status: SecurityStatus
    level: SecurityLevel
    message: str
    details: Dict[str, Any]
    recommendations: List[str]

@dataclass
class SecurityReport:
    """Complete security validation report"""
    timestamp: datetime
    overall_score: float
    total_checks: int
    passed_checks: int
    failed_checks: int
    warning_checks: int
    critical_issues: int
    checks: List[SecurityCheck]
    summary: Dict[str, Any]

class SecurityValidator:
    """Main security validation system"""
    
    def __init__(self):
        self.checks = []
    
    def validate_api_security(self, config: Dict[str, Any]) -> List[SecurityCheck]:
        """Validate API security configuration"""
        checks = []
        
        # API Key validation
        api_key = config.get('API_KEY', '')
        if api_key and len(api_key) >= 32:
            if self._is_strong_api_key(api_key):
                checks.append(SecurityCheck(
                    id="api_key_strength",
                    name="API Key Strength",
                    status=SecurityStatus.PASS,
                    level=SecurityLevel.CRITICAL,
                    message="API key meets security requirements",
                    details={"length": len(api_key), "has_entropy": True},
                    recommendations=[]
                ))
            else:
                checks.append(SecurityCheck(
                    id="api_key_strength",
                    name="API Key Strength",
                    status=SecurityStatus.WARNING,
                    level=SecurityLevel.CRITICAL,
                    message="API key should be more random",
                    details={"length": len(api_key)},
                    recommendations=["Use a cryptographically secure random generator", "Include mixed case, numbers, and symbols"]
                ))
        else:
            checks.append(SecurityCheck(
                id="api_key_strength",
                name="API Key Strength",
                status=SecurityStatus.FAIL,
                level=SecurityLevel.CRITICAL,
                message="API key is missing or too short",
                details={"length": len(api_key)},
                recommendations=["Generate a secure API key with at least 32 characters"]
            ))
        
        # Rate limiting validation
        rate_limit = config.get('RATE_LIMIT_REQUESTS_PER_MINUTE', 0)
        if rate_limit > 0:
            if rate_limit <= 100:
                checks.append(SecurityCheck(
                    id="rate_limiting",
                    name="Rate Limiting",
                    status=SecurityStatus.PASS,
                    level=SecurityLevel.HIGH,
                    message="Rate limiting is configured appropriately",
                    details={"requests_per_minute": rate_limit},
                    recommendations=[]
                ))
            else:
                checks.append(SecurityCheck(
                    id="rate_limiting",
                    name="Rate Limiting",
                    status=SecurityStatus.WARNING,
                    level=SecurityLevel.HIGH,
                    message="Rate limit may be too permissive",
                    details={"requests_per_minute": rate_limit},
                    recommendations=["Consider reducing rate limit for better security"]
                ))
        else:
            checks.append(SecurityCheck(
                id="rate_limiting",
                name="Rate Limiting",
                status=SecurityStatus.FAIL,
                level=SecurityLevel.HIGH,
                message="Rate limiting is not configured",
                details={},
                recommendations=["Enable rate limiting to prevent abuse"]
            ))
        
        # Request size validation
        max_request_size = config.get('MAX_REQUEST_SIZE_MB', 0)
        if max_request_size > 0:
            if max_request_size <= 10:
                checks.append(SecurityCheck(
                    id="request_size_limit",
                    name="Request Size Limit",
                    status=SecurityStatus.PASS,
                    level=SecurityLevel.MEDIUM,
                    message="Request size limit is appropriate",
                    details={"max_size_mb": max_request_size},
                    recommendations=[]
                ))
            else:
                checks.append(SecurityCheck(
                    id="request_size_limit",
                    name="Request Size Limit",
                    status=SecurityStatus.WARNING,
                    level=SecurityLevel.MEDIUM,
                    message="Request size limit may be too large",
                    details={"max_size_mb": max_request_size},
                    recommendations=["Consider reducing request size limit"]
                ))
        else:
            checks.append(SecurityCheck(
                id="request_size_limit",
                name="Request Size Limit",
                status=SecurityStatus.FAIL,
                level=SecurityLevel.MEDIUM,
                message="Request size limit is not configured",
                details={},
                recommendations=["Set a reasonable request size limit"]
            ))
        
        return checks
    
    def validate_cors_security(self, config: Dict[str, Any]) -> List[SecurityCheck]:
        """Validate CORS security configuration"""
        checks = []
        
        # CORS origins validation
        allowed_origins = config.get('ALLOW_ORIGINS', [])
        if allowed_origins:
            if self._are_secure_origins(allowed_origins):
                checks.append(SecurityCheck(
                    id="cors_origins",
                    name="CORS Origins",
                    status=SecurityStatus.PASS,
                    level=SecurityLevel.HIGH,
                    message="CORS origins are properly configured",
                    details={"origins": allowed_origins},
                    recommendations=[]
                ))
            else:
                checks.append(SecurityCheck(
                    id="cors_origins",
                    name="CORS Origins",
                    status=SecurityStatus.WARNING,
                    level=SecurityLevel.HIGH,
                    message="Some CORS origins may be insecure",
                    details={"origins": allowed_origins},
                    recommendations=["Use HTTPS origins in production", "Avoid wildcard origins"]
                ))
        else:
            checks.append(SecurityCheck(
                id="cors_origins",
                name="CORS Origins",
                status=SecurityStatus.FAIL,
                level=SecurityLevel.HIGH,
                message="CORS origins are not configured",
                details={},
                recommendations=["Configure specific allowed origins"]
            ))
        
        return checks
    
    def validate_data_security(self, config: Dict[str, Any]) -> List[SecurityCheck]:
        """Validate data security configuration"""
        checks = []
        
        # PII redaction validation
        pii_redaction = config.get('PII_REDACTION_ENABLED', False)
        if pii_redaction:
            checks.append(SecurityCheck(
                id="pii_redaction",
                name="PII Redaction",
                status=SecurityStatus.PASS,
                level=SecurityLevel.HIGH,
                message="PII redaction is enabled",
                details={"enabled": pii_redaction},
                recommendations=[]
            ))
        else:
            checks.append(SecurityCheck(
                id="pii_redaction",
                name="PII Redaction",
                status=SecurityStatus.WARNING,
                level=SecurityLevel.HIGH,
                message="PII redaction is not enabled",
                details={"enabled": pii_redaction},
                recommendations=["Enable PII redaction for data protection"]
            ))
        
        # Database security validation
        db_url = config.get('AUDIT_DB_URL', '')
        if db_url:
            if self._is_secure_db_url(db_url):
                checks.append(SecurityCheck(
                    id="database_security",
                    name="Database Security",
                    status=SecurityStatus.PASS,
                    level=SecurityLevel.CRITICAL,
                    message="Database connection is secure",
                    details={"url_type": "secure"},
                    recommendations=[]
                ))
            else:
                checks.append(SecurityCheck(
                    id="database_security",
                    name="Database Security",
                    status=SecurityStatus.WARNING,
                    level=SecurityLevel.CRITICAL,
                    message="Database connection may not be secure",
                    details={"url_type": "check_required"},
                    recommendations=["Use encrypted database connections", "Ensure proper authentication"]
                ))
        else:
            checks.append(SecurityCheck(
                id="database_security",
                name="Database Security",
                status=SecurityStatus.FAIL,
                level=SecurityLevel.CRITICAL,
                message="Database URL is not configured",
                details={},
                recommendations=["Configure database connection"]
            ))
        
        return checks
    
    def validate_environment_security(self, config: Dict[str, Any]) -> List[SecurityCheck]:
        """Validate environment security configuration"""
        checks = []
        
        # Debug mode validation
        debug_mode = config.get('DEBUG', False)
        environment = config.get('ENVIRONMENT', '')
        
        if environment == 'production':
            if not debug_mode:
                checks.append(SecurityCheck(
                    id="debug_mode",
                    name="Debug Mode",
                    status=SecurityStatus.PASS,
                    level=SecurityLevel.HIGH,
                    message="Debug mode is disabled in production",
                    details={"debug": debug_mode, "environment": environment},
                    recommendations=[]
                ))
            else:
                checks.append(SecurityCheck(
                    id="debug_mode",
                    name="Debug Mode",
                    status=SecurityStatus.FAIL,
                    level=SecurityLevel.CRITICAL,
                    message="Debug mode is enabled in production",
                    details={"debug": debug_mode, "environment": environment},
                    recommendations=["Disable debug mode in production"]
                ))
        else:
            checks.append(SecurityCheck(
                id="debug_mode",
                name="Debug Mode",
                status=SecurityStatus.INFO,
                level=SecurityLevel.LOW,
                message="Debug mode status for development environment",
                details={"debug": debug_mode, "environment": environment},
                recommendations=[]
            ))
        
        # Environment variable exposure validation
        sensitive_vars = ['API_KEY', 'DATABASE_URL', 'SECRET_KEY', 'PASSWORD']
        exposed_vars = []
        
        for var in sensitive_vars:
            if var in config and config[var]:
                # Check if the value looks like a placeholder
                value = str(config[var])
                if any(placeholder in value.lower() for placeholder in ['change_me', 'your_', 'placeholder', 'example']):
                    exposed_vars.append(var)
        
        if not exposed_vars:
            checks.append(SecurityCheck(
                id="sensitive_vars",
                name="Sensitive Variables",
                status=SecurityStatus.PASS,
                level=SecurityLevel.HIGH,
                message="No sensitive variables appear to be using default values",
                details={"checked_vars": sensitive_vars},
                recommendations=[]
            ))
        else:
            checks.append(SecurityCheck(
                id="sensitive_vars",
                name="Sensitive Variables",
                status=SecurityStatus.FAIL,
                level=SecurityLevel.CRITICAL,
                message="Some sensitive variables are using default/placeholder values",
                details={"exposed_vars": exposed_vars},
                recommendations=["Change all default/placeholder values", "Use environment-specific secrets"]
            ))
        
        return checks
    
    def validate_network_security(self, config: Dict[str, Any]) -> List[SecurityCheck]:
        """Validate network security configuration"""
        checks = []
        
        # HTTPS enforcement validation
        api_url = config.get('NEXT_PUBLIC_API_URL', '')
        if api_url:
            if api_url.startswith('https://'):
                checks.append(SecurityCheck(
                    id="https_enforcement",
                    name="HTTPS Enforcement",
                    status=SecurityStatus.PASS,
                    level=SecurityLevel.HIGH,
                    message="API URL uses HTTPS",
                    details={"url": api_url},
                    recommendations=[]
                ))
            else:
                checks.append(SecurityCheck(
                    id="https_enforcement",
                    name="HTTPS Enforcement",
                    status=SecurityStatus.WARNING,
                    level=SecurityLevel.HIGH,
                    message="API URL does not use HTTPS",
                    details={"url": api_url},
                    recommendations=["Use HTTPS in production", "Configure SSL certificates"]
                ))
        else:
            checks.append(SecurityCheck(
                id="https_enforcement",
                name="HTTPS Enforcement",
                status=SecurityStatus.FAIL,
                level=SecurityLevel.HIGH,
                message="API URL is not configured",
                details={},
                recommendations=["Configure API URL"]
            ))
        
        return checks
    
    def _is_strong_api_key(self, api_key: str) -> bool:
        """Check if API key is cryptographically strong"""
        if len(api_key) < 32:
            return False
        
        # Check for entropy (basic check)
        has_upper = any(c.isupper() for c in api_key)
        has_lower = any(c.islower() for c in api_key)
        has_digit = any(c.isdigit() for c in api_key)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in api_key)
        
        return has_upper and has_lower and has_digit and has_special
    
    def _are_secure_origins(self, origins: List[str]) -> bool:
        """Check if CORS origins are secure"""
        for origin in origins:
            if origin == "*":
                return False
            if not origin.startswith(('http://localhost', 'https://')):
                return False
        return True
    
    def _is_secure_db_url(self, db_url: str) -> bool:
        """Check if database URL is secure"""
        # Basic check for encrypted connections
        return any(protocol in db_url.lower() for protocol in ['postgresql://', 'mysql://', 'sqlite://'])
    
    def generate_security_report(self, config: Dict[str, Any]) -> SecurityReport:
        """Generate comprehensive security report"""
        all_checks = []
        
        # Run all security validation categories
        all_checks.extend(self.validate_api_security(config))
        all_checks.extend(self.validate_cors_security(config))
        all_checks.extend(self.validate_data_security(config))
        all_checks.extend(self.validate_environment_security(config))
        all_checks.extend(self.validate_network_security(config))
        
        # Calculate summary statistics
        total_checks = len(all_checks)
        passed_checks = sum(1 for check in all_checks if check.status == SecurityStatus.PASS)
        failed_checks = sum(1 for check in all_checks if check.status == SecurityStatus.FAIL)
        warning_checks = sum(1 for check in all_checks if check.status == SecurityStatus.WARNING)
        critical_issues = sum(1 for check in all_checks if check.status == SecurityStatus.FAIL and check.level == SecurityLevel.CRITICAL)
        
        # Calculate overall security score
        score_weights = {
            SecurityLevel.CRITICAL: 4,
            SecurityLevel.HIGH: 3,
            SecurityLevel.MEDIUM: 2,
            SecurityLevel.LOW: 1
        }
        
        total_weighted_score = 0
        max_weighted_score = 0
        
        for check in all_checks:
            weight = score_weights[check.level]
            max_weighted_score += weight
            
            if check.status == SecurityStatus.PASS:
                total_weighted_score += weight
            elif check.status == SecurityStatus.WARNING:
                total_weighted_score += weight * 0.5
        
        overall_score = (total_weighted_score / max_weighted_score * 100) if max_weighted_score > 0 else 0
        
        # Create summary
        summary = {
            "security_score": round(overall_score, 2),
            "critical_issues": critical_issues,
            "recommendations": list(set([
                rec for check in all_checks 
                for rec in check.recommendations
            ])),
            "category_summary": {
                "API Security": len([c for c in all_checks if "api" in c.id.lower()]),
                "CORS Security": len([c for c in all_checks if "cors" in c.id.lower()]),
                "Data Security": len([c for c in all_checks if "pii" in c.id.lower() or "database" in c.id.lower()]),
                "Environment Security": len([c for c in all_checks if "debug" in c.id.lower() or "sensitive" in c.id.lower()]),
                "Network Security": len([c for c in all_checks if "https" in c.id.lower()])
            }
        }
        
        return SecurityReport(
            timestamp=datetime.now(),
            overall_score=overall_score,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warning_checks=warning_checks,
            critical_issues=critical_issues,
            checks=all_checks,
            summary=summary
        )

def validate_security(config: Dict[str, Any]) -> SecurityReport:
    """Main function to validate security configuration"""
    validator = SecurityValidator()
    return validator.generate_security_report(config)




