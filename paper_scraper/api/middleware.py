"""API middleware for rate limiting and security."""

from collections.abc import Awaitable, Callable

from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from paper_scraper.core.config import settings
from paper_scraper.core.security import decode_token, validate_token_type

# Rate limiter with Redis backend
# When RATE_LIMIT_ENABLED is False, all requests are exempt (useful for E2E testing)
limiter = Limiter(
    key_func=lambda request: get_rate_limit_key(request),
    default_limits=[f"{settings.RATE_LIMIT_REQUESTS_PER_MINUTE}/minute"],
    storage_uri=settings.REDIS_URL,
    enabled=settings.RATE_LIMIT_ENABLED,
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
    "style-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
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

    authorization = request.headers.get("Authorization")
    token: str | None = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    elif request.cookies.get(settings.AUTH_ACCESS_COOKIE_NAME):
        token = request.cookies.get(settings.AUTH_ACCESS_COOKIE_NAME)

    if token:
        payload = decode_token(token)
        if payload and validate_token_type(payload, "access") and payload.get("sub"):
            return f"user:{payload['sub']}"

    return get_remote_address(request)


def _build_csp_header(directives: dict[str, str]) -> str:
    """Build CSP header string from directives dictionary."""
    return "; ".join(f"{key} {value}" for key, value in directives.items())


def _build_permissions_header() -> str:
    """Build Permissions-Policy header string."""
    return ", ".join(f"{perm}=()" for perm in _DISABLED_PERMISSIONS)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add OWASP-recommended security headers to all responses."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
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
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        headers["Permissions-Policy"] = _build_permissions_header()

        # HSTS only in production
        if settings.is_production:
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Cache control for API responses
        if request.url.path.startswith("/api/"):
            headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            headers["Pragma"] = "no-cache"

        return response


class CSRFMiddleware(BaseHTTPMiddleware):
    """Enforce CSRF header validation for cookie-authenticated mutating requests."""

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
    EXEMPT_PATHS = {
        "/health",
        "/health/live",
        "/health/ready",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
        "/api/v1/auth/verify-email",
        "/api/v1/auth/resend-verification",
        "/api/v1/auth/accept-invite",
    }

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method in self.SAFE_METHODS:
            return await call_next(request)

        path = request.url.path
        if not path.startswith(settings.API_V1_PREFIX) or path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Bearer-token requests are treated as non-browser clients.
        authorization = request.headers.get("Authorization")
        if authorization and authorization.lower().startswith("bearer "):
            return await call_next(request)

        access_cookie = request.cookies.get(settings.AUTH_ACCESS_COOKIE_NAME)
        refresh_cookie = request.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)
        if not access_cookie and not refresh_cookie:
            return await call_next(request)

        csrf_cookie = request.cookies.get(settings.AUTH_CSRF_COOKIE_NAME)
        csrf_header = request.headers.get(settings.CSRF_HEADER_NAME)
        if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
            return Response(
                content='{"error":"csrf_validation_failed","message":"Missing or invalid CSRF token"}',
                status_code=403,
                media_type="application/json",
            )

        return await call_next(request)


__all__ = [
    "limiter",
    "SlowAPIMiddleware",
    "SecurityHeadersMiddleware",
    "CSRFMiddleware",
    "get_rate_limit_key",
]
