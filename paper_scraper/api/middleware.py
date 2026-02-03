"""API middleware for rate limiting and security."""

from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from paper_scraper.core.config import settings

# Rate limiter with Redis backend
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_REQUESTS_PER_MINUTE}/minute"],
    storage_uri=settings.REDIS_URL,
)

# Content Security Policy directives
_CSP_BASE = {
    "default-src": "'self'",
    "style-src": "'self' 'unsafe-inline'",
    "img-src": "'self' data: https:",
    "connect-src": "'self'",
    "base-uri": "'self'",
    "form-action": "'self'",
}

_CSP_STRICT = {
    **_CSP_BASE,
    "script-src": "'self'",
    "font-src": "'self'",
    "frame-ancestors": "'none'",
}

_CSP_DOCS = {
    **_CSP_BASE,
    "script-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
    "font-src": "'self' https://cdn.jsdelivr.net",
    "frame-ancestors": "'self'",
}

# Browser permissions to disable
_DISABLED_PERMISSIONS = (
    "accelerometer",
    "camera",
    "geolocation",
    "gyroscope",
    "magnetometer",
    "microphone",
    "payment",
    "usb",
)


def get_rate_limit_key(request: Request) -> str:
    """Get rate limit key based on user or IP.

    If authenticated, uses user ID for per-user limits.
    Otherwise, falls back to IP address.

    Args:
        request: The incoming request.

    Returns:
        Rate limit key string.
    """
    # If authenticated, use user ID; otherwise IP
    if hasattr(request.state, "user_id") and request.state.user_id:
        return f"user:{request.state.user_id}"
    return get_remote_address(request)


def _build_csp_header(directives: dict[str, str]) -> str:
    """Build CSP header string from directives dictionary."""
    return "; ".join(f"{key} {value}" for key, value in directives.items())


def _build_permissions_header() -> str:
    """Build Permissions-Policy header string."""
    return ", ".join(f"{perm}=()" for perm in _DISABLED_PERMISSIONS)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add OWASP-recommended security headers to all responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        headers = response.headers

        # Content Security Policy (relaxed for Swagger UI in debug mode)
        is_docs_path = request.url.path in ("/docs", "/redoc", "/openapi.json")
        csp = _CSP_DOCS if settings.DEBUG and is_docs_path else _CSP_STRICT
        headers["Content-Security-Policy"] = _build_csp_header(csp)

        # Security headers
        headers["X-Content-Type-Options"] = "nosniff"
        headers["X-Frame-Options"] = "DENY"
        headers["X-XSS-Protection"] = "1; mode=block"
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        headers["Permissions-Policy"] = _build_permissions_header()

        # HSTS only in production
        if settings.is_production:
            headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Cache control for API responses
        if request.url.path.startswith("/api/"):
            headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            headers["Pragma"] = "no-cache"

        return response


__all__ = ["limiter", "SlowAPIMiddleware", "SecurityHeadersMiddleware", "get_rate_limit_key"]
