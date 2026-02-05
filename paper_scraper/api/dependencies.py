"""FastAPI dependencies for dependency injection."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.database import get_db
from paper_scraper.core.exceptions import ForbiddenError, UnauthorizedError
from paper_scraper.core.permissions import Permission, check_permission
from paper_scraper.core.security import decode_token, validate_token_type
from paper_scraper.core.token_blacklist import token_blacklist
from paper_scraper.modules.auth.models import User, UserRole


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

    # Check token blacklist (by JTI - specific token)
    jti = payload.get("jti")
    if jti:
        if await token_blacklist.is_token_blacklisted(jti):
            raise UnauthorizedError("Token has been revoked")

    # Check user-level token invalidation (all tokens before timestamp)
    iat = payload.get("iat")
    if iat:
        if await token_blacklist.is_token_invalid_for_user(user_id, iat):
            raise UnauthorizedError("Token has been invalidated")

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
OrganizationId = Annotated[UUID, Depends(get_organization_id)]


async def require_admin(
    current_user: CurrentUser,
) -> User:
    """Require the current user to be an admin.

    Args:
        current_user: The authenticated user.

    Returns:
        The admin User object.

    Raises:
        ForbiddenError: If user is not an admin.
    """
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenError("This action requires admin privileges")
    return current_user


async def require_manager_or_admin(
    current_user: CurrentUser,
) -> User:
    """Require the current user to be a manager or admin.

    Args:
        current_user: The authenticated user.

    Returns:
        The User object.

    Raises:
        ForbiddenError: If user is not a manager or admin.
    """
    if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):
        raise ForbiddenError("This action requires manager or admin privileges")
    return current_user


def require_permission(*permissions: Permission):
    """FastAPI dependency factory that checks the current user has **all**
    of the specified permissions.

    Usage as a route dependency::

        @router.post("/papers/{id}/score",
                      dependencies=[Depends(require_permission(Permission.SCORING_TRIGGER))])
        async def score_paper(...): ...

    Or as a parameter dependency (returns the User)::

        async def delete_paper(
            _auth: Annotated[User, Depends(require_permission(Permission.PAPERS_DELETE))],
            ...
        ): ...
    """

    async def _check(current_user: CurrentUser) -> User:
        check_permission(current_user.role.value, *permissions)
        return current_user

    return _check


# Type aliases for role-based dependencies
AdminUser = Annotated[User, Depends(require_admin)]
ManagerOrAdminUser = Annotated[User, Depends(require_manager_or_admin)]
