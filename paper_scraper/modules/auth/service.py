"""Service layer for authentication module."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from paper_scraper.core.config import settings
from paper_scraper.core.exceptions import (
    DuplicateError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from paper_scraper.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    validate_token_type,
    verify_password,
)
from paper_scraper.modules.auth.models import Organization, User, UserRole
from paper_scraper.modules.auth.schemas import (
    OrganizationCreate,
    RegisterRequest,
    TokenResponse,
    UserCreate,
    UserUpdate,
)


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
            select(User)
            .options(selectinload(User.organization))
            .where(User.id == user_id)
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
            UnauthorizedError: If credentials are invalid.
        """
        user = await self.get_user_by_email(email)
        if not user:
            raise UnauthorizedError("Invalid email or password")

        if not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedError("User account is deactivated")

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

        try:
            user = await self.get_user_by_id(UUID(user_id))
        except ValueError:
            raise UnauthorizedError("Invalid user ID in token")

        if not user:
            raise UnauthorizedError("User not found")

        if not user.is_active:
            raise UnauthorizedError("User account is deactivated")

        return self.create_tokens(user)
