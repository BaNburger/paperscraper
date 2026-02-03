"""API middleware for rate limiting and security."""

from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from paper_scraper.core.config import settings

# Create limiter with Redis backend
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_REQUESTS_PER_MINUTE}/minute"],
    storage_uri=settings.REDIS_URL,
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


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses.

    Implements OWASP recommended security headers:
    - Content-Security-Policy: Prevents XSS and data injection attacks
    - X-Content-Type-Options: Prevents MIME type sniffing
    - X-Frame-Options: Prevents clickjacking
    - X-XSS-Protection: Legacy XSS protection for older browsers
    - Strict-Transport-Security: Enforces HTTPS
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Restricts browser features
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add security headers to response.

        Args:
            request: The incoming request.
            call_next: The next middleware/handler in the chain.

        Returns:
            Response with security headers added.
        """
        response = await call_next(request)

        # Content Security Policy - Adjust based on your frontend needs
        # Relax CSP for Swagger UI docs in debug mode
        is_docs_path = request.url.path in ("/docs", "/redoc", "/openapi.json")

        if settings.DEBUG and is_docs_path:
            # Relaxed CSP for Swagger UI (loads from CDN)
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
                "img-src 'self' data: https:",
                "font-src 'self' https://cdn.jsdelivr.net",
                "connect-src 'self'",
                "frame-ancestors 'self'",
                "base-uri 'self'",
                "form-action 'self'",
            ]
        else:
            # Strict CSP for API responses
            csp_directives = [
                "default-src 'self'",
                "script-src 'self'",
                "style-src 'self' 'unsafe-inline'",
                "img-src 'self' data: https:",
                "font-src 'self'",
                "connect-src 'self'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
            ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Legacy XSS protection (for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS - Force HTTPS (only in production)
        if settings.ENVIRONMENT == "production":
            # max-age=31536000 = 1 year, includeSubDomains for all subdomains
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Restrict browser features/permissions
        permissions = [
            "accelerometer=()",
            "camera=()",
            "geolocation=()",
            "gyroscope=()",
            "magnetometer=()",
            "microphone=()",
            "payment=()",
            "usb=()",
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)

        # Cache control for API responses
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"

        return response


__all__ = ["limiter", "SlowAPIMiddleware", "SecurityHeadersMiddleware", "get_rate_limit_key"]
