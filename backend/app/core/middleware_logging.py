"""
Middleware for logging all requests and responses.
This provides visibility into the middle layer (API layer) operations.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import logging
import time
from typing import Callable

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all incoming requests and outgoing responses.
    Provides visibility into the middle layer operations.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timer
        start_time = time.time()
        
        # Extract request details
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else ""
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Check if request has tenant context (from TenantMiddleware)
        tenant_info = ""
        if hasattr(request.state, "tenant") and request.state.tenant:
            tenant = request.state.tenant
            tenant_info = f" | Tenant: {tenant.institution_id} | User: {tenant.user_id} | Role: {tenant.role}"
        
        # Log incoming request
        logger.info(
            f"→ {method} {path}{'?' + query_params if query_params else ''} | "
            f"IP: {client_ip}{tenant_info} | "
            f"User-Agent: {user_agent[:50]}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Extract response details
            status_code = response.status_code
            response_size = response.headers.get("content-length", "unknown")
            
            # Log outgoing response
            logger.info(
                f"← {method} {path} | "
                f"Status: {status_code} | "
                f"Time: {process_time:.3f}s | "
                f"Size: {response_size}"
            )
            
            # Add processing time to response headers (for debugging)
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Calculate processing time even for errors
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"✗ {method} {path} | "
                f"Error: {str(e)} | "
                f"Time: {process_time:.3f}s"
            )
            raise
