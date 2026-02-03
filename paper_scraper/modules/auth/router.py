"""FastAPI router for authentication endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, require_admin
from paper_scraper.api.middleware import limiter
from paper_scraper.core.database import get_db
from paper_scraper.modules.auth.models import UserRole
from paper_scraper.modules.auth.schemas import (
    AcceptInviteRequest,
    ChangePasswordRequest,
    DeleteAccountRequest,
    ForgotPasswordRequest,
    GDPRDataExport,
    InvitationInfoResponse,
    InviteUserRequest,
    LoginRequest,
    MessageResponse,
    OrganizationUsersResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TeamInvitationResponse,
    TokenResponse,
    UpdateRoleRequest,
    UserListResponse,
    UserResponse,
    UserUpdate,
    UserWithOrganization,
    VerifyEmailRequest,
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
@limiter.limit("5/minute")
async def register(
    request: Request,
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
@limiter.limit("10/minute")
async def login(
    request: Request,
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


# =============================================================================
# Email Verification Endpoints
# =============================================================================


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email address",
)
async def verify_email(
    request: VerifyEmailRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    """Verify email address with token received via email."""
    await auth_service.verify_email(request.token)
    return MessageResponse(message="Email verified successfully")


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    summary="Resend verification email",
)
async def resend_verification(
    request: ResendVerificationRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    """Resend email verification link.

    Always returns success to prevent email enumeration.
    """
    await auth_service.resend_verification_email(request.email)
    return MessageResponse(
        message="If an account exists with this email, a verification link has been sent"
    )


# =============================================================================
# Password Reset Endpoints
# =============================================================================


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request password reset",
)
@limiter.limit("5/minute")
async def forgot_password(
    request: Request,
    forgot_data: ForgotPasswordRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    """Request a password reset email.

    Always returns success to prevent email enumeration.
    """
    await auth_service.initiate_password_reset(forgot_data.email)
    return MessageResponse(
        message="If an account exists with this email, a password reset link has been sent"
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password with token",
)
@limiter.limit("5/minute")
async def reset_password(
    request: Request,
    reset_data: ResetPasswordRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    """Reset password using token from email."""
    await auth_service.reset_password(reset_data.token, reset_data.new_password)
    return MessageResponse(message="Password reset successfully")


# =============================================================================
# Team Invitation Endpoints
# =============================================================================


@router.post(
    "/invite",
    response_model=TeamInvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite user to organization",
    dependencies=[Depends(require_admin)],
)
async def invite_user(
    request: InviteUserRequest,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TeamInvitationResponse:
    """Invite a new user to join the organization.

    Only admins can send invitations.
    """
    invitation = await auth_service.create_team_invitation(
        email=request.email,
        role=request.role,
        organization_id=current_user.organization_id,
        inviter=current_user,
    )
    return TeamInvitationResponse.model_validate(invitation)


@router.get(
    "/invitation/{token}",
    response_model=InvitationInfoResponse,
    summary="Get invitation info",
)
async def get_invitation_info(
    token: str,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> InvitationInfoResponse:
    """Get invitation details for the accept-invite page.

    This is a public endpoint (no auth required).
    """
    return await auth_service.get_invitation_info(token)


@router.post(
    "/accept-invite",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Accept team invitation",
)
async def accept_invite(
    request: AcceptInviteRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """Accept a team invitation and create account.

    This is a public endpoint (no auth required).
    """
    user, tokens = await auth_service.accept_invitation(
        token=request.token,
        password=request.password,
        full_name=request.full_name,
    )
    return tokens


@router.get(
    "/invitations",
    response_model=list[TeamInvitationResponse],
    summary="List pending invitations",
    dependencies=[Depends(require_admin)],
)
async def list_invitations(
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> list[TeamInvitationResponse]:
    """List all pending invitations for the organization.

    Only admins can view invitations.
    """
    invitations = await auth_service.list_pending_invitations(
        current_user.organization_id
    )
    return [TeamInvitationResponse.model_validate(inv) for inv in invitations]


@router.delete(
    "/invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel invitation",
    dependencies=[Depends(require_admin)],
)
async def cancel_invitation(
    invitation_id: UUID,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> None:
    """Cancel a pending invitation.

    Only admins can cancel invitations.
    """
    await auth_service.cancel_invitation(invitation_id, current_user.organization_id)


# =============================================================================
# User Management Endpoints (Admin)
# =============================================================================


@router.get(
    "/users",
    response_model=OrganizationUsersResponse,
    summary="List organization users",
    dependencies=[Depends(require_admin)],
)
async def list_users(
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> OrganizationUsersResponse:
    """List all users in the organization.

    Only admins can list users.
    """
    return await auth_service.list_organization_users(current_user.organization_id)


@router.patch(
    "/users/{user_id}/role",
    response_model=UserListResponse,
    summary="Update user role",
    dependencies=[Depends(require_admin)],
)
async def update_user_role(
    user_id: UUID,
    request: UpdateRoleRequest,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserListResponse:
    """Update a user's role.

    Only admins can change user roles. Cannot change own role.
    """
    user = await auth_service.update_user_role(
        user_id=user_id,
        new_role=request.role,
        organization_id=current_user.organization_id,
        current_user=current_user,
    )
    return UserListResponse.model_validate(user)


@router.post(
    "/users/{user_id}/deactivate",
    response_model=UserListResponse,
    summary="Deactivate user",
    dependencies=[Depends(require_admin)],
)
async def deactivate_user(
    user_id: UUID,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserListResponse:
    """Deactivate a user account.

    Only admins can deactivate users. Cannot deactivate self.
    """
    user = await auth_service.deactivate_user(
        user_id=user_id,
        organization_id=current_user.organization_id,
        current_user=current_user,
    )
    return UserListResponse.model_validate(user)


@router.post(
    "/users/{user_id}/reactivate",
    response_model=UserListResponse,
    summary="Reactivate user",
    dependencies=[Depends(require_admin)],
)
async def reactivate_user(
    user_id: UUID,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserListResponse:
    """Reactivate a deactivated user account.

    Only admins can reactivate users.
    """
    user = await auth_service.reactivate_user(
        user_id=user_id,
        organization_id=current_user.organization_id,
    )
    return UserListResponse.model_validate(user)


# =============================================================================
# Onboarding Endpoints
# =============================================================================


@router.post(
    "/onboarding/complete",
    response_model=MessageResponse,
    summary="Mark onboarding as complete",
)
async def complete_onboarding(
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    """Mark the current user's onboarding as complete."""
    await auth_service.complete_onboarding(current_user)
    return MessageResponse(message="Onboarding completed successfully")


# =============================================================================
# GDPR Compliance Endpoints
# =============================================================================


@router.get(
    "/export-data",
    response_model=GDPRDataExport,
    summary="Export user data (GDPR)",
)
async def export_user_data(
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> GDPRDataExport:
    """Export all user and organization data as JSON.

    GDPR Article 20: Right to data portability.
    Returns all data associated with the user's account and organization.
    """
    return await auth_service.export_user_data(current_user)


@router.delete(
    "/delete-account",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete account (GDPR)",
)
async def delete_account(
    request: DeleteAccountRequest,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> None:
    """Permanently delete account and all associated data.

    GDPR Article 17: Right to erasure ("right to be forgotten").

    Requires password confirmation. If the user is the sole admin of an
    organization, they must set delete_organization=true to delete the
    entire organization and all its data.

    WARNING: This action is irreversible!
    """
    if not request.confirm_deletion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must confirm deletion by setting confirm_deletion=true",
        )

    await auth_service.delete_account(
        user=current_user,
        password=request.password,
        delete_organization=request.delete_organization,
    )
