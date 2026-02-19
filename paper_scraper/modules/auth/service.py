"""Service layer for authentication module."""

import asyncio
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from paper_scraper.core.account_lockout import account_lockout
from paper_scraper.core.config import settings
from paper_scraper.core.exceptions import (
    DuplicateError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from paper_scraper.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_invitation_token,
    generate_password_reset_token,
    generate_verification_token,
    get_password_hash,
    is_token_expired,
    validate_token_type,
    verify_password,
)
from paper_scraper.core.token_blacklist import token_blacklist
from paper_scraper.modules.auth.models import (
    InvitationStatus,
    Organization,
    TeamInvitation,
    User,
    UserRole,
)
from paper_scraper.modules.auth.schemas import (
    GDPRDataExport,
    InvitationInfoResponse,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUsersResponse,
    RegisterRequest,
    TokenResponse,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from paper_scraper.modules.email.service import email_service


class AuthService:
    """Service for authentication and user management."""

    def __init__(self, db: AsyncSession):
        """Initialize auth service with database session.

        Args:
            db: Async database session.
        """
        self.db = db

    # =========================================================================
    # Organization Methods
    # =========================================================================

    async def create_organization(
        self,
        organization_data: OrganizationCreate,
    ) -> Organization:
        """Create a new organization.

        Args:
            organization_data: Organization creation data.

        Returns:
            The created Organization.
        """
        organization = Organization(
            name=organization_data.name,
            type=organization_data.type,
        )
        self.db.add(organization)
        await self.db.flush()
        return organization

    async def get_organization(self, organization_id: UUID) -> Organization | None:
        """Get an organization by ID.

        Args:
            organization_id: The organization's UUID.

        Returns:
            The Organization if found, None otherwise.
        """
        result = await self.db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        return result.scalar_one_or_none()

    # =========================================================================
    # User Methods
    # =========================================================================

    async def get_user_by_email(self, email: str) -> User | None:
        """Get a user by email address.

        Args:
            email: The user's email address.

        Returns:
            The User if found, None otherwise.
        """
        result = await self.db.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Get a user by ID.

        Args:
            user_id: The user's UUID.

        Returns:
            The User if found, None otherwise.
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_with_organization(self, user_id: UUID) -> User | None:
        """Get a user with their organization loaded.

        Args:
            user_id: The user's UUID.

        Returns:
            The User with organization if found, None otherwise.
        """
        result = await self.db.execute(
            select(User).options(selectinload(User.organization)).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_user(
        self,
        user_data: UserCreate,
        organization_id: UUID,
        role: UserRole = UserRole.MEMBER,
    ) -> User:
        """Create a new user.

        Args:
            user_data: User creation data.
            organization_id: The organization to associate the user with.
            role: The user's role within the organization.

        Returns:
            The created User.

        Raises:
            DuplicateError: If a user with this email already exists.
        """
        # Check for existing user
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise DuplicateError("User", "email", user_data.email)

        user = User(
            email=user_data.email.lower(),
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            organization_id=organization_id,
            role=role,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def update_user(self, user: User, update_data: UserUpdate) -> User:
        """Update a user's profile.

        Args:
            user: The user to update.
            update_data: The update data.

        Returns:
            The updated User.
        """
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(user, field, value)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
    ) -> None:
        """Change a user's password.

        Args:
            user: The user whose password to change.
            current_password: The current password for verification.
            new_password: The new password to set.

        Raises:
            ValidationError: If the current password is incorrect.
        """
        if not verify_password(current_password, user.hashed_password):
            raise ValidationError("Current password is incorrect", field="current_password")

        user.hashed_password = get_password_hash(new_password)
        await self.db.flush()

        # Invalidate all existing tokens for this user (security measure)
        await token_blacklist.invalidate_user_tokens(str(user.id))

    # =========================================================================
    # Authentication Methods
    # =========================================================================

    async def authenticate_user(self, email: str, password: str) -> User:
        """Authenticate a user with email and password.

        Args:
            email: The user's email address.
            password: The user's password.

        Returns:
            The authenticated User.

        Raises:
            UnauthorizedError: If credentials are invalid or account is locked.
        """
        # Check if account is locked out
        if await account_lockout.is_locked_out(email):
            remaining = await account_lockout.get_lockout_remaining_seconds(email)
            raise UnauthorizedError(
                f"Account is temporarily locked due to multiple failed login attempts. "
                f"Please try again in {remaining // 60 + 1} minutes."
            )

        user = await self.get_user_by_email(email)
        if not user:
            # Record failed attempt even for non-existent users to prevent enumeration
            await account_lockout.record_failed_attempt(email)
            raise UnauthorizedError("Invalid email or password")

        if not verify_password(password, user.hashed_password):
            # Record failed attempt
            attempts, locked = await account_lockout.record_failed_attempt(email)
            if locked:
                raise UnauthorizedError(
                    "Account has been locked due to multiple failed login attempts. "
                    "Please try again in 15 minutes or contact support."
                )
            raise UnauthorizedError("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedError("User account is deactivated")

        # Clear failed attempts on successful login
        await account_lockout.record_successful_login(email)

        return user

    async def register(self, register_data: RegisterRequest) -> tuple[User, Organization]:
        """Register a new user and organization.

        This creates both a new organization and a user as the admin.

        Args:
            register_data: Registration data including user and organization info.

        Returns:
            A tuple of (User, Organization).

        Raises:
            DuplicateError: If a user with this email already exists.
        """
        # Check for existing user first
        existing_user = await self.get_user_by_email(register_data.email)
        if existing_user:
            raise DuplicateError("User", "email", register_data.email)

        # Create organization
        organization = Organization(
            name=register_data.organization_name,
            type=register_data.organization_type,
        )
        self.db.add(organization)
        await self.db.flush()

        # Create user as admin of the organization
        user = User(
            email=register_data.email.lower(),
            hashed_password=get_password_hash(register_data.password),
            full_name=register_data.full_name,
            organization_id=organization.id,
            role=UserRole.ADMIN,
        )
        self.db.add(user)
        await self.db.flush()

        return user, organization

    def create_tokens(self, user: User) -> TokenResponse:
        """Create access and refresh tokens for a user.

        Args:
            user: The user to create tokens for.

        Returns:
            TokenResponse with access and refresh tokens.
        """
        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={
                "org_id": str(user.organization_id),
                "role": user.role.value,
            },
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using a refresh token.

        Args:
            refresh_token: The refresh token.

        Returns:
            New TokenResponse with fresh tokens.

        Raises:
            UnauthorizedError: If refresh token is invalid.
        """
        payload = decode_token(refresh_token)
        if not payload:
            raise UnauthorizedError("Invalid refresh token")

        if not validate_token_type(payload, "refresh"):
            raise UnauthorizedError("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError("Invalid token payload")

        # Check if specific token is blacklisted
        jti = payload.get("jti")
        if jti:
            if await token_blacklist.is_token_blacklisted(jti):
                raise UnauthorizedError("Token has been revoked")

        # Check if all user tokens were invalidated
        iat = payload.get("iat")
        if iat:
            if await token_blacklist.is_token_invalid_for_user(user_id, iat):
                raise UnauthorizedError("Token has been invalidated")

        try:
            user = await self.get_user_by_id(UUID(user_id))
        except ValueError as err:
            raise UnauthorizedError("Invalid user ID in token") from err

        if not user:
            raise UnauthorizedError("User not found")

        if not user.is_active:
            raise UnauthorizedError("User account is deactivated")

        return self.create_tokens(user)

    # =========================================================================
    # Email Verification Methods
    # =========================================================================

    async def send_verification_email(self, user: User) -> None:
        """Generate verification token and send verification email.

        Args:
            user: The user to send verification email to.
        """
        token, expires_at = generate_verification_token()
        user.email_verification_token = token
        user.email_verification_token_expires_at = expires_at
        await self.db.flush()

        await email_service.send_verification_email(
            to=user.email,
            token=token,
        )

    async def verify_email(self, token: str) -> User:
        """Verify user email with token.

        Args:
            token: The verification token.

        Returns:
            The verified User.

        Raises:
            ValidationError: If token is invalid or expired.
        """
        result = await self.db.execute(select(User).where(User.email_verification_token == token))
        user = result.scalar_one_or_none()

        if not user:
            raise ValidationError("Invalid verification token", field="token")

        if is_token_expired(user.email_verification_token_expires_at):
            raise ValidationError("Verification token has expired", field="token")

        user.email_verified = True
        user.email_verification_token = None
        user.email_verification_token_expires_at = None
        await self.db.flush()

        return user

    async def resend_verification_email(self, email: str) -> bool:
        """Resend verification email for a user.

        Args:
            email: The user's email address.

        Returns:
            True if email was sent (always returns True to prevent enumeration).
        """
        user = await self.get_user_by_email(email)
        if user and not user.email_verified:
            await self.send_verification_email(user)
        return True

    # =========================================================================
    # Password Reset Methods
    # =========================================================================

    async def initiate_password_reset(self, email: str) -> bool:
        """Initiate password reset flow.

        Args:
            email: The user's email address.

        Returns:
            True always (to prevent email enumeration).
        """
        user = await self.get_user_by_email(email)
        if user:
            token, expires_at = generate_password_reset_token()
            user.password_reset_token = token
            user.password_reset_token_expires_at = expires_at
            await self.db.flush()

            await email_service.send_password_reset_email(
                to=user.email,
                token=token,
            )
        return True

    async def reset_password(self, token: str, new_password: str) -> User:
        """Reset password using reset token.

        Args:
            token: The password reset token.
            new_password: The new password to set.

        Returns:
            The updated User.

        Raises:
            ValidationError: If token is invalid or expired.
        """
        result = await self.db.execute(select(User).where(User.password_reset_token == token))
        user = result.scalar_one_or_none()

        if not user:
            raise ValidationError("Invalid reset token", field="token")

        if is_token_expired(user.password_reset_token_expires_at):
            raise ValidationError("Reset token has expired", field="token")

        user.hashed_password = get_password_hash(new_password)
        user.password_reset_token = None
        user.password_reset_token_expires_at = None
        await self.db.flush()

        # Invalidate all existing tokens for this user (security measure)
        await token_blacklist.invalidate_user_tokens(str(user.id))

        return user

    # =========================================================================
    # Team Invitation Methods
    # =========================================================================

    async def create_team_invitation(
        self,
        email: str,
        role: UserRole,
        organization_id: UUID,
        inviter: User,
    ) -> TeamInvitation:
        """Create a team invitation.

        Args:
            email: Email of the invitee.
            role: Role to assign to the new user.
            organization_id: The organization to invite to.
            inviter: The user sending the invitation.

        Returns:
            The created TeamInvitation.

        Raises:
            DuplicateError: If user already exists in organization.
            ValidationError: If there's a pending invitation.
        """
        # Check if user already exists
        existing_user = await self.get_user_by_email(email)
        if existing_user and existing_user.organization_id == organization_id:
            raise DuplicateError("User", "email", email)

        # Check for pending invitation
        result = await self.db.execute(
            select(TeamInvitation).where(
                TeamInvitation.email == email.lower(),
                TeamInvitation.organization_id == organization_id,
                TeamInvitation.status == InvitationStatus.PENDING,
            )
        )
        existing_invitation = result.scalar_one_or_none()
        if existing_invitation:
            raise ValidationError(
                "An invitation has already been sent to this email",
                field="email",
            )

        # Create invitation
        token, expires_at = generate_invitation_token()
        invitation = TeamInvitation(
            email=email.lower(),
            role=role,
            organization_id=organization_id,
            created_by_id=inviter.id,
            token=token,
            expires_at=expires_at,
        )
        self.db.add(invitation)
        await self.db.flush()

        # Get organization and inviter names for email
        org = await self.get_organization(organization_id)
        inviter_name = inviter.full_name or inviter.email

        await email_service.send_team_invite_email(
            to=email,
            token=token,
            inviter_name=inviter_name,
            org_name=org.name if org else "Unknown Organization",
        )

        return invitation

    async def _validate_pending_invitation(self, invitation: TeamInvitation) -> None:
        """Validate that an invitation is pending and not expired.

        Args:
            invitation: The invitation to validate.

        Raises:
            ValidationError: If invitation is expired or already used.
        """
        if invitation.status != InvitationStatus.PENDING:
            raise ValidationError(
                f"This invitation has already been {invitation.status.value}",
                field="token",
            )

        if is_token_expired(invitation.expires_at):
            invitation.status = InvitationStatus.EXPIRED
            await self.db.flush()
            raise ValidationError("This invitation has expired", field="token")

    async def get_invitation_info(self, token: str) -> InvitationInfoResponse:
        """Get invitation info for accept-invite page.

        Args:
            token: The invitation token.

        Returns:
            Invitation info for display.

        Raises:
            NotFoundError: If invitation not found.
            ValidationError: If invitation is expired or already used.
        """
        result = await self.db.execute(
            select(TeamInvitation)
            .options(
                selectinload(TeamInvitation.organization),
                selectinload(TeamInvitation.created_by),
            )
            .where(TeamInvitation.token == token)
        )
        invitation = result.scalar_one_or_none()

        if not invitation:
            raise NotFoundError("Invitation", token)

        await self._validate_pending_invitation(invitation)

        return InvitationInfoResponse(
            email=invitation.email,
            organization_name=invitation.organization.name,
            inviter_name=invitation.created_by.full_name,
            role=invitation.role,
            expires_at=invitation.expires_at,
        )

    async def accept_invitation(
        self,
        token: str,
        password: str,
        full_name: str | None = None,
    ) -> tuple[User, TokenResponse]:
        """Accept a team invitation and create user account.

        Args:
            token: The invitation token.
            password: Password for the new account.
            full_name: Optional full name for the user.

        Returns:
            A tuple of (User, TokenResponse).

        Raises:
            NotFoundError: If invitation not found.
            ValidationError: If invitation is expired or already used.
            DuplicateError: If user already exists.
        """
        result = await self.db.execute(select(TeamInvitation).where(TeamInvitation.token == token))
        invitation = result.scalar_one_or_none()

        if not invitation:
            raise NotFoundError("Invitation", token)

        await self._validate_pending_invitation(invitation)

        # Check if user already exists
        existing_user = await self.get_user_by_email(invitation.email)
        if existing_user:
            raise DuplicateError("User", "email", invitation.email)

        # Create user
        user = User(
            email=invitation.email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            organization_id=invitation.organization_id,
            role=invitation.role,
            email_verified=True,  # Email is verified through invitation
        )
        self.db.add(user)

        # Update invitation status
        invitation.status = InvitationStatus.ACCEPTED
        await self.db.flush()

        return user, self.create_tokens(user)

    async def list_pending_invitations(
        self,
        organization_id: UUID,
    ) -> list[TeamInvitation]:
        """List pending invitations for an organization.

        Args:
            organization_id: The organization ID.

        Returns:
            List of pending TeamInvitations.
        """
        result = await self.db.execute(
            select(TeamInvitation)
            .where(
                TeamInvitation.organization_id == organization_id,
                TeamInvitation.status == InvitationStatus.PENDING,
            )
            .order_by(TeamInvitation.created_at.desc())
        )
        return list(result.scalars().all())

    async def cancel_invitation(
        self,
        invitation_id: UUID,
        organization_id: UUID,
    ) -> None:
        """Cancel a pending invitation.

        Args:
            invitation_id: The invitation ID.
            organization_id: The organization ID (for tenant isolation).

        Raises:
            NotFoundError: If invitation not found.
        """
        result = await self.db.execute(
            select(TeamInvitation).where(
                TeamInvitation.id == invitation_id,
                TeamInvitation.organization_id == organization_id,
                TeamInvitation.status == InvitationStatus.PENDING,
            )
        )
        invitation = result.scalar_one_or_none()

        if not invitation:
            raise NotFoundError("Invitation", invitation_id)

        await self.db.delete(invitation)
        await self.db.flush()

    # =========================================================================
    # User Management Methods (Admin)
    # =========================================================================

    async def list_organization_users(
        self,
        organization_id: UUID,
    ) -> OrganizationUsersResponse:
        """List all users in an organization.

        Args:
            organization_id: The organization ID.

        Returns:
            OrganizationUsersResponse with users list and counts.
        """
        # Get users
        result = await self.db.execute(
            select(User)
            .where(User.organization_id == organization_id)
            .order_by(User.created_at.desc())
        )
        users = list(result.scalars().all())

        # Count pending invitations
        inv_result = await self.db.execute(
            select(func.count(TeamInvitation.id)).where(
                TeamInvitation.organization_id == organization_id,
                TeamInvitation.status == InvitationStatus.PENDING,
            )
        )
        pending_count = inv_result.scalar() or 0

        return OrganizationUsersResponse(
            users=[UserListResponse.model_validate(u) for u in users],
            total=len(users),
            pending_invitations=pending_count,
        )

    async def update_user_role(
        self,
        user_id: UUID,
        new_role: UserRole,
        organization_id: UUID,
        current_user: User,
    ) -> User:
        """Update a user's role.

        Args:
            user_id: The user ID to update.
            new_role: The new role to assign.
            organization_id: The organization ID (for tenant isolation).
            current_user: The user performing the action.

        Returns:
            The updated User.

        Raises:
            NotFoundError: If user not found.
            ForbiddenError: If trying to modify own role or last admin.
        """
        result = await self.db.execute(
            select(User).where(
                User.id == user_id,
                User.organization_id == organization_id,
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User", user_id)

        # Prevent self-demotion
        if user.id == current_user.id:
            raise ForbiddenError("You cannot change your own role")

        # Check if removing last admin
        if user.role == UserRole.ADMIN and new_role != UserRole.ADMIN:
            admin_count_result = await self.db.execute(
                select(func.count(User.id)).where(
                    User.organization_id == organization_id,
                    User.role == UserRole.ADMIN,
                )
            )
            admin_count = admin_count_result.scalar() or 0
            if admin_count <= 1:
                raise ForbiddenError("Cannot remove the last admin from the organization")

        user.role = new_role
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def deactivate_user(
        self,
        user_id: UUID,
        organization_id: UUID,
        current_user: User,
    ) -> User:
        """Deactivate a user account.

        Args:
            user_id: The user ID to deactivate.
            organization_id: The organization ID (for tenant isolation).
            current_user: The user performing the action.

        Returns:
            The deactivated User.

        Raises:
            NotFoundError: If user not found.
            ForbiddenError: If trying to deactivate self.
        """
        result = await self.db.execute(
            select(User).where(
                User.id == user_id,
                User.organization_id == organization_id,
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User", user_id)

        if user.id == current_user.id:
            raise ForbiddenError("You cannot deactivate your own account")

        user.is_active = False
        await self.db.flush()
        await self.db.refresh(user)

        # Invalidate all tokens for the deactivated user
        await token_blacklist.invalidate_user_tokens(str(user.id))

        return user

    async def reactivate_user(
        self,
        user_id: UUID,
        organization_id: UUID,
    ) -> User:
        """Reactivate a user account.

        Args:
            user_id: The user ID to reactivate.
            organization_id: The organization ID (for tenant isolation).

        Returns:
            The reactivated User.

        Raises:
            NotFoundError: If user not found.
        """
        result = await self.db.execute(
            select(User).where(
                User.id == user_id,
                User.organization_id == organization_id,
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User", user_id)

        user.is_active = True
        await self.db.flush()
        await self.db.refresh(user)
        return user

    # =========================================================================
    # Onboarding Methods
    # =========================================================================

    async def complete_onboarding(self, user: User) -> User:
        """Mark user's onboarding as complete.

        Args:
            user: The user to update.

        Returns:
            The updated User.
        """
        user.onboarding_completed = True
        user.onboarding_completed_at = datetime.now(UTC)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    # =========================================================================
    # GDPR Compliance Methods
    # =========================================================================

    async def export_user_data(self, user: User) -> GDPRDataExport:
        """Export all user and organization data for GDPR compliance.

        Args:
            user: The user requesting data export.

        Returns:
            GDPRDataExport containing all user-related data.
        """
        from paper_scraper.modules.alerts.models import Alert
        from paper_scraper.modules.papers.models import Paper
        from paper_scraper.modules.projects.models import Project
        from paper_scraper.modules.saved_searches.models import SavedSearch

        # Get user with organization
        user_with_org = await self.get_user_with_organization(user.id)
        if not user_with_org:
            raise NotFoundError("User", user.id)

        org_id = user.organization_id

        # Count related entities
        papers_result = await self.db.execute(
            select(func.count(Paper.id)).where(Paper.organization_id == org_id)
        )
        papers_count = papers_result.scalar() or 0

        projects_result = await self.db.execute(
            select(func.count(Project.id)).where(Project.organization_id == org_id)
        )
        projects_count = projects_result.scalar() or 0

        searches_result = await self.db.execute(
            select(func.count(SavedSearch.id)).where(SavedSearch.organization_id == org_id)
        )
        searches_count = searches_result.scalar() or 0

        alerts_result = await self.db.execute(
            select(func.count(Alert.id)).where(Alert.organization_id == org_id)
        )
        alerts_count = alerts_result.scalar() or 0

        # Build full data export
        data = {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "preferences": user.preferences,
                "email_verified": user.email_verified,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat(),
            },
            "organization": {
                "id": str(user_with_org.organization.id),
                "name": user_with_org.organization.name,
                "type": user_with_org.organization.type.value,
                "subscription_tier": user_with_org.organization.subscription_tier.value,
                "settings": user_with_org.organization.settings,
                "created_at": user_with_org.organization.created_at.isoformat(),
            },
            "summary": {
                "papers_count": papers_count,
                "projects_count": projects_count,
                "saved_searches_count": searches_count,
                "alerts_count": alerts_count,
            },
        }

        return GDPRDataExport(
            user=UserResponse.model_validate(user),
            organization=OrganizationResponse.model_validate(user_with_org.organization),
            export_date=datetime.now(UTC),
            papers_count=papers_count,
            projects_count=projects_count,
            saved_searches_count=searches_count,
            alerts_count=alerts_count,
            data=data,
        )

    async def delete_account(
        self,
        user: User,
        password: str,
        delete_organization: bool = False,
    ) -> None:
        """Delete user account and optionally the organization.

        GDPR Article 17: Right to erasure ("right to be forgotten").

        Args:
            user: The user requesting account deletion.
            password: Current password for verification.
            delete_organization: If True and user is sole admin, delete org too.

        Raises:
            ValidationError: If password is incorrect.
            ForbiddenError: If user is sole admin and delete_organization is False.
        """
        # Verify password
        if not verify_password(password, user.hashed_password):
            raise ValidationError("Incorrect password", field="password")

        # Check if user is the sole admin
        admin_count_result = await self.db.execute(
            select(func.count(User.id)).where(
                User.organization_id == user.organization_id,
                User.role == UserRole.ADMIN,
                User.is_active is True,
            )
        )
        admin_count = admin_count_result.scalar() or 0

        if user.role == UserRole.ADMIN and admin_count == 1:
            if not delete_organization:
                raise ForbiddenError(
                    "You are the only admin. Set delete_organization=true to delete "
                    "the entire organization, or transfer admin role to another user first."
                )
            # Delete entire organization (cascades to all data)
            org = await self.get_organization(user.organization_id)
            if org:
                await self.db.delete(org)
        else:
            # Just delete the user
            await self.db.delete(user)

        await self.db.flush()

    async def update_branding(
        self,
        org_id: UUID,
        branding_update: dict,
    ) -> Organization:
        """Update organization branding settings.

        Merges the provided branding keys into existing branding dict.

        Args:
            org_id: Organization ID.
            branding_update: Dict of branding fields to update.

        Returns:
            Updated organization.

        Raises:
            NotFoundError: If organization not found.
        """
        org = await self.get_organization(org_id)
        if not org:
            raise NotFoundError("Organization", str(org_id))

        current_branding = dict(org.branding) if org.branding else {}
        current_branding.update(branding_update)
        org.branding = current_branding
        await self.db.flush()
        await self.db.refresh(org)
        return org

    async def upload_logo(
        self,
        org_id: UUID,
        file_content: bytes,
        content_type: str,
        filename: str,
    ) -> Organization:
        """Upload organization logo to storage and update branding.

        Args:
            org_id: Organization ID.
            file_content: Logo file content bytes.
            content_type: MIME type of the logo.
            filename: Original filename.

        Returns:
            Updated organization with logo_url in branding.

        Raises:
            NotFoundError: If organization not found.
        """
        from paper_scraper.core.storage import StorageService

        org = await self.get_organization(org_id)
        if not org:
            raise NotFoundError("Organization", str(org_id))

        # Determine extension from content type
        ext_map = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/webp": ".webp",
        }
        ext = ext_map.get(content_type, ".png")
        key = f"orgs/{org_id}/logo{ext}"

        storage = StorageService()
        await asyncio.to_thread(storage.upload_file, file_content, key, content_type)
        # Generate a pre-signed URL (24h max) for the logo
        # TODO: Consider a proxy endpoint for permanent logo URLs
        logo_url = await asyncio.to_thread(storage.get_download_url, key, expires_in=24 * 3600)

        current_branding = dict(org.branding) if org.branding else {}
        current_branding["logo_url"] = logo_url
        current_branding["logo_storage_key"] = key
        org.branding = current_branding
        await self.db.flush()
        await self.db.refresh(org)
        return org
