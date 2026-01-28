"""
Multi-tenancy middleware and context management.
Provides tenant isolation at the middleware layer.

Tenant Model:
- Institution is the top-level tenant (school/university)
- Users (students, counsellors, admins) belong to an institution
- All data is scoped to an institution
"""
from contextvars import ContextVar
from typing import Optional
from dataclasses import dataclass, field
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt

from app.core.config import settings

# Context variable to store tenant info for the current request
_tenant_context: ContextVar[Optional["TenantContext"]] = ContextVar("tenant_context", default=None)


@dataclass
class TenantContext:
    """
    Holds tenant information for the current request.
    
    Hierarchy:
    - institution_id: Top-level tenant (school/university)
    - user_id: The authenticated user
    - role: User's role within the institution
    """
    user_id: str
    institution_id: str  # The actual tenant identifier
    role: str
    email: str
    full_name: str = ""
    is_authenticated: bool = True
    
    @property
    def tenant_id(self) -> str:
        """Alias for institution_id - the tenant is the institution"""
        return self.institution_id
    
    @property
    def is_student(self) -> bool:
        return self.role == "student"
    
    @property
    def is_counsellor(self) -> bool:
        return self.role == "counsellor"
    
    @property
    def is_admin(self) -> bool:
        return self.role == "admin"
    
    def can_access_student_data(self, student_id: str) -> bool:
        """Check if this user can access a specific student's data"""
        if self.is_admin:
            return True  # Admins can access all data in their institution
        if self.is_counsellor:
            return True  # Counsellors can access all students in their institution
        if self.is_student:
            return self.user_id == student_id  # Students can only access their own data
        return False


def get_tenant_context() -> Optional[TenantContext]:
    """Get the current tenant context from the request"""
    return _tenant_context.get()


def get_required_tenant_context() -> TenantContext:
    """Get tenant context, raise error if not authenticated"""
    ctx = _tenant_context.get()
    if ctx is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return ctx


def set_tenant_context(context: Optional[TenantContext]) -> None:
    """Set the tenant context for the current request"""
    _tenant_context.set(context)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts tenant information from JWT token
    and makes it available throughout the request lifecycle.
    
    This is the FIRST line of defense for multi-tenancy.
    All authenticated requests have tenant context set.
    """
    
    # Paths that don't require authentication
    PUBLIC_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/auth/login",
        "/api/auth/register",
        "/api/dashboard/stats",
        "/api/institutions",  # Public list of institutions for registration
    }
    
    async def dispatch(self, request: Request, call_next):
        import logging
        logger = logging.getLogger(__name__)
        
        # Reset tenant context for each request
        set_tenant_context(None)
        
        # Skip auth for public paths
        path = request.url.path
        if path in self.PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)
        
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                # Decode and validate JWT
                payload = jwt.decode(
                    token, 
                    settings.SECRET_KEY, 
                    algorithms=[settings.ALGORITHM]
                )
                user_id = payload.get("sub")
                
                if user_id:
                    # Fetch user details for tenant context
                    from app.core.database import get_database
                    from bson import ObjectId
                    
                    database = await get_database()
                    user = await database.users.find_one({"_id": ObjectId(user_id)})
                    
                    if user and user.get("is_active", True):
                        # Get institution_id - required for multi-tenancy
                        institution_id = user.get("institution_id")
                        
                        if not institution_id:
                            # User without institution - likely legacy data
                            # For backwards compatibility, use a default
                            institution_id = "default"
                        
                        # Set tenant context for this request
                        context = TenantContext(
                            user_id=str(user["_id"]),
                            institution_id=institution_id,
                            role=user["role"],
                            email=user["email"],
                            full_name=user.get("full_name", ""),
                            is_authenticated=True
                        )
                        set_tenant_context(context)
                        
                        # Add to request state for easy access
                        request.state.tenant = context
                        
                        # Log tenant context extraction
                        logger.debug(
                            f"Tenant context extracted | "
                            f"Institution: {institution_id} | "
                            f"User: {str(user['_id'])} | "
                            f"Role: {user['role']} | "
                            f"Path: {request.url.path}"
                        )
                        
            except JWTError:
                # Invalid token - continue without tenant context
                # Individual endpoints will handle auth requirements
                pass
        
        response = await call_next(request)
        return response


def require_role(*allowed_roles: str):
    """
    Dependency to require specific roles.
    
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(tenant: TenantContext = Depends(require_role("admin"))):
            ...
    """
    def dependency() -> TenantContext:
        ctx = get_required_tenant_context()
        if ctx.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {list(allowed_roles)}"
            )
        return ctx
    return dependency


def require_institution_admin():
    """Dependency to require institution admin role"""
    return require_role("admin")


def require_counsellor_or_admin():
    """Dependency to require counsellor or admin role"""
    return require_role("counsellor", "admin")


def require_student():
    """Dependency to require student role"""
    return require_role("student")


def get_tenant_dependency() -> TenantContext:
    """Simple dependency to get tenant context"""
    return get_required_tenant_context()


def is_super_admin(tenant: TenantContext) -> bool:
    """
    Check if the current user is a super admin.
    Super admins are identified by their email being in the SUPER_ADMIN_EMAILS config.
    """
    return is_email_super_admin(tenant.email)


def is_email_super_admin(email: str) -> bool:
    """Check if an email is a super admin (in SUPER_ADMIN_EMAILS config)."""
    if not email or not settings.SUPER_ADMIN_EMAILS:
        return False
    super_admin_emails = [e.strip().lower() for e in settings.SUPER_ADMIN_EMAILS.split(",") if e.strip()]
    return email.strip().lower() in super_admin_emails
