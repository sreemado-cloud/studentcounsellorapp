"""
Rate limiting middleware for API endpoints.
Uses slowapi to prevent brute force attacks and DoS.
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Rate limit configurations
# Login: 5 attempts per minute per IP
LOGIN_RATE_LIMIT = "5/minute"

# Registration: 3 attempts per hour per IP
REGISTER_RATE_LIMIT = "3/hour"

# Forgot password: 3 attempts per hour per IP
FORGOT_PASSWORD_RATE_LIMIT = "3/hour"

# Reset password with token: 5 attempts per hour per IP
RESET_PASSWORD_RATE_LIMIT = "5/hour"

# General API: 100 requests per minute per IP
GENERAL_API_RATE_LIMIT = "100/minute"


def get_rate_limit_handler(app):
    """Register rate limit exception handler with FastAPI app"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    return app
