"""Pydantic schemas for authentication module."""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from paper_scraper.modules.auth.models import (
    OrganizationType,
    SubscriptionTier,
    UserRole,
)


# =============================================================================
# Password Validation
# =============================================================================

# Common passwords to reject (top passwords from breach lists)
COMMON_PASSWORDS = {
    "password", "12345678", "123456789", "qwerty123", "password1",
    "iloveyou", "sunshine", "princess", "football", "welcome1",
    "shadow12", "superman", "michael1", "password123", "letmein1",
}


def validate_password_complexity(password: str) -> str:
    """Validate password meets complexity requirements.

    Requirements:
    - At least 8 characters (enforced by Field)
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - Not in common password list

    Args:
        password: The password to validate.

    Returns:
        The password if valid.

    Raises:
        ValueError: If password doesn't meet requirements.
    """
    errors = []

    if not re.search(r"[A-Z]", password):
        errors.append("at least one uppercase letter")

    if not re.search(r"[a-z]", password):
        errors.append("at least one lowercase letter")

    if not re.search(r"\d", password):
        errors.append("at least one digit")

    if password.lower() in COMMON_PASSWORDS:
        errors.append("not be a commonly used password")

    if errors:
        raise ValueError(f"Password must contain {', '.join(errors)}")

    return password


# =============================================================================
# Organization Schemas
# =============================================================================


class OrganizationBase(BaseModel):
    """Base schema for organization data."""

    name: str = Field(..., min_length=1, max_length=255)
    type: OrganizationType = OrganizationType.UNIVERSITY


class OrganizationCreate(OrganizationBase):
    """Schema for creating a new organization."""

    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""

    name: str | None = Field(None, min_length=1, max_length=255)
    type: OrganizationType | None = None
    settings: dict | None = None


class OrganizationResponse(OrganizationBase):
    """Schema for organization response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subscription_tier: SubscriptionTier
    settings: dict
    created_at: datetime
    updated_at: datetime


# =============================================================================
# User Schemas
# =============================================================================


class UserBase(BaseModel):
    """Base schema for user data."""

    email: EmailStr
    full_name: str | None = Field(None, max_length=255)


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        """Validate password complexity."""
        return validate_password_complexity(v)


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    full_name: str | None = Field(None, max_length=255)
    preferences: dict | None = None


class UserResponse(UserBase):
    """Schema for user response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    role: UserRole
    preferences: dict
    is_active: bool
    onboarding_completed: bool
    onboarding_completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class UserWithOrganization(UserResponse):
    """Schema for user response including organization details."""

    organization: OrganizationResponse


# =============================================================================
# Auth Schemas
# =============================================================================


class RegisterRequest(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(None, max_length=255)
    organization_name: str = Field(..., min_length=1, max_length=255)
    organization_type: OrganizationType = OrganizationType.UNIVERSITY

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        """Validate password complexity."""
        return validate_password_complexity(v)


class LoginRequest(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    """Schema for refreshing access token."""

    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Schema for changing password."""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        """Validate password complexity."""
        return validate_password_complexity(v)


# =============================================================================
# Email Verification & Password Reset Schemas
# =============================================================================


class ForgotPasswordRequest(BaseModel):
    """Schema for requesting password reset."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for resetting password with token."""

    token: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        """Validate password complexity."""
        return validate_password_complexity(v)


class VerifyEmailRequest(BaseModel):
    """Schema for email verification."""

    token: str


class ResendVerificationRequest(BaseModel):
    """Schema for resending verification email."""

    email: EmailStr


# =============================================================================
# Team Invitation Schemas
# =============================================================================


class InviteUserRequest(BaseModel):
    """Schema for inviting a user to the organization."""

    email: EmailStr
    role: UserRole = UserRole.MEMBER


class AcceptInviteRequest(BaseModel):
    """Schema for accepting a team invitation."""

    token: str
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(None, max_length=255)

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        """Validate password complexity."""
        return validate_password_complexity(v)


class TeamInvitationResponse(BaseModel):
    """Schema for team invitation response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    email: str
    role: UserRole
    status: str
    expires_at: datetime
    created_at: datetime


class InvitationInfoResponse(BaseModel):
    """Schema for invitation info (public, for accept-invite page)."""

    email: str
    organization_name: str
    inviter_name: str | None
    role: UserRole
    expires_at: datetime


# =============================================================================
# User Management Schemas (Admin)
# =============================================================================


class UpdateRoleRequest(BaseModel):
    """Schema for updating user role (admin only)."""

    role: UserRole


class UserListResponse(BaseModel):
    """Schema for user list response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str | None
    role: UserRole
    is_active: bool
    email_verified: bool
    created_at: datetime
    updated_at: datetime


class OrganizationUsersResponse(BaseModel):
    """Schema for organization users list."""

    users: list[UserListResponse]
    total: int
    pending_invitations: int


class MessageResponse(BaseModel):
    """Schema for simple message responses."""

    message: str


# =============================================================================
# GDPR Compliance Schemas
# =============================================================================


class GDPRDataExport(BaseModel):
    """Schema for GDPR data export response."""

    user: UserResponse
    organization: OrganizationResponse
    export_date: datetime
    papers_count: int
    projects_count: int
    saved_searches_count: int
    alerts_count: int
    data: dict  # Full data export as JSON


class DeleteAccountRequest(BaseModel):
    """Schema for account deletion request."""

    password: str = Field(..., description="Current password for verification")
    confirm_deletion: bool = Field(
        ..., description="Must be true to confirm deletion"
    )
    delete_organization: bool = Field(
        default=False,
        description="If true and user is sole admin, delete entire organization",
    )
