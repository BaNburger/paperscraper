"""FastAPI router for authentication endpoints."""

from datetime import UTC, datetime
from typing import Annotated, Literal, cast
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Header,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, require_admin
from paper_scraper.api.middleware import limiter
from paper_scraper.core.account_lockout import account_lockout
from paper_scraper.core.config import settings
from paper_scraper.core.database import get_db
from paper_scraper.core.security import decode_token, generate_secure_token
from paper_scraper.core.token_blacklist import token_blacklist
from paper_scraper.modules.audit.models import AuditAction
from paper_scraper.modules.audit.service import AuditService
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
    OrganizationResponse,
    OrganizationUsersResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TeamInvitationResponse,
    TokenResponse,
    UpdateBrandingRequest,
    UpdateRoleRequest,
    UserListResponse,
    UserResponse,
    UserUpdate,
    UserWithOrganization,
    VerifyEmailRequest,
)
from paper_scraper.modules.auth.service import AuthService

router = APIRouter()


def _set_cookie(
    response: Response,
    *,
    key: str,
    value: str,
    max_age: int,
    httponly: bool,
) -> None:
    same_site = cast(
        Literal["lax", "strict", "none"],
        settings.AUTH_COOKIE_SAMESITE,
    )
    response.set_cookie(
        key=key,
        value=value,
        max_age=max_age,
        httponly=httponly,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=same_site,
        domain=settings.AUTH_COOKIE_DOMAIN,
        path=settings.AUTH_COOKIE_PATH,
    )


def _delete_cookie(response: Response, key: str) -> None:
    same_site = cast(
        Literal["lax", "strict", "none"],
        settings.AUTH_COOKIE_SAMESITE,
    )
    response.delete_cookie(
        key=key,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=same_site,
        domain=settings.AUTH_COOKIE_DOMAIN,
        path=settings.AUTH_COOKIE_PATH,
    )


def _set_auth_cookies(response: Response, tokens: TokenResponse) -> None:
    """Write auth and CSRF cookies for browser sessions."""
    csrf_token = generate_secure_token(24)

    _set_cookie(
        response,
        key=settings.AUTH_ACCESS_COOKIE_NAME,
        value=tokens.access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
    )
    _set_cookie(
        response,
        key=settings.AUTH_REFRESH_COOKIE_NAME,
        value=tokens.refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
    )
    _set_cookie(
        response,
        key=settings.AUTH_CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=False,
    )


def _clear_auth_cookies(response: Response) -> None:
    """Clear browser auth cookies."""
    _delete_cookie(response, settings.AUTH_ACCESS_COOKIE_NAME)
    _delete_cookie(response, settings.AUTH_REFRESH_COOKIE_NAME)
    _delete_cookie(response, settings.AUTH_CSRF_COOKIE_NAME)


def get_auth_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AuthService:
    """Dependency to get auth service instance."""
    return AuthService(db)


def get_audit_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AuditService:
    """Dependency to get audit service instance."""
    return AuditService(db)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user and organization",
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    response: Response,
    register_data: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> TokenResponse:
    """Register a new user and create their organization.

    This endpoint creates:
    - A new organization with the provided name and type
    - A new user as the admin of that organization

    Returns JWT tokens for immediate authentication.
    """
    user, organization = await auth_service.register(register_data)

    # Audit log: new user registration
    await audit_service.log(
        action=AuditAction.REGISTER,
        user_id=user.id,
        organization_id=organization.id,
        resource_type="user",
        resource_id=user.id,
        details={"email": user.email, "organization_name": organization.name},
        request=request,
    )

    tokens = auth_service.create_tokens(user)
    _set_auth_cookies(response, tokens)
    return tokens


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and get tokens",
)
@limiter.limit("10/minute")
async def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> TokenResponse:
    """Authenticate a user with email and password.

    Returns JWT access and refresh tokens on successful authentication.
    """
    try:
        user = await auth_service.authenticate_user(
            email=login_data.email,
            password=login_data.password,
        )

        # Audit log: successful login
        await audit_service.log(
            action=AuditAction.LOGIN,
            user_id=user.id,
            organization_id=user.organization_id,
            resource_type="user",
            resource_id=user.id,
            details={"email": user.email},
            request=request,
        )

        tokens = auth_service.create_tokens(user)
        _set_auth_cookies(response, tokens)
        return tokens

    except Exception as e:
        # Audit log: failed login attempt (without exposing if user exists)
        await audit_service.log(
            action=AuditAction.LOGIN_FAILED,
            user_id=None,
            organization_id=None,
            resource_type="user",
            details={"email_attempted": login_data.email, "reason": str(e)[:100]},
            request=request,
        )
        raise


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    response: Response,
    refresh_data: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """Get new access and refresh tokens using a valid refresh token.

    The old refresh token should be discarded after calling this endpoint.
    """
    refresh_token_value = (
        refresh_data.refresh_token
        or request.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)
    )
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )
    tokens = await auth_service.refresh_tokens(refresh_token_value)
    _set_auth_cookies(response, tokens)
    return tokens


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout and invalidate token",
)
async def logout(
    request: Request,
    response: Response,
    current_user: CurrentUser,
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Logout the current user and invalidate their access token.

    The access token will be added to the blacklist and cannot be reused.
    For full security, clients should also discard the refresh token.
    """
    # Extract token from Authorization header
    # Note: current_user already validated the token, so we just need to extract it
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    elif request.cookies.get(settings.AUTH_ACCESS_COOKIE_NAME):
        token = request.cookies.get(settings.AUTH_ACCESS_COOKIE_NAME)

    if token:
        payload = decode_token(token)
        if payload:
            jti = payload.get("jti")
            exp_timestamp = payload.get("exp")
            if jti and exp_timestamp:
                exp = datetime.fromtimestamp(exp_timestamp, tz=UTC)
                await token_blacklist.blacklist_token(jti, exp)

    _clear_auth_cookies(response)

    # Audit log: logout
    await audit_service.log(
        action=AuditAction.LOGOUT,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_type="user",
        resource_id=current_user.id,
        request=request,
    )


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
    request: Request,
    password_data: ChangePasswordRequest,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> None:
    """Change the current user's password.

    Requires the current password for verification.
    """
    await auth_service.change_password(
        user=current_user,
        current_password=password_data.current_password,
        new_password=password_data.new_password,
    )

    # Audit log: password change
    await audit_service.log(
        action=AuditAction.PASSWORD_CHANGE,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_type="user",
        resource_id=current_user.id,
        request=request,
    )


# =============================================================================
# Email Verification Endpoints
# =============================================================================


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email address",
)
@limiter.limit("10/minute")
async def verify_email(
    request: Request,
    verify_data: VerifyEmailRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> MessageResponse:
    """Verify email address with token received via email."""
    user = await auth_service.verify_email(verify_data.token)

    # Audit log: email verification
    await audit_service.log(
        action=AuditAction.EMAIL_VERIFY,
        user_id=user.id,
        organization_id=user.organization_id,
        resource_type="user",
        resource_id=user.id,
        details={"email": user.email},
        request=request,
    )

    return MessageResponse(message="Email verified successfully")


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    summary="Resend verification email",
)
@limiter.limit("3/minute")
async def resend_verification(
    request: Request,
    resend_data: ResendVerificationRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    """Resend email verification link.

    Always returns success to prevent email enumeration.
    """
    await auth_service.resend_verification_email(resend_data.email)
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
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> MessageResponse:
    """Request a password reset email.

    Always returns success to prevent email enumeration.
    """
    await auth_service.initiate_password_reset(forgot_data.email)

    # Audit log: password reset request (don't expose if email exists)
    await audit_service.log(
        action=AuditAction.PASSWORD_RESET_REQUEST,
        user_id=None,
        organization_id=None,
        resource_type="user",
        details={"email_requested": forgot_data.email[:3] + "***"},  # Partial for privacy
        request=request,
    )

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
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> MessageResponse:
    """Reset password using token from email."""
    user = await auth_service.reset_password(reset_data.token, reset_data.new_password)

    # Audit log: password reset completed
    await audit_service.log(
        action=AuditAction.PASSWORD_RESET,
        user_id=user.id,
        organization_id=user.organization_id,
        resource_type="user",
        resource_id=user.id,
        request=request,
    )

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
    http_request: Request,
    invite_request: InviteUserRequest,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> TeamInvitationResponse:
    """Invite a new user to join the organization.

    Only admins can send invitations.
    """
    invitation = await auth_service.create_team_invitation(
        email=invite_request.email,
        role=invite_request.role,
        organization_id=current_user.organization_id,
        inviter=current_user,
    )

    # Audit log: user invitation
    await audit_service.log(
        action=AuditAction.USER_INVITE,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_type="invitation",
        resource_id=invitation.id,
        details={"invited_email": invite_request.email, "role": invite_request.role.value},
        request=http_request,
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
@limiter.limit("5/minute")
async def accept_invite(
    request: Request,
    invite_data: AcceptInviteRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> TokenResponse:
    """Accept a team invitation and create account.

    This is a public endpoint (no auth required).
    """
    user, tokens = await auth_service.accept_invitation(
        token=invite_data.token,
        password=invite_data.password,
        full_name=invite_data.full_name,
    )

    # Audit log: invitation accepted
    await audit_service.log(
        action=AuditAction.USER_INVITE_ACCEPT,
        user_id=user.id,
        organization_id=user.organization_id,
        resource_type="user",
        resource_id=user.id,
        details={"email": user.email, "role": user.role.value},
        request=request,
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
    http_request: Request,
    user_id: UUID,
    role_request: UpdateRoleRequest,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> UserListResponse:
    """Update a user's role.

    Only admins can change user roles. Cannot change own role.
    """
    # Get old role for audit log
    old_user = await auth_service.get_user_by_id(user_id)
    old_role = old_user.role.value if old_user else "unknown"

    user = await auth_service.update_user_role(
        user_id=user_id,
        new_role=role_request.role,
        organization_id=current_user.organization_id,
        current_user=current_user,
    )

    # Audit log: role change
    await audit_service.log(
        action=AuditAction.USER_ROLE_CHANGE,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_type="user",
        resource_id=user_id,
        details={
            "target_user_email": user.email,
            "old_role": old_role,
            "new_role": role_request.role.value,
        },
        request=http_request,
    )

    return UserListResponse.model_validate(user)


@router.post(
    "/users/{user_id}/deactivate",
    response_model=UserListResponse,
    summary="Deactivate user",
    dependencies=[Depends(require_admin)],
)
async def deactivate_user(
    request: Request,
    user_id: UUID,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> UserListResponse:
    """Deactivate a user account.

    Only admins can deactivate users. Cannot deactivate self.
    """
    user = await auth_service.deactivate_user(
        user_id=user_id,
        organization_id=current_user.organization_id,
        current_user=current_user,
    )

    # Audit log: user deactivation
    await audit_service.log(
        action=AuditAction.USER_DEACTIVATE,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_type="user",
        resource_id=user_id,
        details={"target_user_email": user.email},
        request=request,
    )

    return UserListResponse.model_validate(user)


@router.post(
    "/users/{user_id}/reactivate",
    response_model=UserListResponse,
    summary="Reactivate user",
    dependencies=[Depends(require_admin)],
)
async def reactivate_user(
    request: Request,
    user_id: UUID,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> UserListResponse:
    """Reactivate a deactivated user account.

    Only admins can reactivate users.
    """
    user = await auth_service.reactivate_user(
        user_id=user_id,
        organization_id=current_user.organization_id,
    )

    # Audit log: user reactivation
    await audit_service.log(
        action=AuditAction.USER_REACTIVATE,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_type="user",
        resource_id=user_id,
        details={"target_user_email": user.email},
        request=request,
    )

    return UserListResponse.model_validate(user)


@router.post(
    "/users/{user_id}/unlock",
    response_model=MessageResponse,
    summary="Unlock user account",
    dependencies=[Depends(require_admin)],
)
async def unlock_user_account(
    user_id: UUID,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    """Unlock a user account that was locked due to failed login attempts.

    Only admins can unlock accounts.
    """
    # Get the user to verify they exist and belong to the organization
    user = await auth_service.get_user_by_id(user_id)
    if not user or user.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    unlocked = await account_lockout.unlock_account(user.email)
    if unlocked:
        return MessageResponse(message="Account unlocked successfully")
    return MessageResponse(message="Account was not locked")


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
    request: Request,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> GDPRDataExport:
    """Export all user and organization data as JSON.

    GDPR Article 20: Right to data portability.
    Returns all data associated with the user's account and organization.
    """
    data = await auth_service.export_user_data(current_user)

    # Audit log: GDPR data export
    await audit_service.log(
        action=AuditAction.DATA_EXPORT,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_type="user",
        resource_id=current_user.id,
        details={"export_type": "gdpr_full_export"},
        request=request,
    )

    return data


@router.delete(
    "/delete-account",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete account (GDPR)",
)
async def delete_account(
    http_request: Request,
    delete_request: DeleteAccountRequest,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> None:
    """Permanently delete account and all associated data.

    GDPR Article 17: Right to erasure ("right to be forgotten").

    Requires password confirmation. If the user is the sole admin of an
    organization, they must set delete_organization=true to delete the
    entire organization and all its data.

    WARNING: This action is irreversible!
    """
    if not delete_request.confirm_deletion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must confirm deletion by setting confirm_deletion=true",
        )

    # Capture user info before deletion
    user_email = current_user.email
    user_id = current_user.id
    org_id = current_user.organization_id

    # Audit log: GDPR account deletion (log before deletion!)
    await audit_service.log(
        action=AuditAction.ACCOUNT_DELETE,
        user_id=user_id,
        organization_id=org_id,
        resource_type="user",
        resource_id=user_id,
        details={
            "email": user_email,
            "delete_organization": delete_request.delete_organization,
        },
        request=http_request,
    )

    await auth_service.delete_account(
        user=current_user,
        password=delete_request.password,
        delete_organization=delete_request.delete_organization,
    )


# =============================================================================
# RBAC Permission Endpoints
# =============================================================================


@router.get(
    "/permissions",
    summary="List current user's permissions",
)
async def get_my_permissions(
    current_user: CurrentUser,
) -> dict:
    """Return the effective permissions for the current user based on their role."""
    from paper_scraper.core.permissions import get_permissions_for_role

    perms = get_permissions_for_role(current_user.role.value)
    return {
        "role": current_user.role.value,
        "permissions": [p.value for p in perms],
    }


@router.get(
    "/roles",
    summary="List available roles and their permissions",
    dependencies=[Depends(require_admin)],
)
async def list_roles(
    current_user: CurrentUser,
) -> dict:
    """Return all available roles and their associated permissions (admin only)."""
    from paper_scraper.core.permissions import ROLE_PERMISSIONS

    return {
        "roles": {
            role: [p.value for p in perms]
            for role, perms in ROLE_PERMISSIONS.items()
        },
    }


# =============================================================================
# Organization Branding
# =============================================================================

_LOGO_MAX_SIZE = 5_000_000  # 5MB
_LOGO_ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp"}


@router.patch(
    "/organization/branding",
    response_model=OrganizationResponse,
    summary="Update organization branding",
    dependencies=[Depends(require_admin)],
)
async def update_branding(
    request: Request,
    branding_data: UpdateBrandingRequest,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> OrganizationResponse:
    """Update organization branding colors (admin only)."""
    org = await auth_service.update_branding(
        org_id=current_user.organization_id,
        branding_update=branding_data.model_dump(exclude_none=True),
    )
    await audit_service.log(
        action=AuditAction.UPDATE,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_type="organization_branding",
        resource_id=current_user.organization_id,
        details=branding_data.model_dump(exclude_none=True),
        request=request,
    )
    return org


@router.post(
    "/organization/logo",
    response_model=OrganizationResponse,
    summary="Upload organization logo",
    dependencies=[Depends(require_admin)],
)
async def upload_logo(
    request: Request,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    file: UploadFile = File(...),
) -> OrganizationResponse:
    """Upload organization logo to storage (admin only)."""
    if not file.content_type or file.content_type not in _LOGO_ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(_LOGO_ALLOWED_TYPES)}",
        )

    content = await file.read()
    if len(content) > _LOGO_MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")

    org = await auth_service.upload_logo(
        org_id=current_user.organization_id,
        file_content=content,
        content_type=file.content_type,
        filename=file.filename or "logo",
    )
    await audit_service.log(
        action=AuditAction.UPDATE,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_type="organization_logo",
        resource_id=current_user.organization_id,
        details={"filename": file.filename, "content_type": file.content_type},
        request=request,
    )
    return org
