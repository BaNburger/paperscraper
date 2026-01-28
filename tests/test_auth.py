"""Tests for authentication module."""

import pytest
from httpx import AsyncClient

from paper_scraper.modules.auth.models import User


class TestHealthCheck:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test that health check endpoint returns healthy status."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data


class TestRegistration:
    """Tests for user registration."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "full_name": "New User",
                "organization_name": "New Organization",
                "organization_type": "university",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test registration with existing email fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "securepassword123",
                "full_name": "Duplicate User",
                "organization_name": "Another Org",
                "organization_type": "university",
            },
        )
        assert response.status_code == 409
        data = response.json()
        assert data["error"] == "DUPLICATE"

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email format fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "password": "securepassword123",
                "full_name": "Invalid User",
                "organization_name": "Some Org",
                "organization_type": "university",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: AsyncClient):
        """Test registration with too short password fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "shortpass@example.com",
                "password": "short",
                "full_name": "Short Pass User",
                "organization_name": "Some Org",
                "organization_type": "university",
            },
        )
        assert response.status_code == 422


class TestLogin:
    """Tests for user login."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login returns tokens."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """Test login with wrong password fails."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "UNAUTHORIZED"

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent email fails."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "somepassword123",
            },
        )
        assert response.status_code == 401


class TestCurrentUser:
    """Tests for current user endpoints."""

    @pytest.mark.asyncio
    async def test_get_current_user(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
    ):
        """Test getting current user profile."""
        response = await authenticated_client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert "organization" in data

    @pytest.mark.asyncio
    async def test_get_current_user_unauthenticated(self, client: AsyncClient):
        """Test getting current user without auth fails."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_current_user(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
    ):
        """Test updating current user profile."""
        response = await authenticated_client.patch(
            "/api/v1/auth/me",
            json={
                "full_name": "Updated Name",
                "preferences": {"theme": "dark"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["preferences"]["theme"] == "dark"


class TestTokenRefresh:
    """Tests for token refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, test_user: User):
        """Test refreshing tokens with valid refresh token."""
        # First login to get tokens
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123",
            },
        )
        tokens = login_response.json()

        # Use refresh token to get new tokens
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refreshing with invalid token fails."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        assert response.status_code == 401


class TestChangePassword:
    """Tests for password change endpoint."""

    @pytest.mark.asyncio
    async def test_change_password_success(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test changing password with correct current password."""
        response = await authenticated_client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "testpassword123",
                "new_password": "newpassword456",
            },
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test changing password with wrong current password fails."""
        response = await authenticated_client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword456",
            },
        )
        assert response.status_code == 422
