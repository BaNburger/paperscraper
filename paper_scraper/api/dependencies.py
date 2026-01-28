"""FastAPI dependencies for dependency injection."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.database import get_db
from paper_scraper.core.exceptions import UnauthorizedError
from paper_scraper.core.security import decode_token, validate_token_type
from paper_scraper.modules.auth.models import User


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    """Get the currently authenticated user from the JWT token.

    Args:
        db: Database session.
        authorization: Authorization header containing the Bearer token.

    Returns:
        The authenticated User object.

    Raises:
        UnauthorizedError: If token is missing, invalid, or user not found.
    """
    if not authorization:
        raise UnauthorizedError("Missing authorization header")

    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError("Invalid authorization header format")

    token = parts[1]

    # Decode and validate token
    payload = decode_token(token)
    if not payload:
        raise UnauthorizedError("Invalid or expired token")

    if not validate_token_type(payload, "access"):
        raise UnauthorizedError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token payload")

    # Fetch user from database
    try:
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()
    except ValueError:
        raise UnauthorizedError("Invalid user ID in token")

    if not user:
        raise UnauthorizedError("User not found")

    if not user.is_active:
        raise UnauthorizedError("User account is deactivated")

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get the current active user (alias for get_current_user with active check).

    Args:
        current_user: The authenticated user from get_current_user.

    Returns:
        The active User object.
    """
    return current_user


async def get_organization_id(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UUID:
    """Get the organization ID of the current user.

    Args:
        current_user: The authenticated user.

    Returns:
        The organization UUID.

    Raises:
        UnauthorizedError: If user has no organization.
    """
    if not current_user.organization_id:
        raise UnauthorizedError("User is not associated with an organization")
    return current_user.organization_id


# Type aliases for cleaner dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
OrganizationId = Annotated[UUID, Depends(get_organization_id)]
