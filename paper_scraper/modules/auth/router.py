"""FastAPI router for authentication endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser
from paper_scraper.core.database import get_db
from paper_scraper.modules.auth.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    UserUpdate,
    UserWithOrganization,
)
from paper_scraper.modules.auth.service import AuthService

router = APIRouter()


def get_auth_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AuthService:
    """Dependency to get auth service instance."""
    return AuthService(db)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user and organization",
)
async def register(
    register_data: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """Register a new user and create their organization.

    This endpoint creates:
    - A new organization with the provided name and type
    - A new user as the admin of that organization

    Returns JWT tokens for immediate authentication.
    """
    user, _ = await auth_service.register(register_data)
    return auth_service.create_tokens(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and get tokens",
)
async def login(
    login_data: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """Authenticate a user with email and password.

    Returns JWT access and refresh tokens on successful authentication.
    """
    user = await auth_service.authenticate_user(
        email=login_data.email,
        password=login_data.password,
    )
    return auth_service.create_tokens(user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """Get new access and refresh tokens using a valid refresh token.

    The old refresh token should be discarded after calling this endpoint.
    """
    return await auth_service.refresh_tokens(refresh_data.refresh_token)


@router.get(
    "/me",
    response_model=UserWithOrganization,
    summary="Get current user profile",
)
async def get_current_user_profile(
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserWithOrganization:
    """Get the currently authenticated user's profile with organization details."""
    user = await auth_service.get_user_with_organization(current_user.id)
    return user  # type: ignore


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
)
async def update_current_user_profile(
    update_data: UserUpdate,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """Update the currently authenticated user's profile.

    Only modifiable fields (full_name, preferences) can be updated.
    """
    updated_user = await auth_service.update_user(current_user, update_data)
    return updated_user  # type: ignore


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password",
)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> None:
    """Change the current user's password.

    Requires the current password for verification.
    """
    await auth_service.change_password(
        user=current_user,
        current_password=password_data.current_password,
        new_password=password_data.new_password,
    )
