# Threat Model & Security Analysis
## Student Counsellor SaaS Platform

**Date**: January 25, 2026  
**Version**: 2.0.0  
**Status**: Security Review

---

## Executive Summary

This document identifies security threats, vulnerabilities, and gaps in the Student Counsellor platform. **7 CRITICAL** and **12 HIGH** priority security issues have been identified that require immediate attention.

---

## Threat Categories

### 1. Authentication & Authorization
### 2. Data Protection & Privacy
### 3. API Security
### 4. Multi-Tenancy Isolation
### 5. Input Validation & Injection
### 6. Error Handling & Information Disclosure
### 7. Infrastructure & Configuration

---

## CRITICAL Security Gaps

### 🔴 CRITICAL-1: Information Disclosure via Error Messages
**Severity**: CRITICAL  
**Location**: `backend/app/main.py:50-57`

**Issue**:
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": traceback.format_exc()}
    )
```

**Risk**: Full stack traces exposed in production, revealing:
- Database structure
- File paths
- Internal error details
- Code structure

**Impact**: Attackers can gain insights into system architecture and exploit vulnerabilities.

**Recommendation**:
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "traceback": traceback.format_exc()}
        )
    else:
        # Log full error server-side
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred. Please contact support."}
        )
```

---

### 🔴 CRITICAL-2: Weak Secret Key in Production
**Severity**: CRITICAL  
**Location**: `backend/app/core/config.py:15`

**Issue**:
```python
SECRET_KEY: str = "your-super-secret-key-change-in-production"
```

**Risk**: 
- JWT tokens can be forged
- Session hijacking
- Complete authentication bypass

**Impact**: Attackers can create valid tokens for any user.

**Recommendation**:
- Use environment variable with strong random key
- Generate with: `openssl rand -hex 32`
- Never commit secrets to repository
- Use secrets management (AWS Secrets Manager, HashiCorp Vault)

---

### 🔴 CRITICAL-3: No Rate Limiting
**Severity**: CRITICAL  
**Location**: All authentication endpoints

**Issue**: No rate limiting on:
- Login attempts
- Password reset requests
- Registration attempts
- API endpoints

**Risk**:
- Brute force attacks
- Account enumeration
- DoS attacks
- Resource exhaustion

**Impact**: 
- Credential stuffing attacks
- System overload
- Service unavailability

**Recommendation**:
```python
# Add slowapi or fastapi-limiter
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")  # 5 attempts per minute
async def login(...):
    pass

@router.post("/forgot-password")
@limiter.limit("3/hour")  # 3 requests per hour per IP
async def forgot_password(...):
    pass
```

---

### 🔴 CRITICAL-4: Overly Permissive CORS
**Severity**: CRITICAL  
**Location**: `backend/app/main.py:32-43`

**Issue**:
```python
allow_origins=[
    "http://localhost:3000",
    "http://localhost:5173",
    # Hardcoded localhost only
],
allow_methods=["*"],  # Allows all HTTP methods
allow_headers=["*"],  # Allows all headers
```

**Risk**:
- CSRF attacks
- Unauthorized API access from malicious sites
- Credential theft

**Impact**: Malicious websites can make authenticated requests on behalf of users.

**Recommendation**:
```python
# Use environment variables for production origins
allow_origins=settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS else [],
allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
allow_headers=["Authorization", "Content-Type"],
allow_credentials=True,
```

---

### 🔴 CRITICAL-5: Public Endpoint Exposes Sensitive Data
**Severity**: CRITICAL  
**Location**: `backend/app/main.py:83-97`

**Issue**:
```python
@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Public endpoint for demo - in production, add auth"""
    stats = {
        "total_students": await database.users.count_documents({"role": "student"}),
        "total_counsellors": await database.users.count_documents({"role": "counsellor"}),
        # Exposes system-wide statistics
    }
```

**Risk**:
- Information disclosure
- System enumeration
- Competitive intelligence

**Impact**: Attackers can gather information about system usage and scale.

**Recommendation**:
- Remove or add authentication
- Scope to institution if needed
- Add rate limiting

---

### 🔴 CRITICAL-6: No JWT Token Revocation
**Severity**: CRITICAL  
**Location**: `backend/app/core/security.py`

**Issue**: 
- No token blacklist/revocation mechanism
- Tokens valid until expiration even after:
  - Password change
  - Account deactivation
  - Suspicious activity

**Risk**:
- Stolen tokens remain valid
- Cannot invalidate compromised sessions
- No way to force re-authentication

**Impact**: Compromised tokens can be used until expiration (30 minutes default).

**Recommendation**:
```python
# Add token blacklist
class TokenBlacklist:
    async def revoke_token(self, token: str, expires_at: datetime):
        # Store in Redis/MongoDB with TTL
        pass
    
    async def is_revoked(self, token: str) -> bool:
        # Check if token is blacklisted
        pass
```

---

### 🔴 CRITICAL-7: NoSQL Injection Vulnerabilities
**Severity**: CRITICAL  
**Location**: Multiple endpoints using ObjectId

**Issue**: 
- ObjectId validation may fail silently
- User-controlled input directly in queries
- No input sanitization for MongoDB operators

**Risk**:
```python
# Vulnerable pattern:
user_id = request.path_params["user_id"]
user = await database.users.find_one({"_id": ObjectId(user_id)})
# If user_id is malformed, exception is caught but may leak info
```

**Impact**: Potential for NoSQL injection attacks, data exfiltration.

**Recommendation**:
```python
def validate_object_id(id_str: str) -> ObjectId:
    """Safely validate and convert to ObjectId"""
    try:
        if not ObjectId.is_valid(id_str):
            raise HTTPException(status_code=400, detail="Invalid ID format")
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

# Use everywhere:
user_id_obj = validate_object_id(user_id)
```

---

## HIGH Priority Security Gaps

### 🟠 HIGH-1: Missing Input Validation
**Severity**: HIGH  
**Location**: Various endpoints

**Issues**:
- Email validation exists but could be stricter
- No length limits on some text fields
- No sanitization of user-generated content
- Phone number format not validated

**Recommendation**:
- Add comprehensive Pydantic validators
- Sanitize HTML content in messages/notes
- Validate file uploads (if added)
- Enforce field length limits

---

### 🟠 HIGH-2: Password Reset Token Security
**Severity**: HIGH  
**Location**: `backend/app/api/auth.py:344-400`

**Issues**:
- No rate limiting on token generation
- Tokens stored in database (could be exposed)
- No token reuse prevention beyond `used` flag
- 1-hour expiration may be too long

**Recommendation**:
- Add rate limiting (3 requests/hour)
- Consider shorter expiration (15-30 minutes)
- Add IP-based tracking
- Implement token rotation

---

### 🟠 HIGH-3: Session Management Weaknesses
**Severity**: HIGH  
**Location**: JWT token handling

**Issues**:
- No refresh tokens
- Long-lived access tokens (30 minutes)
- No device/session tracking
- Cannot see active sessions

**Recommendation**:
- Implement refresh token rotation
- Add session management API
- Track active sessions per user
- Allow users to revoke sessions

---

### 🟠 HIGH-4: Insufficient Audit Logging
**Severity**: HIGH  
**Location**: `backend/app/core/audit.py`

**Issues**:
- May log sensitive data (passwords, tokens)
- No log retention policy enforcement
- No log integrity protection
- Limited query capabilities

**Recommendation**:
- Sanitize sensitive data before logging
- Implement log rotation
- Add log signing/encryption
- Create audit log query API

---

### 🟠 HIGH-5: Multi-Tenancy Bypass Risks
**Severity**: HIGH  
**Location**: Various endpoints

**Issues**:
- Some queries may not properly filter by `institution_id`
- Counsellor access checks may be incomplete
- Student data access verification inconsistent

**Recommendation**:
- Audit all database queries
- Use `TenantAwareRepository` consistently
- Add integration tests for tenant isolation
- Implement query logging for tenant violations

---

### 🟠 HIGH-6: Email Enumeration (Partial)
**Severity**: HIGH  
**Location**: `backend/app/api/auth.py:344`

**Issue**: 
- Forgot password prevents enumeration ✅
- But login endpoint reveals if email exists
- Registration reveals if email exists

**Recommendation**:
```python
# In login endpoint:
# Always return same error message regardless of email existence
if not user or not verify_password(...):
    # Add artificial delay to prevent timing attacks
    await asyncio.sleep(0.5)  # Constant delay
    raise HTTPException(
        status_code=401,
        detail="Incorrect email or password"
    )
```

---

### 🟠 HIGH-7: Missing Security Headers
**Severity**: HIGH  
**Location**: Response headers

**Issues**:
- No Content-Security-Policy
- No X-Frame-Options
- No X-Content-Type-Options
- No Strict-Transport-Security (HSTS)

**Recommendation**:
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

---

### 🟠 HIGH-8: Password Policy Weakness
**Severity**: HIGH  
**Location**: Password validation

**Issues**:
- Only minimum length (8 chars)
- No complexity requirements
- No password history
- No common password checking

**Recommendation**:
- Require uppercase, lowercase, number, special char
- Check against common password lists
- Implement password history (prevent reuse)
- Add password strength meter

---

### 🟠 HIGH-9: No Account Lockout
**Severity**: HIGH  
**Location**: Login endpoint

**Issue**: Unlimited login attempts allowed.

**Risk**: Brute force attacks on user accounts.

**Recommendation**:
```python
# Track failed attempts
failed_attempts = await database.login_attempts.find_one({
    "email": email,
    "timestamp": {"$gte": datetime.utcnow() - timedelta(minutes=15)}
})

if failed_attempts and failed_attempts["count"] >= 5:
    raise HTTPException(
        status_code=429,
        detail="Account temporarily locked. Try again in 15 minutes."
    )
```

---

### 🟠 HIGH-10: Super Admin Configuration Risk
**Severity**: HIGH  
**Location**: `backend/app/core/tenant.py:213-222`

**Issue**:
- Super admin based on email only
- No additional verification
- Single point of failure
- No audit trail for super admin actions

**Recommendation**:
- Add MFA for super admins
- Separate super admin role in database
- Enhanced audit logging
- Require approval for sensitive operations

---

### 🟠 HIGH-11: Database Connection Security
**Severity**: HIGH  
**Location**: `backend/app/core/database.py`

**Issues**:
- MongoDB connection string may not use TLS
- No connection pooling limits
- No query timeout
- No connection encryption verification

**Recommendation**:
- Enforce TLS for MongoDB connections
- Add connection pool limits
- Implement query timeouts
- Verify SSL certificates

---

### 🟠 HIGH-12: Frontend Security
**Severity**: HIGH  
**Location**: Frontend code

**Issues**:
- Tokens stored in localStorage (XSS risk)
- No Content Security Policy
- No input sanitization on frontend
- API keys potentially exposed

**Recommendation**:
- Consider httpOnly cookies for tokens
- Implement CSP headers
- Sanitize all user inputs
- Use environment variables for API URLs

---

## MEDIUM Priority Issues

### 🟡 MEDIUM-1: Missing HTTPS Enforcement
- No redirect from HTTP to HTTPS
- No HSTS headers

### 🟡 MEDIUM-2: Insufficient Logging
- No request/response logging
- Limited error context
- No performance metrics

### 🟡 MEDIUM-3: No API Versioning
- Breaking changes affect all clients
- No deprecation strategy

### 🟡 MEDIUM-4: File Upload Security (Future)
- No file upload currently, but if added:
  - Need file type validation
  - Size limits
  - Virus scanning
  - Secure storage

### 🟡 MEDIUM-5: Email Security
- No SPF/DKIM/DMARC verification
- Email content not encrypted
- No email delivery tracking

---

## Security Best Practices Already Implemented ✅

1. ✅ **Password Hashing**: Using bcrypt with salt
2. ✅ **JWT Authentication**: Secure token-based auth
3. ✅ **Multi-Tenancy Isolation**: Institution-based filtering
4. ✅ **Role-Based Access Control**: Proper role checks
5. ✅ **Audit Logging**: Comprehensive action tracking
6. ✅ **Input Validation**: Pydantic models for validation
7. ✅ **Email Enumeration Protection**: In forgot password
8. ✅ **Password Reset Security**: Secure token generation
9. ✅ **Student Approval Workflow**: Prevents unauthorized access

---

## Immediate Action Items

### Priority 1 (This Week)
1. 🔴 Fix error handler to not expose tracebacks in production
2. 🔴 Change default SECRET_KEY to environment variable
3. 🔴 Add rate limiting to authentication endpoints
4. 🔴 Secure CORS configuration
5. 🔴 Remove or secure `/api/dashboard/stats` endpoint

### Priority 2 (Next Week)
6. 🔴 Implement JWT token revocation
7. 🔴 Add ObjectId validation helper
8. 🟠 Add security headers middleware
9. 🟠 Implement account lockout
10. 🟠 Strengthen password policy

### Priority 3 (This Month)
11. 🟠 Add refresh token mechanism
12. 🟠 Enhance audit logging security
13. 🟠 Complete multi-tenancy audit
14. 🟠 Add input sanitization
15. 🟠 Implement session management

---

## Testing Recommendations

### Security Testing
1. **Penetration Testing**: Hire external security firm
2. **Automated Scanning**: OWASP ZAP, Burp Suite
3. **Dependency Scanning**: Check for vulnerable packages
4. **Code Review**: Security-focused code review
5. **Threat Modeling**: Regular threat model updates

### Test Cases
- [ ] Brute force login attempts
- [ ] SQL/NoSQL injection attempts
- [ ] Cross-tenant data access attempts
- [ ] Token manipulation
- [ ] XSS in user inputs
- [ ] CSRF attacks
- [ ] Rate limit bypass attempts

---

## Compliance Considerations

### GDPR/Privacy
- ✅ Audit logging (data access tracking)
- ⚠️ Need: Data export functionality
- ⚠️ Need: Right to deletion
- ⚠️ Need: Privacy policy integration

### SOC 2 / Security Standards
- ⚠️ Need: Security incident response plan
- ⚠️ Need: Regular security audits
- ⚠️ Need: Access control reviews
- ⚠️ Need: Encryption at rest

---

## Risk Matrix

| Threat | Likelihood | Impact | Risk Level | Priority |
|--------|-----------|--------|------------|----------|
| Information Disclosure | High | High | CRITICAL | P1 |
| Weak Secret Key | High | Critical | CRITICAL | P1 |
| No Rate Limiting | High | High | CRITICAL | P1 |
| CORS Misconfiguration | Medium | High | CRITICAL | P1 |
| Public Data Exposure | Medium | Medium | CRITICAL | P1 |
| No Token Revocation | Medium | High | CRITICAL | P1 |
| NoSQL Injection | Low | Critical | CRITICAL | P1 |
| Missing Input Validation | Medium | Medium | HIGH | P2 |
| Session Management | Medium | Medium | HIGH | P2 |
| Audit Logging Gaps | Low | Medium | HIGH | P2 |

---

## Conclusion

The application has a solid security foundation with proper password hashing, multi-tenancy isolation, and role-based access control. However, **7 critical issues** require immediate attention, particularly around error handling, secret management, and rate limiting.

**Estimated Remediation Time**: 
- Critical issues: 1-2 weeks
- High priority: 2-4 weeks
- Medium priority: 1-2 months

**Recommended Next Steps**:
1. Review and prioritize this threat model
2. Create security backlog items
3. Implement Priority 1 fixes immediately
4. Schedule security review meetings
5. Consider security training for team

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/advanced/security/)
- [MongoDB Security Checklist](https://www.mongodb.com/docs/manual/administration/security-checklist/)
