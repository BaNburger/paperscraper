"""FastAPI dependencies for dependency injection."""

from dataclasses import dataclass
from datetime import datetime, timezone
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


@dataclass
class APIKeyAuth:
    """Authentication context from an API key."""

    api_key_id: UUID
    organization_id: UUID
    permissions: list[str]


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


# =============================================================================
# API Key Authentication
# =============================================================================


async def get_api_key_auth(
    db: Annotated[AsyncSession, Depends(get_db)],
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> APIKeyAuth | None:
    """Authenticate using an API key from the X-API-Key header.

    Args:
        db: Database session.
        x_api_key: API key from X-API-Key header.

    Returns:
        APIKeyAuth context if authenticated, None if no API key provided.

    Raises:
        UnauthorizedError: If API key is invalid or expired.
    """
    if not x_api_key:
        return None

    # Import here to avoid circular import
    from paper_scraper.modules.developer import service as dev_service
    from paper_scraper.modules.developer.models import APIKey

    # Hash the key and look it up
    key_hash = dev_service.hash_api_key(x_api_key)
    api_key = await dev_service.get_api_key_by_hash(db, key_hash)

    if not api_key:
        raise UnauthorizedError("Invalid or expired API key")

    # Update last used timestamp (fire and forget)
    await dev_service.update_api_key_last_used(db, api_key.id)

    return APIKeyAuth(
        api_key_id=api_key.id,
        organization_id=api_key.organization_id,
        permissions=api_key.permissions,
    )


async def get_current_user_or_api_key(
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> User | APIKeyAuth:
    """Authenticate using either JWT token or API key.

    Prefers JWT if both are provided.

    Args:
        db: Database session.
        authorization: Authorization header with Bearer token.
        x_api_key: API key from X-API-Key header.

    Returns:
        User or APIKeyAuth depending on authentication method.

    Raises:
        UnauthorizedError: If neither auth method is provided or valid.
    """
    # Try JWT first if provided
    if authorization:
        return await get_current_user(db, authorization)

    # Try API key
    if x_api_key:
        api_key_auth = await get_api_key_auth(db, x_api_key)
        if api_key_auth:
            return api_key_auth

    raise UnauthorizedError("Authentication required")


async def get_organization_id_from_auth(
    auth: Annotated[User | APIKeyAuth, Depends(get_current_user_or_api_key)],
) -> UUID:
    """Get organization ID from either User or API key authentication.

    Args:
        auth: User or APIKeyAuth from authentication.

    Returns:
        Organization UUID.

    Raises:
        UnauthorizedError: If no organization is associated.
    """
    if isinstance(auth, User):
        if not auth.organization_id:
            raise UnauthorizedError("User is not associated with an organization")
        return auth.organization_id
    else:
        return auth.organization_id


def require_api_permission(*permissions: str):
    """Dependency factory that checks API key has required permissions.

    Args:
        *permissions: Permission strings to check.

    Returns:
        Dependency function.
    """

    async def _check(
        auth: Annotated[User | APIKeyAuth, Depends(get_current_user_or_api_key)],
    ) -> User | APIKeyAuth:
        if isinstance(auth, User):
            # User with JWT - check role-based permissions
            for perm in permissions:
                try:
                    check_permission(auth.role.value, Permission(perm))
                except ValueError:
                    # Permission string not in Permission enum, skip
                    pass
            return auth
        else:
            # API key - check API key permissions
            missing = [p for p in permissions if p not in auth.permissions]
            if missing:
                raise ForbiddenError(
                    f"API key missing required permissions: {', '.join(missing)}"
                )
            return auth

    return _check


# Type aliases for API key authentication
CurrentUserOrAPIKey = Annotated[User | APIKeyAuth, Depends(get_current_user_or_api_key)]
OrganizationIdFromAuth = Annotated[UUID, Depends(get_organization_id_from_auth)]
