# How to View Middle Layer Logs

## What is the Middle Layer?

In your Student Counsellor application architecture:

```
Frontend (React) → Middle Layer (FastAPI API) → Database (MongoDB)
```

**The FastAPI backend IS your middle layer.** It includes:
- **API endpoints** (authentication, users, appointments, etc.)
- **TenantMiddleware** (multi-tenancy isolation)
- **CORS Middleware** (cross-origin requests)
- **Rate Limiting** (API protection)
- **Request/Response Logging** (all API calls)

---

## Viewing Middle Layer Logs

### 1. Where to See the Logs

**All middle layer logs appear in the terminal where you started the FastAPI server.**

Look for the terminal showing:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### 2. What You'll See

With the logging middleware enabled, you'll see detailed logs for every API request:

#### Request Logs (Incoming)
```
2025-01-25 10:30:45 - app.core.middleware_logging - INFO - → POST /api/auth/forgot-password | IP: 127.0.0.1 | Tenant: inst_123 | User: user_456 | Role: student | User-Agent: Mozilla/5.0...
```

#### Response Logs (Outgoing)
```
2025-01-25 10:30:46 - app.core.middleware_logging - INFO - ← POST /api/auth/forgot-password | Status: 200 | Time: 0.234s | Size: 156
```

#### Tenant Context Logs
```
2025-01-25 10:30:45 - app.core.tenant - DEBUG - Tenant context extracted | Institution: inst_123 | User: user_456 | Role: student | Path: /api/auth/forgot-password
```

#### Error Logs
```
2025-01-25 10:30:45 - app.core.middleware_logging - ERROR - ✗ POST /api/auth/forgot-password | Error: Database connection failed | Time: 5.123s
```

---

### 3. Log Format Explained

#### Request Log Format:
```
→ METHOD PATH | IP: xxx | Tenant: xxx | User: xxx | Role: xxx | User-Agent: xxx
```

**Components:**
- `→` = Incoming request
- `METHOD` = HTTP method (GET, POST, PUT, DELETE)
- `PATH` = API endpoint path
- `IP` = Client IP address
- `Tenant` = Institution ID (if authenticated)
- `User` = User ID (if authenticated)
- `Role` = User role (student/counsellor/admin)
- `User-Agent` = Browser/client information

#### Response Log Format:
```
← METHOD PATH | Status: XXX | Time: X.XXXs | Size: XXX
```

**Components:**
- `←` = Outgoing response
- `Status` = HTTP status code (200, 404, 500, etc.)
- `Time` = Processing time in seconds
- `Size` = Response size in bytes

---

### 4. Enable More Detailed Logging

#### Option A: Enable DEBUG Logging for Tenant Middleware

Edit `backend/app/main.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
```

This will show:
- Tenant context extraction details
- JWT token validation
- Database queries (if enabled)

#### Option B: Enable Uvicorn Access Logs

The FastAPI server (Uvicorn) also logs requests. You'll see:

```
INFO:     127.0.0.1:xxxxx - "POST /api/auth/forgot-password HTTP/1.1" 200 OK
```

These are automatically enabled and appear in the same terminal.

---

### 5. Filtering Logs

#### View Only Middle Layer Logs

You can filter logs by module:

**Request/Response Logs:**
- Look for lines containing `app.core.middleware_logging`

**Tenant Middleware Logs:**
- Look for lines containing `app.core.tenant`

**API Endpoint Logs:**
- Look for lines containing `app.api.`

**Rate Limiting Logs:**
- Look for lines containing `slowapi` or status code `429`

---

### 6. Example: Complete Request Flow

When a user submits the forgot password form, you'll see:

```
# 1. Request arrives at middleware
2025-01-25 10:30:45 - app.core.middleware_logging - INFO - → POST /api/auth/forgot-password | IP: 127.0.0.1 | User-Agent: Mozilla/5.0...

# 2. CORS middleware processes (no log, but happens)

# 3. Tenant middleware processes (if authenticated)
2025-01-25 10:30:45 - app.core.tenant - DEBUG - Tenant context extracted | Institution: inst_123 | User: user_456 | Role: student

# 4. API endpoint processes
2025-01-25 10:30:45 - app.api.auth - INFO - Forgot password request received for: user@example.com
2025-01-25 10:30:45 - app.api.auth - INFO - Reset token stored for user: user@example.com

# 5. Response sent
2025-01-25 10:30:46 - app.core.middleware_logging - INFO - ← POST /api/auth/forgot-password | Status: 200 | Time: 0.234s | Size: 156
```

---

### 7. Troubleshooting

#### Issue: "No middleware logs appearing"
- **Check**: Is the backend server running?
- **Check**: Is `RequestLoggingMiddleware` added in `main.py`?
- **Solution**: Restart the backend server

#### Issue: "Too many logs"
- **Solution**: Change log level from `DEBUG` to `INFO` in `main.py`

#### Issue: "Can't see tenant information"
- **Check**: Is the user authenticated? (Tenant info only appears for authenticated requests)
- **Check**: Is `DEBUG` logging enabled? (Tenant extraction logs are DEBUG level)

---

### 8. Logging Components Summary

| Component | Log Module | What It Logs |
|-----------|-----------|--------------|
| **Request/Response** | `app.core.middleware_logging` | All API requests and responses |
| **Tenant Isolation** | `app.core.tenant` | Tenant context extraction |
| **Rate Limiting** | `slowapi` | Rate limit violations (429 errors) |
| **API Endpoints** | `app.api.*` | Business logic operations |
| **Errors** | All modules | Error messages and stack traces |
| **Uvicorn** | `uvicorn` | HTTP access logs |

---

### 9. Quick Test

Test the logging by making a request:

```powershell
# Test health endpoint
Invoke-RestMethod -Uri "http://localhost:8000/health"
```

You should see in the backend terminal:
```
→ GET /health | IP: 127.0.0.1 | User-Agent: ...
← GET /health | Status: 200 | Time: 0.001s | Size: 45
```

---

## Summary

1. **Middle Layer = FastAPI Backend** (all API operations)
2. **Logs appear in the terminal** where uvicorn is running
3. **RequestLoggingMiddleware** logs all requests/responses
4. **TenantMiddleware** logs tenant context extraction
5. **All middleware logs** appear together in the same terminal

**The middle layer logs show you:**
- What requests are coming in
- Which tenant/user is making the request
- How long each request takes
- What responses are being sent
- Any errors that occur

This gives you complete visibility into your API layer operations!
