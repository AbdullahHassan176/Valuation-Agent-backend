# Security Playbook

## Overview

This document outlines security policies, procedures, and best practices for the Valuation Agent system. All team members must follow these guidelines to ensure system security and data protection.

## Data Boundaries & Storage

### Data Classification
- **Public**: Non-sensitive information that can be freely shared
- **Internal**: Company information not for public disclosure
- **Confidential**: Sensitive business information requiring protection
- **Restricted**: Highly sensitive data with strict access controls

### Storage Locations
- **Vector Database**: `/app/.vector/ifrs` - Encrypted at rest
- **Document Store**: `/app/.docs` - Access-controlled directory
- **Audit Database**: `/app/.run/audit.db` - SQLite with encryption
- **Logs**: `/app/.run/audit.log` - Rotated and secured

### Data Retention Policy
- **Audit Logs**: 7 years (regulatory requirement)
- **Valuation Runs**: 180 days (configurable)
- **Export Files**: 90 days
- **Vector Embeddings**: Permanent (until document deletion)

## PII Redaction

### Redaction Patterns
```regex
# Email addresses
\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b

# IBAN (International Bank Account Numbers)
\b[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{7}([A-Z0-9]?){0,16}\b

# Phone numbers (international format)
\b\+?[1-9]\d{1,14}\b

# Credit Card numbers (basic pattern)
\b[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}\b

# Social Security Numbers (US format)
\b\d{3}-\d{2}-\d{4}\b

# Tax IDs
\b[A-Z]{2}[0-9]{6}[A-Z0-9]{2}\b
```

### Implementation
- All user inputs are scanned for PII patterns
- Matches are replaced with `[REDACTED]` before processing
- Redaction is logged for audit purposes
- Original data is never stored in plain text

## API Key Policy

### Key Management
- **Development**: `dev-key` (local development only)
- **Staging**: Rotated every 30 days
- **Production**: Rotated every 90 days
- **Emergency**: Immediate rotation capability

### Key Format
- Minimum 32 characters
- Mix of alphanumeric and special characters
- Stored as environment variables only
- Never committed to version control

### Access Control
- API keys required for all endpoints except health checks
- Rate limiting: 100 requests per minute per key
- Request size limit: 10MB per request
- IP whitelisting available for production

## Rate Limiting

### Implementation
- Token bucket algorithm
- 100 requests per minute per IP
- Burst allowance: 20 requests
- 429 status code for rate limit exceeded

### Monitoring
- Rate limit violations logged
- Automatic IP blocking after 5 violations
- Admin notification for repeated violations

## Incident Response

### Security Incident Classification
1. **Low**: Minor policy violations, no data exposure
2. **Medium**: Potential data exposure, system compromise
3. **High**: Confirmed data breach, system compromise
4. **Critical**: Widespread breach, regulatory impact

### Response Procedures

#### Low/Medium Incidents
1. Log incident in security tracking system
2. Notify security team within 1 hour
3. Implement containment measures
4. Document findings and remediation
5. Update security policies if needed

#### High/Critical Incidents
1. Immediate notification to security team and management
2. Activate incident response team
3. Implement emergency containment
4. Notify legal and compliance teams
5. Prepare regulatory notifications if required
6. Conduct post-incident review

### Communication
- Internal: Security team, management, legal
- External: Customers (if data affected), regulators (if required)
- Timeline: Within 24 hours for high/critical incidents

## Access Control

### Authentication
- Multi-factor authentication required for all admin accounts
- Session timeout: 30 minutes of inactivity
- Password policy: 12+ characters, mixed case, numbers, symbols
- Account lockout: 5 failed attempts

### Authorization
- Role-based access control (RBAC)
- Principle of least privilege
- Regular access reviews (quarterly)
- Immediate access revocation for terminated employees

### Audit Requirements
- All authentication events logged
- Failed login attempts monitored
- Privilege escalation tracked
- Regular audit log reviews

## Data Encryption

### At Rest
- Database: AES-256 encryption
- File storage: Encrypted volumes
- Backup: Encrypted before transmission
- Vector embeddings: Encrypted storage

### In Transit
- TLS 1.3 for all API communications
- HTTPS only for web interfaces
- Certificate pinning for mobile apps
- VPN for internal communications

## Backup Security

### Backup Procedures
- Daily automated backups
- Encrypted before storage
- Tested restoration procedures
- Off-site storage for critical data

### Recovery Testing
- Monthly backup restoration tests
- Documented recovery procedures
- Recovery time objectives defined
- Business continuity planning

## Monitoring & Alerting

### Security Monitoring
- Failed authentication attempts
- Unusual access patterns
- Data exfiltration attempts
- System vulnerabilities

### Alert Thresholds
- 5+ failed logins from same IP
- Unusual data access patterns
- System resource anomalies
- Security scan failures

### Response Times
- Critical alerts: Immediate
- High priority: Within 15 minutes
- Medium priority: Within 1 hour
- Low priority: Within 4 hours

## Compliance Requirements

### Regulatory Standards
- GDPR compliance for EU data
- SOX compliance for financial data
- Industry-specific regulations
- Data residency requirements

### Documentation
- Security policies documented
- Procedures regularly updated
- Training materials current
- Compliance reports maintained

## Security Testing

### Automated Testing
- Daily vulnerability scans
- Weekly penetration testing
- Monthly security assessments
- Quarterly compliance audits

### Manual Testing
- Annual penetration testing
- Security code reviews
- Social engineering tests
- Physical security assessments

## Training & Awareness

### Security Training
- New employee security orientation
- Annual security awareness training
- Phishing simulation exercises
- Incident response training

### Documentation
- Security policies accessible
- Procedures clearly documented
- Training materials updated
- Knowledge base maintained

## Contact Information

### Security Team
- Email: security@company.com
- Phone: +1-XXX-XXX-XXXX
- Emergency: 24/7 security hotline

### Escalation
- Security Manager: [Name]
- CISO: [Name]
- Legal: [Name]
- Compliance: [Name]

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-18 | Security Team | Initial version |

---

**Note**: This document is confidential and for internal use only. Distribution is restricted to authorized personnel.
