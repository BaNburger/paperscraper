"""Token blacklist service for JWT invalidation.

Uses Redis to store blacklisted JWT tokens with automatic expiration.
Tokens are blacklisted on:
- Logout
- Password change
- Password reset
- User deactivation
"""

from datetime import datetime, timezone

from paper_scraper.core.config import settings
from paper_scraper.core.logging import get_logger
from paper_scraper.core.redis_base import RedisService

logger = get_logger(__name__)

# Redis key prefixes
BLACKLIST_PREFIX = "token:blacklist:"
USER_INVALIDATION_PREFIX = "user:tokens_invalid_before:"


class TokenBlacklist(RedisService):
    """Service for managing JWT token blacklist in Redis."""

    async def blacklist_token(self, jti: str, exp: datetime) -> bool:
        """Add a specific token to the blacklist.

        Args:
            jti: JWT ID (unique token identifier).
            exp: Token expiration datetime.

        Returns:
            True if token was blacklisted, False on error.
        """
        try:
            redis = await self._get_redis()
            key = f"{BLACKLIST_PREFIX}{jti}"

            # Calculate TTL from expiration time
            now = datetime.now(timezone.utc)
            ttl = int((exp - now).total_seconds())

            if ttl <= 0:
                # Token already expired, no need to blacklist
                return True

            # Store with expiration matching token expiry
            await redis.setex(key, ttl, "1")
            logger.debug(f"Token blacklisted: {jti[:8]}... (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False

    async def is_token_blacklisted(self, jti: str) -> bool:
        """Check if a specific token is blacklisted.

        Args:
            jti: JWT ID to check.

        Returns:
            True if token is blacklisted, False otherwise.
        """
        try:
            redis = await self._get_redis()
            key = f"{BLACKLIST_PREFIX}{jti}"
            result = await redis.exists(key)
            return bool(result)

        except Exception as e:
            logger.error(f"Failed to check token blacklist: {e}")
            # On Redis failure, fail open to avoid blocking all users
            # Log this prominently for monitoring
            return False

    async def invalidate_user_tokens(self, user_id: str) -> bool:
        """Invalidate all tokens for a user issued before now.

        This is more efficient than blacklisting each token individually.
        Used when:
        - User changes password
        - User is deactivated
        - Security incident occurs

        Args:
            user_id: User UUID string.

        Returns:
            True if invalidation timestamp was set, False on error.
        """
        try:
            redis = await self._get_redis()
            key = f"{USER_INVALIDATION_PREFIX}{user_id}"

            # Store current timestamp - all tokens issued before this are invalid
            timestamp = int(datetime.now(timezone.utc).timestamp())

            # Keep this key for the maximum token lifetime (refresh token duration)
            ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
            await redis.setex(key, ttl, str(timestamp))

            logger.info(f"Invalidated all tokens for user: {user_id[:8]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to invalidate user tokens: {e}")
            return False

    async def is_token_invalid_for_user(
        self, user_id: str, issued_at: int
    ) -> bool:
        """Check if a token was issued before the user's invalidation timestamp.

        Args:
            user_id: User UUID string.
            issued_at: Token's 'iat' (issued at) timestamp.

        Returns:
            True if token should be rejected, False if valid.
        """
        try:
            redis = await self._get_redis()
            key = f"{USER_INVALIDATION_PREFIX}{user_id}"

            invalid_before = await redis.get(key)
            if invalid_before is None:
                # No invalidation set, token is valid
                return False

            # If token was issued before invalidation timestamp, reject it
            return issued_at < int(invalid_before)

        except Exception as e:
            logger.error(f"Failed to check user token invalidation: {e}")
            # On Redis failure, fail open
            return False


# Singleton instance
token_blacklist = TokenBlacklist()
