"""Email service for sending transactional emails using Resend."""

import html as html_escape
import logging
from typing import Any

import httpx

from paper_scraper.core.config import settings
from paper_scraper.core.exceptions import EmailError

logger = logging.getLogger(__name__)

# Common email styles
BODY_STYLE = (
    "font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; "
    "line-height: 1.6; color: #1f2937; max-width: 600px; margin: 0 auto; padding: 20px;"
)
CONTENT_STYLE = "background: #f9fafb; padding: 24px; border: 1px solid #e5e7eb; border-top: none;"
BUTTON_STYLE = (
    "display: inline-block; color: white; padding: 14px 28px; "
    "border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 16px;"
)
MUTED_TEXT_STYLE = "color: #6b7280; font-size: 14px;"
FOOTER_TEXT_STYLE = "color: #9ca3af; font-size: 12px;"


def _build_header(title: str, gradient_colors: tuple[str, str]) -> str:
    """Build email header with gradient background."""
    return f"""
    <div style="background: linear-gradient(135deg, {gradient_colors[0]} 0%, {gradient_colors[1]} 100%);
                padding: 30px; border-radius: 8px 8px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 24px;">{title}</h1>
    </div>"""


def _build_button(url: str, text: str, color: str) -> str:
    """Build centered call-to-action button."""
    return f"""
    <div style="text-align: center; margin: 30px 0;">
        <a href="{url}" style="{BUTTON_STYLE} background: {color};">{text}</a>
    </div>"""


def _build_fallback_link(url: str) -> str:
    """Build fallback link section for email clients that don't render buttons."""
    return f"""
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
    <p style="{FOOTER_TEXT_STYLE}">
        If the button doesn't work, copy and paste this link into your browser:
        <br>
        <a href="{url}" style="color: #6b7280; word-break: break-all;">{url}</a>
    </p>"""


def _build_footer() -> str:
    """Build common email footer."""
    return f"""
    <div style="text-align: center; padding: 20px; {FOOTER_TEXT_STYLE}">
        <p>&copy; Paper Scraper. All rights reserved.</p>
    </div>"""


def _wrap_html(content: str) -> str:
    """Wrap content in complete HTML document structure."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="{BODY_STYLE}">
{content}
{_build_footer()}
</body>
</html>"""


class EmailService:
    """Email sending service using Resend API."""

    RESEND_API_URL = "https://api.resend.com"

    def __init__(self) -> None:
        self.api_key = settings.RESEND_API_KEY
        self.from_email = settings.EMAIL_FROM_ADDRESS
        self.frontend_url = settings.FRONTEND_URL

    async def send_email(
        self,
        to: str | list[str],
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> dict[str, Any]:
        """
        Send an email using Resend API.

        Args:
            to: Recipient email address(es).
            subject: Email subject.
            html_content: HTML content of the email.
            text_content: Plain text content (optional).

        Returns:
            Response from Resend API.

        Raises:
            EmailError: If email sending fails.
        """
        if not self.api_key:
            logger.warning("RESEND_API_KEY not configured, skipping email")
            return {"id": "skipped", "message": "Email service not configured"}

        recipients = to if isinstance(to, list) else [to]
        payload: dict[str, Any] = {
            "from": self.from_email,
            "to": recipients,
            "subject": subject,
            "html": html_content,
        }

        if text_content:
            payload["text"] = text_content

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.RESEND_API_URL}/emails",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code not in (200, 201):
                logger.error(f"Failed to send email to {recipients[0]}: {response.text}")
                raise EmailError(
                    recipient=recipients[0],
                    reason=response.text,
                    status_code=response.status_code,
                )

            return response.json()

    async def send_verification_email(self, to: str, token: str) -> dict[str, Any]:
        """
        Send email verification link.

        Args:
            to: Recipient email address.
            token: Verification token.

        Returns:
            Response from email service.
        """
        verify_url = f"{self.frontend_url}/verify-email?token={token}"

        content = f"""
{_build_header("Verify Your Email", ("#3b82f6", "#1d4ed8"))}
<div style="{CONTENT_STYLE}">
    <p style="margin-top: 0;">
        Thank you for signing up for Paper Scraper! Please verify your email address
        by clicking the button below.
    </p>
    {_build_button(verify_url, "Verify Email Address", "#3b82f6")}
    <p style="{MUTED_TEXT_STYLE}">
        If you didn't create an account with Paper Scraper, you can safely ignore this email.
    </p>
    <p style="{MUTED_TEXT_STYLE}">This link will expire in 24 hours.</p>
    {_build_fallback_link(verify_url)}
</div>"""

        text_content = f"""Verify Your Email

Thank you for signing up for Paper Scraper! Please verify your email address by visiting the link below:

{verify_url}

If you didn't create an account with Paper Scraper, you can safely ignore this email.

This link will expire in 24 hours."""

        return await self.send_email(
            to=to,
            subject="Verify your Paper Scraper email",
            html_content=_wrap_html(content),
            text_content=text_content,
        )

    async def send_password_reset_email(self, to: str, token: str) -> dict[str, Any]:
        """
        Send password reset link.

        Args:
            to: Recipient email address.
            token: Password reset token.

        Returns:
            Response from email service.
        """
        reset_url = f"{self.frontend_url}/reset-password?token={token}"

        warning_box = """
    <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 6px;
                padding: 16px; margin: 20px 0;">
        <p style="margin: 0; color: #92400e; font-size: 14px;">
            <strong>Security notice:</strong> If you didn't request a password reset,
            please ignore this email and your password will remain unchanged.
        </p>
    </div>"""

        content = f"""
{_build_header("Reset Your Password", ("#f59e0b", "#d97706"))}
<div style="{CONTENT_STYLE}">
    <p style="margin-top: 0;">
        We received a request to reset your password for your Paper Scraper account.
        Click the button below to create a new password.
    </p>
    {_build_button(reset_url, "Reset Password", "#f59e0b")}
    {warning_box}
    <p style="{MUTED_TEXT_STYLE}">This link will expire in 1 hour for security reasons.</p>
    {_build_fallback_link(reset_url)}
</div>"""

        text_content = f"""Reset Your Password

We received a request to reset your password for your Paper Scraper account.

Click the link below to create a new password:
{reset_url}

Security notice: If you didn't request a password reset, please ignore this email and your password will remain unchanged.

This link will expire in 1 hour for security reasons."""

        return await self.send_email(
            to=to,
            subject="Reset your Paper Scraper password",
            html_content=_wrap_html(content),
            text_content=text_content,
        )

    async def send_team_invite_email(
        self,
        to: str,
        token: str,
        inviter_name: str,
        org_name: str,
    ) -> dict[str, Any]:
        """
        Send team invitation email.

        Args:
            to: Recipient email address.
            token: Invitation token.
            inviter_name: Name of the person who sent the invitation.
            org_name: Name of the organization.

        Returns:
            Response from email service.
        """
        invite_url = f"{self.frontend_url}/accept-invite?token={token}"

        safe_inviter_name = html_escape.escape(inviter_name)
        safe_org_name = html_escape.escape(org_name)

        content = f"""
{_build_header("You're Invited!", ("#10b981", "#059669"))}
<div style="{CONTENT_STYLE}">
    <p style="margin-top: 0; font-size: 18px;">
        <strong>{safe_inviter_name}</strong> has invited you to join
        <strong>{safe_org_name}</strong> on Paper Scraper.
    </p>
    <p>
        Paper Scraper is an AI-powered platform for discovering and analyzing
        scientific research with commercial potential.
    </p>
    {_build_button(invite_url, "Accept Invitation", "#10b981")}
    <p style="{MUTED_TEXT_STYLE}">This invitation will expire in 7 days.</p>
    {_build_fallback_link(invite_url)}
</div>"""

        text_content = f"""You're Invited!

{inviter_name} has invited you to join {org_name} on Paper Scraper.

Paper Scraper is an AI-powered platform for discovering and analyzing scientific research with commercial potential.

Accept your invitation by visiting:
{invite_url}

This invitation will expire in 7 days."""

        return await self.send_email(
            to=to,
            subject=f"You're invited to join {safe_org_name} on Paper Scraper",
            html_content=_wrap_html(content),
            text_content=text_content,
        )

    async def send_welcome_email(self, to: str, user_name: str) -> dict[str, Any]:
        """
        Send welcome email after successful registration.

        Args:
            to: Recipient email address.
            user_name: Name of the new user.

        Returns:
            Response from email service.
        """
        dashboard_url = f"{self.frontend_url}/dashboard"

        safe_user_name = html_escape.escape(user_name) if user_name else ""
        greeting = f"Hi {safe_user_name}," if safe_user_name else "Hi,"

        content = f"""
{_build_header("Welcome to Paper Scraper!", ("#3b82f6", "#1d4ed8"))}
<div style="{CONTENT_STYLE}">
    <p style="margin-top: 0; font-size: 18px;">{greeting}</p>
    <p>
        Thank you for joining Paper Scraper! You're now ready to discover and analyze
        scientific research with commercial potential.
    </p>
    <h3 style="color: #1f2937;">Get Started:</h3>
    <ul style="color: #4b5563;">
        <li>Import papers from OpenAlex, PubMed, arXiv, or by DOI</li>
        <li>Score papers with AI across 5 dimensions</li>
        <li>Organize research in KanBan projects</li>
        <li>Set up alerts for new research</li>
    </ul>
    {_build_button(dashboard_url, "Go to Dashboard", "#3b82f6")}
    <p style="{MUTED_TEXT_STYLE}">Need help? Check out our documentation or contact support.</p>
</div>"""

        greeting_text = f"Hi {user_name}," if user_name else "Hi,"
        text_content = f"""Welcome to Paper Scraper!

{greeting_text}

Thank you for joining Paper Scraper! You're now ready to discover and analyze scientific research with commercial potential.

Get Started:
- Import papers from OpenAlex, PubMed, arXiv, or by DOI
- Score papers with AI across 5 dimensions
- Organize research in KanBan projects
- Set up alerts for new research

Go to your dashboard: {dashboard_url}

Need help? Check out our documentation or contact support."""

        return await self.send_email(
            to=to,
            subject="Welcome to Paper Scraper!",
            html_content=_wrap_html(content),
            text_content=text_content,
        )


# Singleton instance
email_service = EmailService()
