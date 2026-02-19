"""Security utilities for authentication and authorization."""

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from paper_scraper.core.config import settings

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password to verify.
        hashed_password: The hashed password to compare against.

    Returns:
        True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: The plain text password to hash.

    Returns:
        The hashed password string.
    """
    return pwd_context.hash(password)


def _create_jwt_token(
    subject: str | Any,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a JWT token with the specified type and expiration.

    Args:
        subject: The subject (typically user ID) to encode in the token.
        token_type: Token type ("access" or "refresh").
        expires_delta: Expiration time delta.
        extra_claims: Optional additional claims to include in the token.

    Returns:
        The encoded JWT token string.
    """
    now = datetime.now(UTC)
    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": now + expires_delta,
        "iat": int(now.timestamp()),
        "jti": str(uuid.uuid4()),
        "type": token_type,
    }

    if extra_claims:
        to_encode.update(extra_claims)

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )


def create_access_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        subject: The subject (typically user ID) to encode in the token.
        expires_delta: Optional custom expiration time.
        extra_claims: Optional additional claims to include in the token.

    Returns:
        The encoded JWT token string.
    """
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_jwt_token(subject, "access", delta, extra_claims)


def create_refresh_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT refresh token.

    Args:
        subject: The subject (typically user ID) to encode in the token.
        expires_delta: Optional custom expiration time.

    Returns:
        The encoded JWT refresh token string.
    """
    delta = expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_jwt_token(subject, "refresh", delta)


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token.

    Args:
        token: The JWT token string to decode.

    Returns:
        The decoded token payload if valid, None otherwise.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None


def validate_token_type(payload: dict[str, Any], expected_type: str) -> bool:
    """Validate the token type matches expected.

    Args:
        payload: The decoded token payload.
        expected_type: The expected token type ("access" or "refresh").

    Returns:
        True if the token type matches, False otherwise.
    """
    return payload.get("type") == expected_type


# =============================================================================
# Secure Token Generation
# =============================================================================


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token.

    Args:
        length: The number of bytes to generate (result will be 2x this in hex).

    Returns:
        A URL-safe hex string token.
    """
    return secrets.token_urlsafe(length)


def _generate_token_with_expiry(expires_delta: timedelta) -> tuple[str, datetime]:
    """Generate a secure token with an expiration datetime.

    Args:
        expires_delta: Time until the token expires.

    Returns:
        A tuple of (token, expires_at datetime).
    """
    token = generate_secure_token()
    expires_at = datetime.now(UTC) + expires_delta
    return token, expires_at


def generate_verification_token() -> tuple[str, datetime]:
    """Generate an email verification token with expiry.

    Returns:
        A tuple of (token, expires_at datetime).
    """
    return _generate_token_with_expiry(
        timedelta(minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES)
    )


def generate_password_reset_token() -> tuple[str, datetime]:
    """Generate a password reset token with expiry.

    Returns:
        A tuple of (token, expires_at datetime).
    """
    return _generate_token_with_expiry(
        timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    )


def generate_invitation_token() -> tuple[str, datetime]:
    """Generate a team invitation token with expiry.

    Returns:
        A tuple of (token, expires_at datetime).
    """
    return _generate_token_with_expiry(timedelta(days=settings.TEAM_INVITATION_TOKEN_EXPIRE_DAYS))


def is_token_expired(expires_at: datetime | None) -> bool:
    """Check if a token has expired.

    Args:
        expires_at: The expiration datetime of the token.

    Returns:
        True if expired or no expiry set, False otherwise.
    """
    if expires_at is None:
        return True
    return datetime.now(UTC) > expires_at
