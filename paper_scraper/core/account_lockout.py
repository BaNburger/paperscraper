"""Account lockout service for brute force protection.

Uses Redis to track failed login attempts and lock accounts after
multiple failures. This approach is database-agnostic and works
across distributed systems.
"""

from datetime import UTC, datetime

from paper_scraper.core.logging import get_logger
from paper_scraper.core.redis_base import RedisService

logger = get_logger(__name__)

# Redis key prefixes
FAILED_ATTEMPTS_PREFIX = "login:failed:"
LOCKOUT_PREFIX = "login:lockout:"

# Lockout configuration
MAX_FAILED_ATTEMPTS = 5  # Lock after 5 failed attempts
LOCKOUT_DURATION_MINUTES = 15  # Lock account for 15 minutes
FAILED_ATTEMPT_WINDOW_MINUTES = 15  # Reset counter after 15 minutes of inactivity


class AccountLockout(RedisService):
    """Service for tracking failed login attempts and account lockouts."""

    def _get_failed_key(self, email: str) -> str:
        """Get Redis key for failed attempts counter.

        Args:
            email: User email (lowercased).

        Returns:
            Redis key string.
        """
        return f"{FAILED_ATTEMPTS_PREFIX}{email.lower()}"

    def _get_lockout_key(self, email: str) -> str:
        """Get Redis key for lockout status.

        Args:
            email: User email (lowercased).

        Returns:
            Redis key string.
        """
        return f"{LOCKOUT_PREFIX}{email.lower()}"

    async def is_locked_out(self, email: str) -> bool:
        """Check if an account is locked out.

        Args:
            email: User email to check.

        Returns:
            True if account is locked out, False otherwise.
        """
        try:
            redis = await self._get_redis()
            lockout_key = self._get_lockout_key(email)
            result = await redis.exists(lockout_key)
            return bool(result)

        except Exception as e:
            logger.error(f"Failed to check lockout status: {e}")
            # On Redis failure, fail open to avoid blocking legitimate users
            return False

    async def get_lockout_remaining_seconds(self, email: str) -> int:
        """Get remaining lockout time in seconds.

        Args:
            email: User email to check.

        Returns:
            Remaining seconds, or 0 if not locked out.
        """
        try:
            redis = await self._get_redis()
            lockout_key = self._get_lockout_key(email)
            ttl = await redis.ttl(lockout_key)
            return max(0, ttl)

        except Exception as e:
            logger.error(f"Failed to get lockout TTL: {e}")
            return 0

    async def record_failed_attempt(self, email: str) -> tuple[int, bool]:
        """Record a failed login attempt.

        Args:
            email: User email that failed login.

        Returns:
            Tuple of (current_attempt_count, is_now_locked_out).
        """
        try:
            redis = await self._get_redis()
            failed_key = self._get_failed_key(email)
            lockout_key = self._get_lockout_key(email)

            # Increment failed attempt counter
            attempts = await redis.incr(failed_key)

            # Set/refresh expiry on the failed attempts counter
            await redis.expire(failed_key, FAILED_ATTEMPT_WINDOW_MINUTES * 60)

            # Check if we should lock the account
            if attempts >= MAX_FAILED_ATTEMPTS:
                # Lock the account
                await redis.setex(
                    lockout_key,
                    LOCKOUT_DURATION_MINUTES * 60,
                    datetime.now(UTC).isoformat(),
                )
                logger.warning(
                    f"Account locked due to {attempts} failed login attempts: "
                    f"{email[:3]}***{email[-10:]}"
                )
                return attempts, True

            logger.info(
                f"Failed login attempt {attempts}/{MAX_FAILED_ATTEMPTS} for: "
                f"{email[:3]}***{email[-10:]}"
            )
            return attempts, False

        except Exception as e:
            logger.error(f"Failed to record failed attempt: {e}")
            return 0, False

    async def record_successful_login(self, email: str) -> None:
        """Clear failed attempt counter after successful login.

        Args:
            email: User email that logged in successfully.
        """
        try:
            redis = await self._get_redis()
            failed_key = self._get_failed_key(email)

            # Clear the failed attempts counter
            await redis.delete(failed_key)

        except Exception as e:
            logger.error(f"Failed to clear failed attempts: {e}")

    async def unlock_account(self, email: str) -> bool:
        """Manually unlock a locked account (admin action).

        Args:
            email: User email to unlock.

        Returns:
            True if account was unlocked, False if not locked or error.
        """
        try:
            redis = await self._get_redis()
            failed_key = self._get_failed_key(email)
            lockout_key = self._get_lockout_key(email)

            # Remove lockout and failed attempts
            deleted = await redis.delete(lockout_key, failed_key)

            if deleted > 0:
                logger.info(f"Account unlocked by admin: {email[:3]}***{email[-10:]}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to unlock account: {e}")
            return False

    async def get_failed_attempts(self, email: str) -> int:
        """Get current failed attempt count for an account.

        Args:
            email: User email to check.

        Returns:
            Number of failed attempts, or 0 if none/error.
        """
        try:
            redis = await self._get_redis()
            failed_key = self._get_failed_key(email)
            count = await redis.get(failed_key)
            return int(count) if count else 0

        except Exception as e:
            logger.error(f"Failed to get failed attempts: {e}")
            return 0


# Singleton instance
account_lockout = AccountLockout()
