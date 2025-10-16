# Security Hardening Guide

## Overview

This document outlines security best practices and hardening measures for the Financial Assistant backend. Financial data requires the highest level of protection.

---

## Authentication & Authorization

### JWT Token Security

1. **Token Expiration**
   - Access tokens expire after 60 minutes by default
   - Configure via `ACCESS_TOKEN_EXPIRE_MINUTES` environment variable
   - Implement refresh token flow for extended sessions

2. **Token Generation**
   ```python
   # Use HS256 algorithm (symmetric, fast)
   from src.core.security import create_access_token
   
   token = create_access_token(
       subject=user_id,
       expires_delta=timedelta(minutes=60)
   )
   ```

3. **Token Storage (Client-side)**
   - Store in `httpOnly` cookies (not localStorage)
   - Enable `Secure` flag (HTTPS only)
   - Enable `SameSite=Strict` to prevent CSRF

### Password Security

1. **Hashing**
   - Use bcrypt with 12 rounds (CPU-intensive)
   - Never store plain passwords
   - Use `src.core.security.hash_password()`

2. **Password Validation**
   ```python
   from src.utils.validators import validate_password
   
   # Enforces:
   # - Minimum 8 characters
   # - At least one uppercase letter
   # - At least one lowercase letter
   # - At least one digit
   # - At least one special character
   validate_password(user_password)
   ```

3. **Password Reset Flow**
   - Use one-time tokens (15-minute expiration)
   - Invalidate all sessions after password change
   - Send confirmation emails

### Authorization

1. **Role-Based Access Control (RBAC)**
   - Users: Basic access to own data
   - Admins: System-wide access (future)
   - Implement via middleware and route guards

2. **Resource Ownership Verification**
   ```python
   # Always verify user owns resource
   invoice = db.query(Invoice).filter(
       Invoice.id == invoice_id,
       Invoice.user_id == current_user.id  # Ownership check
   ).first()
   
   if not invoice:
       raise NotFoundError("Invoice not found")
   ```

---

## Data Protection

### Encryption at Rest

1. **Supabase Features**
   - All data encrypted in PostgreSQL
   - Encryption keys managed by Supabase
   - Enable row-level security (RLS)

2. **Sensitive Fields to Encrypt**
   - Bank account information (if added)
   - Tax identification numbers
   - Social security numbers

### Encryption in Transit

1. **HTTPS/TLS**
   - Enforce HTTPS in production
   - Use TLS 1.3+
   - Certificate renewal via Let's Encrypt

2. **Security Headers**
   ```python
   # Implemented in src/api/main.py
   X-Content-Type-Options: nosniff
   X-Frame-Options: DENY
   X-XSS-Protection: 1; mode=block
   Strict-Transport-Security: max-age=31536000
   Content-Security-Policy: default-src 'self'
   ```

### Sensitive Data Handling

1. **Log Masking**
   ```python
   # DO NOT log sensitive data
   logger.info(f"User {user_id} logged in")  # ✓ Good
   logger.info(f"User {user.password} logged in")  # ✗ Bad
   ```

2. **Response Filtering**
   - Never return password hashes to client
   - Filter sensitive fields in API responses
   - Use Pydantic `exclude` parameter for schemas

3. **File Uploads**
   - Validate file content (not just extension)
   - Store outside web root
   - Scan for malware before processing
   - Set proper MIME types

---

## Input Validation & Sanitization

### Validation Strategy

1. **Pydantic Models**
   - Define strict schemas for all inputs
   - Use type hints and validators
   - Example:
   ```python
   from pydantic import BaseModel, EmailStr, validator
   
   class UserCreateRequest(BaseModel):
       email: EmailStr
       password: str
       first_name: str
       
       @validator('password')
       def validate_password_strength(cls, v):
           from src.utils.validators import validate_password
           return validate_password(v)
   ```

2. **Custom Validators**
   - Use `src.utils.validators` module
   - Validate email format, amounts, UUIDs, dates
   - Raise `ValidationError` for invalid inputs

3. **Whitelist Approach**
   - Only accept known field names
   - Reject unknown parameters
   - Use `forbid = True` in Pydantic config

### SQL Injection Prevention

1. **SQLAlchemy ORM**
   - Always use parameterized queries
   - Never concatenate strings
   - ✓ Safe: `User.query.filter(User.email == email)`
   - ✗ Unsafe: `db.query(f"SELECT * FROM users WHERE email = '{email}'")`

2. **Input Sanitization**
   - No user input goes directly to SQL
   - Bind parameters automatically
   - ORM prevents SQL injection

### XSS Prevention

1. **Response Encoding**
   - JSON responses automatically escaped
   - HTML content sanitized if returned

2. **CSP Headers**
   - Block inline scripts
   - Block external scripts (unless whitelisted)
   - Configured in `src/api/main.py`

---

## API Security

### Rate Limiting

1. **Implementation**
   - Per-IP rate limiting (future)
   - Per-user rate limiting
   - Different limits for different endpoints

2. **Configuration**
   ```python
   # Example implementation
   RATE_LIMITS = {
       "/auth/register": "5 per day",
       "/auth/login": "10 per hour",
       "/invoices": "100 per hour",
   }
   ```

3. **Response Headers**
   ```
   X-RateLimit-Limit: 100
   X-RateLimit-Remaining: 87
   X-RateLimit-Reset: 1609459200
   ```

### CORS Configuration

1. **Whitelist Origins**
   ```python
   # In production, only allow known frontend URLs
   ALLOWED_ORIGINS = [
       "https://app.moniagent.com",
       "https://www.moniagent.com",
   ]
   ```

2. **Restrict Methods**
   - Only allow necessary HTTP methods
   - Example: `["GET", "POST", "PUT", "DELETE"]`

3. **Credentials Handling**
   - Allow credentials for authenticated requests
   - Properly handle preflight requests

### CSRF Protection

1. **SameSite Cookies**
   - Set `SameSite=Strict` for authentication cookies
   - Prevents cross-site request forgery

2. **CSRF Tokens**
   - Consider for state-changing operations (future)
   - Validate token on POST/PUT/DELETE requests

---

## Audit & Monitoring

### Audit Trail

1. **Log All Security Events**
   - User login/logout
   - Permission changes
   - Data access/modification
   - Failed authentication attempts

2. **AI Interaction Logging**
   - Log all calls to AI services
   - Record inputs and outputs
   - Track financial data processing

3. **Database Audit Tables**
   ```python
   # Example audit logging
   class AuditLog(Base):
       __tablename__ = "audit_logs"
       
       user_id = Column(String, ForeignKey("users.id"))
       action = Column(String)  # "login", "create_budget", etc.
       resource_type = Column(String)  # "invoice", "expense", etc.
       resource_id = Column(String)
       changes = Column(JSON)
       timestamp = Column(DateTime, default=datetime.utcnow)
   ```

### Security Logging

1. **Log Levels**
   - ERROR: Security violations, failed auth
   - WARNING: Suspicious behavior, rate limit hits
   - INFO: Normal operations, successful auth
   - DEBUG: Detailed flow (disabled in production)

2. **Monitoring Alerts**
   - Multiple failed login attempts (>5 in 15 min)
   - Unusual API access patterns
   - Database errors
   - Rate limit exceedances

---

## Third-Party Integrations

### Google Gemini API Security

1. **API Key Management**
   - Store in environment variables (never in code)
   - Rotate keys regularly
   - Monitor for unauthorized usage

2. **Request/Response Handling**
   - Validate all responses from external APIs
   - Implement timeout limits (30 seconds)
   - Retry with exponential backoff

### Supabase Security

1. **Database Access**
   - Use environment-specific keys
   - Implement Row-Level Security (RLS) policies
   - Audit database access logs

2. **Admin Operations**
   - Use service role key only on backend
   - Never expose to frontend
   - Implement proper permission checks

---

## Security Checklist

### Development Phase
- [ ] All endpoints require authentication
- [ ] User resources are ownership-verified
- [ ] Passwords validated for strength
- [ ] All inputs validated via Pydantic
- [ ] Error messages don't leak information
- [ ] Logs don't contain sensitive data
- [ ] Security headers configured
- [ ] CORS properly restricted
- [ ] No secrets in version control
- [ ] Dependencies regularly updated

### Deployment Phase
- [ ] HTTPS/TLS enabled
- [ ] Rate limiting configured
- [ ] Database backups automated
- [ ] Monitoring and alerting active
- [ ] Security scanning enabled
- [ ] API documentation doesn't expose internals
- [ ] Admin endpoints properly restricted
- [ ] Error tracking configured
- [ ] Regular security audits scheduled
- [ ] Incident response plan documented

### Ongoing Operations
- [ ] Weekly security updates review
- [ ] Monthly dependency updates
- [ ] Quarterly penetration testing
- [ ] Annual security audit
- [ ] Log analysis for anomalies
- [ ] User access review quarterly
- [ ] Backup restoration tests monthly
- [ ] Security training for team

---

## Phase 6 Penetration Testing Checklist

- [ ] Fuzz chat endpoints with malformed JSON and oversized payloads
- [ ] Attempt SSRF via image URLs (not supported; ensure rejection)
- [ ] Verify upload validation (content-type, file signature, size limits)
- [ ] Enumerate auth: rate-limit login and protected routes
- [ ] Check error messages for leakage (stack traces, SQL info)
- [ ] Verify RLS and resource ownership checks on invoices/expenses
- [ ] Test JWT tampering (alg=none, wrong secret)
- [ ] Confirm AI prompt inputs are sanitized/logged without PII

See also: DEPENDENCY_AUDIT.md for dependency risk notes.

---

## Security Incident Response

### Reporting Security Issues

1. **Email**: security@moniagent.com
2. **Responsible Disclosure**: 
   - Do not publicly disclose vulnerabilities
   - Allow 90 days for fixes
   - Coordinate announcement timing

### Incident Response Steps

1. **Detection & Assessment**
   - Identify affected systems
   - Determine scope of compromise
   - Preserve evidence

2. **Containment**
   - Isolate affected systems
   - Revoke compromised credentials
   - Block malicious IPs

3. **Eradication**
   - Remove root cause
   - Patch vulnerabilities
   - Update security controls

4. **Recovery**
   - Restore systems from clean backups
   - Monitor for recurrence
   - Restore normal operations

5. **Post-Incident**
   - Notify affected users
   - Document lessons learned
   - Update security policies

---

## Additional Resources

- [OWASP Top 10](https://owasp.org/Top10/)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [FastAPI Security Docs](https://fastapi.tiangolo.com/advanced/security/)
