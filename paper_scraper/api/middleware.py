"""API middleware for rate limiting and security."""

from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.requests import Request

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


__all__ = ["limiter", "SlowAPIMiddleware", "get_rate_limit_key"]
