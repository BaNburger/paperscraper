"""Tests for email service module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from paper_scraper.core.exceptions import EmailError
from paper_scraper.modules.email.service import EmailService

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def email_service():
    """Create an email service instance for testing."""
    return EmailService()


@pytest.fixture
def mock_settings():
    """Mock settings with test values."""
    return {
        "RESEND_API_KEY": "test_api_key",
        "EMAIL_FROM_ADDRESS": "noreply@papersscraper.com",
        "FRONTEND_URL": "http://localhost:3000",
    }


@pytest.fixture
def mock_httpx_response_success():
    """Create a successful mock response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "email_123"}
    mock_response.text = "OK"
    return mock_response


@pytest.fixture
def mock_httpx_response_error():
    """Create an error mock response."""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"error": "Invalid recipient"}
    mock_response.text = "Invalid recipient email"
    return mock_response


# =============================================================================
# send_email Tests
# =============================================================================


class TestSendEmail:
    """Tests for the send_email method."""

    @pytest.mark.asyncio
    async def test_send_email_skipped_without_api_key(self, email_service):
        """Test that email is skipped when API key is not configured."""
        email_service.api_key = None

        result = await email_service.send_email(
            to="test@example.com",
            subject="Test Subject",
            html_content="<p>Test content</p>",
        )

        assert result["id"] == "skipped"
        assert "not configured" in result["message"]

    @pytest.mark.asyncio
    async def test_send_email_success(self, email_service, mock_httpx_response_success):
        """Test successful email sending."""
        email_service.api_key = "test_api_key"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.return_value = mock_httpx_response_success
            mock_client_class.return_value = mock_client

            result = await email_service.send_email(
                to="test@example.com",
                subject="Test Subject",
                html_content="<p>Test content</p>",
            )

            assert result == {"id": "email_123"}
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_with_text_content(self, email_service, mock_httpx_response_success):
        """Test email with both HTML and text content."""
        email_service.api_key = "test_api_key"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.return_value = mock_httpx_response_success
            mock_client_class.return_value = mock_client

            await email_service.send_email(
                to="test@example.com",
                subject="Test Subject",
                html_content="<p>Test content</p>",
                text_content="Test content",
            )

            # Verify text was included in payload
            call_args = mock_client.post.call_args
            assert "text" in call_args.kwargs["json"]

    @pytest.mark.asyncio
    async def test_send_email_to_list(self, email_service, mock_httpx_response_success):
        """Test sending email to multiple recipients."""
        email_service.api_key = "test_api_key"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.return_value = mock_httpx_response_success
            mock_client_class.return_value = mock_client

            await email_service.send_email(
                to=["user1@example.com", "user2@example.com"],
                subject="Test Subject",
                html_content="<p>Test content</p>",
            )

            call_args = mock_client.post.call_args
            assert call_args.kwargs["json"]["to"] == [
                "user1@example.com",
                "user2@example.com",
            ]

    @pytest.mark.asyncio
    async def test_send_email_failure(self, email_service, mock_httpx_response_error):
        """Test email sending failure raises EmailError."""
        email_service.api_key = "test_api_key"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.return_value = mock_httpx_response_error
            mock_client_class.return_value = mock_client

            with pytest.raises(EmailError) as exc_info:
                await email_service.send_email(
                    to="test@example.com",
                    subject="Test Subject",
                    html_content="<p>Test content</p>",
                )

            assert exc_info.value.recipient == "test@example.com"
            assert exc_info.value.status_code == 400


# =============================================================================
# Verification Email Tests
# =============================================================================


class TestSendVerificationEmail:
    """Tests for the send_verification_email method."""

    @pytest.mark.asyncio
    async def test_send_verification_email_calls_send_email(self, email_service):
        """Test that verification email calls send_email with correct params."""
        email_service.send_email = AsyncMock(return_value={"id": "email_123"})

        result = await email_service.send_verification_email(
            to="test@example.com",
            token="verification_token_123",
        )

        assert result == {"id": "email_123"}
        email_service.send_email.assert_called_once()

        # Verify call arguments
        call_args = email_service.send_email.call_args
        assert call_args.kwargs["to"] == "test@example.com"
        assert "Verify" in call_args.kwargs["subject"]
        assert "verification_token_123" in call_args.kwargs["html_content"]
        assert "verification_token_123" in call_args.kwargs["text_content"]

    @pytest.mark.asyncio
    async def test_verification_email_contains_verify_url(self, email_service):
        """Test that verification email contains the correct URL."""
        email_service.send_email = AsyncMock(return_value={"id": "email_123"})
        email_service.frontend_url = "http://localhost:3000"

        await email_service.send_verification_email(
            to="test@example.com",
            token="token123",
        )

        call_args = email_service.send_email.call_args
        expected_url = "http://localhost:3000/verify-email?token=token123"
        assert expected_url in call_args.kwargs["html_content"]


# =============================================================================
# Password Reset Email Tests
# =============================================================================


class TestSendPasswordResetEmail:
    """Tests for the send_password_reset_email method."""

    @pytest.mark.asyncio
    async def test_send_password_reset_email_calls_send_email(self, email_service):
        """Test that password reset email calls send_email with correct params."""
        email_service.send_email = AsyncMock(return_value={"id": "email_123"})

        result = await email_service.send_password_reset_email(
            to="test@example.com",
            token="reset_token_123",
        )

        assert result == {"id": "email_123"}
        email_service.send_email.assert_called_once()

        # Verify call arguments
        call_args = email_service.send_email.call_args
        assert call_args.kwargs["to"] == "test@example.com"
        assert "Reset" in call_args.kwargs["subject"]
        assert "reset_token_123" in call_args.kwargs["html_content"]

    @pytest.mark.asyncio
    async def test_password_reset_email_contains_reset_url(self, email_service):
        """Test that password reset email contains the correct URL."""
        email_service.send_email = AsyncMock(return_value={"id": "email_123"})
        email_service.frontend_url = "http://localhost:3000"

        await email_service.send_password_reset_email(
            to="test@example.com",
            token="reset123",
        )

        call_args = email_service.send_email.call_args
        expected_url = "http://localhost:3000/reset-password?token=reset123"
        assert expected_url in call_args.kwargs["html_content"]


# =============================================================================
# Team Invite Email Tests
# =============================================================================


class TestSendTeamInviteEmail:
    """Tests for the send_team_invite_email method."""

    @pytest.mark.asyncio
    async def test_send_team_invite_email_calls_send_email(self, email_service):
        """Test that team invite email calls send_email with correct params."""
        email_service.send_email = AsyncMock(return_value={"id": "email_123"})

        result = await email_service.send_team_invite_email(
            to="newuser@example.com",
            token="invite_token_123",
            inviter_name="John Admin",
            org_name="Acme Corp",
        )

        assert result == {"id": "email_123"}
        email_service.send_email.assert_called_once()

        # Verify call arguments
        call_args = email_service.send_email.call_args
        assert call_args.kwargs["to"] == "newuser@example.com"
        assert "Acme Corp" in call_args.kwargs["subject"]
        assert "John Admin" in call_args.kwargs["html_content"]
        assert "Acme Corp" in call_args.kwargs["html_content"]
        assert "invite_token_123" in call_args.kwargs["html_content"]

    @pytest.mark.asyncio
    async def test_team_invite_email_contains_invite_url(self, email_service):
        """Test that team invite email contains the correct URL."""
        email_service.send_email = AsyncMock(return_value={"id": "email_123"})
        email_service.frontend_url = "http://localhost:3000"

        await email_service.send_team_invite_email(
            to="newuser@example.com",
            token="invite123",
            inviter_name="Admin",
            org_name="Test Org",
        )

        call_args = email_service.send_email.call_args
        expected_url = "http://localhost:3000/accept-invite?token=invite123"
        assert expected_url in call_args.kwargs["html_content"]


# =============================================================================
# Welcome Email Tests
# =============================================================================


class TestSendWelcomeEmail:
    """Tests for the send_welcome_email method."""

    @pytest.mark.asyncio
    async def test_send_welcome_email_calls_send_email(self, email_service):
        """Test that welcome email calls send_email with correct params."""
        email_service.send_email = AsyncMock(return_value={"id": "email_123"})

        result = await email_service.send_welcome_email(
            to="newuser@example.com",
            user_name="Jane",
        )

        assert result == {"id": "email_123"}
        email_service.send_email.assert_called_once()

        # Verify call arguments
        call_args = email_service.send_email.call_args
        assert call_args.kwargs["to"] == "newuser@example.com"
        assert "Welcome" in call_args.kwargs["subject"]
        assert "Jane" in call_args.kwargs["html_content"]

    @pytest.mark.asyncio
    async def test_welcome_email_without_name(self, email_service):
        """Test welcome email when user name is empty."""
        email_service.send_email = AsyncMock(return_value={"id": "email_123"})

        await email_service.send_welcome_email(
            to="newuser@example.com",
            user_name="",
        )

        call_args = email_service.send_email.call_args
        # Should still work without name
        assert "Hi" in call_args.kwargs["html_content"]

    @pytest.mark.asyncio
    async def test_welcome_email_contains_dashboard_url(self, email_service):
        """Test that welcome email contains the dashboard URL."""
        email_service.send_email = AsyncMock(return_value={"id": "email_123"})
        email_service.frontend_url = "http://localhost:3000"

        await email_service.send_welcome_email(
            to="newuser@example.com",
            user_name="Test User",
        )

        call_args = email_service.send_email.call_args
        expected_url = "http://localhost:3000/dashboard"
        assert expected_url in call_args.kwargs["html_content"]


# =============================================================================
# Email Content Tests
# =============================================================================


class TestEmailContent:
    """Tests for email content and formatting."""

    @pytest.mark.asyncio
    async def test_verification_email_has_html_and_text(self, email_service):
        """Test that verification email includes both HTML and plain text."""
        email_service.send_email = AsyncMock(return_value={"id": "email_123"})

        await email_service.send_verification_email(
            to="test@example.com",
            token="token",
        )

        call_args = email_service.send_email.call_args
        assert "html_content" in call_args.kwargs
        assert "text_content" in call_args.kwargs
        assert "<html>" in call_args.kwargs["html_content"]

    @pytest.mark.asyncio
    async def test_password_reset_email_has_security_notice(self, email_service):
        """Test that password reset email includes security notice."""
        email_service.send_email = AsyncMock(return_value={"id": "email_123"})

        await email_service.send_password_reset_email(
            to="test@example.com",
            token="token",
        )

        call_args = email_service.send_email.call_args
        assert "Security notice" in call_args.kwargs["html_content"]
        assert "Security notice" in call_args.kwargs["text_content"]

    @pytest.mark.asyncio
    async def test_invite_email_expiration_notice(self, email_service):
        """Test that invite email mentions expiration."""
        email_service.send_email = AsyncMock(return_value={"id": "email_123"})

        await email_service.send_team_invite_email(
            to="test@example.com",
            token="token",
            inviter_name="Admin",
            org_name="Test Org",
        )

        call_args = email_service.send_email.call_args
        assert "7 days" in call_args.kwargs["html_content"]


# =============================================================================
# Integration-style Tests (with mock external service)
# =============================================================================


class TestEmailServiceIntegration:
    """Integration-style tests simulating full email flow."""

    @pytest.mark.asyncio
    async def test_full_verification_flow(self, email_service, mock_httpx_response_success):
        """Test complete verification email flow."""
        email_service.api_key = "test_api_key"
        email_service.frontend_url = "http://localhost:3000"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.return_value = mock_httpx_response_success
            mock_client_class.return_value = mock_client

            result = await email_service.send_verification_email(
                to="user@example.com",
                token="verify_token_abc123",
            )

            assert result == {"id": "email_123"}

            # Verify API was called with correct structure
            call_args = mock_client.post.call_args
            payload = call_args.kwargs["json"]
            assert payload["to"] == ["user@example.com"]
            assert "Verify" in payload["subject"]
            assert "verify_token_abc123" in payload["html"]

    @pytest.mark.asyncio
    async def test_full_password_reset_flow(self, email_service, mock_httpx_response_success):
        """Test complete password reset email flow."""
        email_service.api_key = "test_api_key"
        email_service.frontend_url = "http://localhost:3000"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.return_value = mock_httpx_response_success
            mock_client_class.return_value = mock_client

            result = await email_service.send_password_reset_email(
                to="user@example.com",
                token="reset_token_xyz789",
            )

            assert result == {"id": "email_123"}
