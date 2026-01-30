# Threat Model & Security Analysis

## Student Counsellor SaaS Platform

**Version**: 2.1.0  
**Last Updated**: January 2026  
**Status**: Security Review

---

## 1. Overview

The Student Counsellor platform is a **multi-tenant** web application for universities. Students, counsellors, and admins interact within institution boundaries. Data isolation is enforced by `institution_id` and role-based access control (RBAC).

**Scope**: Frontend (React), Backend (FastAPI), MongoDB, Docker/K8s deployment.

---

## 2. Architecture & Trust Boundaries

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  UNTRUSTED                                                                   │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                    │
│  │   Student   │     │ Counsellor  │     │    Admin    │  (Browser)          │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘                    │
└─────────┼───────────────────┼───────────────────┼────────────────────────────┘
          │                   │                   │
          │     HTTPS (or HTTP in dev)            │
          ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  TRUST BOUNDARY 1: Edge / Reverse Proxy (Nginx / ALB)                        │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Frontend (React, Nginx)  │  Backend (FastAPI)                               │
│  - Static assets, SPA     │  - JWT validation, TenantMiddleware              │
│  - Token in localStorage  │  - RBAC, institution_id filtering                │
└──────────────────────────┼──────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  TRUST BOUNDARY 2: Database                                                  │
│  MongoDB (row-level or DB-per-tenant isolation)                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Trust boundaries**:
- **Browser ↔ Frontend/Backend**: All user input is untrusted.
- **Backend ↔ MongoDB**: Backend is trusted; DB access is mediated only via the API.

---

## 3. Assets

| Asset | Description | Sensitivity |
|-------|-------------|-------------|
| User credentials | Passwords (hashed), JWT tokens | Critical |
| PII | Names, emails, phones, grades, majors, bio | High |
| Counselling data | Messages, notes, appointments | High |
| Institution data | Settings, user lists, stats | Medium |
| Audit logs | Who did what, when | Medium |
| Configuration | SECRET_KEY, MONGODB_URL, SMTP credentials | Critical |

---

## 4. Threat Actors

| Actor | Goal | Capability |
|-------|------|------------|
| **External attacker** | Steal data, disrupt service, impersonate users | Network access, custom tools |
| **Malicious user (same tenant)** | Access other users’ data, elevate privileges | Valid account, same institution |
| **Malicious user (other tenant)** | Cross-tenant data access | Valid account, different institution |
| **Insider (admin/counsellor)** | Overread data, misuse admin functions | Elevated access within tenant |
| **Super admin** | Cross-tenant abuse, reassign users | Full platform access |

---

## 5. Data Flow Summary

- **Login**: Email + password → Backend → JWT stored in `localStorage`; later sent as `Authorization: Bearer <token>`.
- **API calls**: Frontend sends JWT; TenantMiddleware extracts `user_id`, `institution_id`, `role`; endpoints filter by tenant and role.
- **Messages / Notes / Appointments**: Created and queried with `institution_id` and role-specific filters (e.g. student_id, assigned_counsellor_id).

---

## 6. STRIDE Threat Summary

| STRIDE | Threat | Mitigation / Gap |
|--------|--------|-------------------|
| **S**poofing | Forge JWT, impersonate user | JWT + SECRET_KEY; ensure strong key in prod. **Gap**: Token in `localStorage` (XSS risk). |
| **T**ampering | Modify requests, alter DB | Validation, RBAC, tenant filters. **Gap**: No systematic ObjectId validation; possible info leak via errors. |
| **R**epudiation | Deny actions | Audit logging. **Gap**: Sensitive data in logs; retention not enforced. |
| **I**nformation disclosure | Leak PII, errors, config | Error handler hides tracebacks in prod. **Gap**: `X-Process-Time` header; no CSP. |
| **D**enial of service | Exhaust resources, brute force | Rate limiting on register/reset-with-token. **Gap**: Login and forgot-password not (or no longer) limited. |
| **E**levation of privilege | Cross-tenant, role abuse | Tenant + RBAC checks. **Gap**: Need full tenant isolation audit. |

---

## 7. Current Security State (What’s Implemented)

### 7.1 Authentication & Secrets
- **Password hashing**: bcrypt with salt.
- **JWT**: Access tokens with `sub`, `exp`; validation via `get_current_user` / `get_current_active_user`.
- **SECRET_KEY**: Must be set via env in production; default rejected when `DEBUG=False`.
- **Token storage**: Frontend uses `localStorage` (XSS risk if frontend is compromised).

### 7.2 Authorization & Multi-Tenancy
- **RBAC**: Student, counsellor, admin, super-admin; endpoints enforce role and ownership.
- **Tenant isolation**: `TenantMiddleware` sets `institution_id`; queries filter by it (row-level or DB-per-tenant).
- **Student–counsellor**: Students message only assigned counsellor; counsellors see only assigned students.
- **Dashboard stats**: `/api/dashboard/stats` requires auth and scopes data to user’s institution.

### 7.3 API & Input
- **CORS**: Configurable via `ALLOWED_ORIGINS`; methods/headers restricted (no wildcard).
- **Rate limiting**: slowapi used for **register** (3/hour) and **reset-password-with-token** (5/hour).
- **Error handling**: In production, generic 500 response; tracebacks only when `DEBUG=True`.
- **Request logging**: Method, path, IP, tenant, user-agent, status, duration.

### 7.4 Infrastructure
- **Nginx**: `X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`.
- **Docker**: Backend, frontend, MongoDB; `.env` for config (secrets in env files).

---

## 8. Security Gaps & Findings

### 8.1 Critical

| ID | Finding | Location | Status |
|----|---------|----------|--------|
| **C1** | **Login not rate limited** | `auth.py` `/login` | **Fixed:** `@limiter.limit(LOGIN_RATE_LIMIT)` added. |
| **C2** | **Forgot-password rate limit disabled** | `auth.py` `/forgot-password` | **Fixed:** `@limiter.limit(FORGOT_PASSWORD_RATE_LIMIT)` re-enabled. |
| **C3** | **No JWT revocation** | `security.py`, auth flow | **Fixed:** `token_sessions` allowlist; revoke on logout, password change, set-password, deactivate. |
| **C4** | **ObjectId used without validation** | `admin.py`, `messages.py`, etc. | **Fixed:** `validate_object_id()` in `core.validators`; used for all user-controlled IDs. |
| **C5** | **CORS `*` in production** | k8s `configmap`, `main.py` | **Fixed:** `*` disabled when `DEBUG=false`; configmap uses explicit-origin placeholder. |
| **C6** | **Default / weak secrets in Docker** | `docker-compose`, `.env` | **Fixed:** No overrides in compose; `env.example` and `MONGO_*` required via root `.env`. |

### 8.2 High

| ID | Finding | Location | Recommendation |
|----|---------|----------|----------------|
| **H1** | **Token in localStorage** | `AuthContext.tsx`, `api.ts` | Prefer httpOnly cookies for tokens; or document XSS mitigations and CSP. |
| **H2** | **No security headers on API** | FastAPI app | Add middleware: `X-Content-Type-Options`, `X-Frame-Options`, CSP, HSTS (when TLS). |
| **H3** | **No account lockout** | Login | Lock after N failed attempts (e.g. 5) per account; cool-down (e.g. 15 min). |
| **H4** | **Weak password policy** | Registration, reset | Enforce complexity (length, upper/lower/digit/symbol) and optional check against common lists. |
| **H5** | **Password reset token lifetime** | `auth.py` | Consider shortening from 1 hour (e.g. 15–30 min); ensure one-time use. |
| **H6** | **Super admin by email only** | `tenant.py` | Add MFA for super admins; restrict super-admin actions; audit all such actions. |
| **H7** | **Sensitive data in logs** | `middleware_logging.py`, audit | Avoid logging tokens, passwords, or full PII; sanitize before log. |

### 8.3 Medium

| ID | Finding | Location | Recommendation |
|----|---------|----------|----------------|
| **M1** | **`X-Process-Time` header** | `middleware_logging.py` | Remove in production or restrict to debug. |
| **M2** | **No refresh tokens** | Auth | Implement refresh tokens; shorter-lived access tokens. |
| **M3** | **Email enumeration** | Login, register | Use constant-time comparison; same message for invalid email/password; consider delaying response. |
| **M4** | **MongoDB TLS** | `database.py`, connection | Enforce TLS for Mongo in production. |
| **M5** | **No API versioning** | Routers | Version API (e.g. `/api/v1/`) for safer changes. |

### 8.4 Low / Informational

| ID | Finding | Recommendation |
|----|---------|----------------|
| **L1** | **OpenAPI exposes structure** | Disable `/docs` in production or protect them. |
| **L2** | **Health checks public** | Prefer minimal info; optional auth for detailed health. |

---

## 9. Risk Matrix

| ID | Threat | Likelihood | Impact | Risk |
|----|--------|------------|--------|------|
| C1 | Login brute force | High | High | **Critical** |
| C2 | Forgot-password abuse | High | Medium | **Critical** |
| C3 | Stolen token usable until expiry | Medium | High | **Critical** |
| C4 | ObjectId errors / injection | Medium | High | **Critical** |
| C5 | CORS misuse | Medium | High | **Critical** |
| C6 | Default secrets in prod | Low | Critical | **Critical** |
| H1 | XSS → token theft | Medium | High | **High** |
| H2 | Clickjacking, XSS, etc. | Medium | Medium | **High** |
| H3 | Account lockout bypass | High | Medium | **High** |
| H4 | Weak passwords | High | Medium | **High** |
| H5 | Reset token abuse | Medium | Medium | **High** |
| H6 | Super admin abuse | Low | High | **High** |
| H7 | Log leakage | Medium | Medium | **High** |

---

## 10. Recommended Action Plan

### Phase 1 (Immediate)
1. **C1, C2**: Rate limit login and re-enable forgot-password rate limit.
2. **C5**: Restrict CORS to explicit origins in production.
3. **C6**: Remove default secrets from Docker/env examples; use secrets management for prod.
4. **C4**: Introduce `validate_object_id()` and use it for all relevant path/query params.

### Phase 2 (Short-term)
5. **C3**: Design and implement JWT revocation (blacklist or equivalent).
6. **H2**: Add security headers middleware.
7. **H3**: Implement account lockout.
8. **H4**: Tighten password policy.

### Phase 3 (Medium-term)
9. **H1**: Move tokens to httpOnly cookies or harden XSS + CSP.
10. **H6**: Harden super-admin (MFA, audit).
11. **H7**: Sanitize logging.
12. **M2, M4, M5**: Refresh tokens, Mongo TLS, API versioning.

---

## 11. Testing & Validation

- **Authentication**: Brute force login, forgot-password abuse, token reuse after logout.
- **Authorization**: Cross-tenant access, role escalation, student → other counsellor.
- **Input**: Invalid ObjectIds, oversized inputs, NoSQL injection patterns.
- **Headers**: CORS, CSP, HSTS, X-Frame-Options.
- **Secrets**: No default keys or passwords in prod images or config.

---

## 12. References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [MongoDB Security Checklist](https://www.mongodb.com/docs/manual/administration/security-checklist/)
