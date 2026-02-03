"""Base class for Redis-backed services.

Provides common Redis connection management for services that need
to interact with Redis, such as token blacklist and account lockout.
"""

from typing import TYPE_CHECKING

import redis.asyncio as aioredis

from paper_scraper.core.config import settings

if TYPE_CHECKING:
    from redis.asyncio import Redis


class RedisService:
    """Base class providing Redis connection management."""

    def __init__(self) -> None:
        """Initialize Redis service."""
        self._redis: "Redis | None" = None

    async def _get_redis(self) -> "Redis":
        """Get or create Redis connection.

        Returns:
            Redis client instance.
        """
        if self._redis is None:
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
        return self._redis

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
