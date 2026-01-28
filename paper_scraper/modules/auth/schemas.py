"""Pydantic schemas for authentication module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from paper_scraper.modules.auth.models import (
    OrganizationType,
    SubscriptionTier,
    UserRole,
)


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
