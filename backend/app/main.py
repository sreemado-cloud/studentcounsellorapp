import asyncio
import traceback
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
    # Startup: init DB in background so /health is up immediately; API waits for DB ready
    async def init_db():
        try:
            await connect_to_mongo()
            await create_audit_indexes()
        except Exception as e:
            logger.error("DB init failed: %s", e, exc_info=True)

    asyncio.create_task(init_db())

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

# CORS middleware for React frontend (C5: no * in production)
allowed_origins: list[str] = []
if settings.ALLOWED_ORIGINS:
    origins_str = settings.ALLOWED_ORIGINS.strip()
    if origins_str == "*":
        if settings.DEBUG:
            allowed_origins = ["*"]
        else:
            logger.warning(
                "ALLOWED_ORIGINS=* is disabled in production. Set explicit origins (e.g. https://your-app.example.com)."
            )
            allowed_origins = []
    else:
        allowed_origins = [o.strip() for o in origins_str.split(",") if o.strip()]
else:
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
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
