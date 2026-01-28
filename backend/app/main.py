from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import traceback
import logging

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.core.tenant import TenantMiddleware, get_tenant_context
from app.core.audit import create_audit_indexes
from app.core.rate_limit import get_rate_limit_handler
from app.core.middleware_logging import RequestLoggingMiddleware
from app.api import auth, users, appointments, messages, notes, institutions, admin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    await create_audit_indexes()
    # Debug: verify set-password route is in OpenAPI
    try:
        openapi = app.openapi()
        paths = openapi.get("paths", {})
        sp = "/api/admin/users/{user_id}/set-password"
        if sp in paths:
            logger.info("set-password route IS in OpenAPI: %s", list(paths[sp].keys()))
        else:
            logger.warning("set-password route NOT in OpenAPI. Sample paths: %s", list(paths.keys())[:15])
    except Exception as e:
        logger.warning("Could not check OpenAPI for set-password: %s", e)
    yield
    # Shutdown
    await close_mongo_connection()


app = FastAPI(
    title=settings.APP_NAME,
    description="A multi-tenant student counselling platform API with institution-based isolation",
    version="2.0.0",
    lifespan=lifespan
)

# Initialize rate limiting
app = get_rate_limit_handler(app)

# CORS middleware for React frontend
# Use environment variable for production origins
allowed_origins = []
if settings.ALLOWED_ORIGINS:
    origins_str = settings.ALLOWED_ORIGINS.strip()
    if origins_str == "*":
        # Allow all origins (use with caution in production)
        allowed_origins = ["*"]
    else:
        allowed_origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]
else:
    # Default to localhost for development
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

# Request/Response Logging Middleware - Logs all API requests/responses
# This should be added FIRST to capture all requests
app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# Tenant isolation middleware - extracts tenant context from JWT
# This is the FIRST layer of multi-tenancy defense
app.add_middleware(TenantMiddleware)

# Exception handler to log errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Always log full error details server-side
    error_msg = f"Error: {str(exc)}\n{traceback.format_exc()}"
    logger.error(error_msg, exc_info=True)
    
    # Only expose detailed errors in DEBUG mode
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "traceback": traceback.format_exc()}
        )
    else:
        # In production, return generic error message
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred. Please contact support."}
        )

# Include routers
app.include_router(institutions.router)  # Institution management
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(appointments.router)
app.include_router(messages.router)
app.include_router(notes.router)
app.include_router(admin.router)  # Admin panel for user management


@app.get("/")
async def root():
    return {
        "message": "Welcome to Student Counsellor API",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.APP_NAME}


@app.get("/api/health")
async def api_health_check():
    """Health check endpoint accessible via /api prefix (for ALB routing)"""
    return {"status": "healthy", "service": settings.APP_NAME, "version": "2.0.0"}


@app.get("/api/dashboard/stats")
async def get_dashboard_stats(
    request: Request,
    current_user: dict = Depends(auth.get_current_active_user)
):
    """
    Get dashboard statistics for the authenticated user's institution.
    Requires authentication and scopes data to user's institution.
    """
    from app.core.database import get_database
    from app.core.tenant import get_tenant_context
    
    database = await get_database()
    tenant = get_tenant_context()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Scope statistics to user's institution
    stats = {
        "total_students": await database.users.count_documents({
            "role": "student",
            "institution_id": tenant.institution_id,
            "is_active": True
        }),
        "total_counsellors": await database.users.count_documents({
            "role": "counsellor",
            "institution_id": tenant.institution_id,
            "is_active": True
        }),
        "total_appointments": await database.appointments.count_documents({
            "institution_id": tenant.institution_id
        }),
        "pending_appointments": await database.appointments.count_documents({
            "institution_id": tenant.institution_id,
            "status": "pending"
        }),
    }
    
    return stats
