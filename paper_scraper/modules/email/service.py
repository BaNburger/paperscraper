"""Email service for sending transactional emails using Resend."""

import logging
from typing import Any

import httpx

from paper_scraper.core.config import settings
from paper_scraper.core.exceptions import EmailError

logger = logging.getLogger(__name__)


class EmailService:
    """Email sending service using Resend API."""

    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        self.from_email = settings.EMAIL_FROM_ADDRESS
        self.base_url = "https://api.resend.com"
        self.frontend_url = settings.FRONTEND_URL

    async def send_email(
        self,
        to: str | list[str],
        subject: str,
        html: str,
        text: str | None = None,
    ) -> dict[str, Any]:
        """
        Send an email using Resend API.

        Args:
            to: Recipient email address(es).
            subject: Email subject.
            html: HTML content of the email.
            text: Plain text content (optional).

        Returns:
            Response from Resend API.

        Raises:
            EmailError: If email sending fails.
        """
        if not self.api_key:
            logger.warning("RESEND_API_KEY not configured, skipping email")
            return {"id": "skipped", "message": "Email service not configured"}

        recipient = to[0] if isinstance(to, list) else to
        payload = {
            "from": self.from_email,
            "to": to if isinstance(to, list) else [to],
            "subject": subject,
            "html": html,
        }

        if text:
            payload["text"] = text

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/emails",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code not in (200, 201):
                logger.error(f"Failed to send email to {recipient}: {response.text}")
                raise EmailError(
                    recipient=recipient,
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

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                     line-height: 1.6; color: #1f2937; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
                        padding: 30px; border-radius: 8px 8px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Verify Your Email</h1>
            </div>

            <div style="background: #f9fafb; padding: 24px; border: 1px solid #e5e7eb; border-top: none;">
                <p style="margin-top: 0;">
                    Thank you for signing up for Paper Scraper! Please verify your email address
                    by clicking the button below.
                </p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verify_url}"
                       style="display: inline-block; background: #3b82f6; color: white;
                              padding: 14px 28px; border-radius: 6px; text-decoration: none;
                              font-weight: 600; font-size: 16px;">
                        Verify Email Address
                    </a>
                </div>

                <p style="color: #6b7280; font-size: 14px;">
                    If you didn't create an account with Paper Scraper, you can safely ignore this email.
                </p>

                <p style="color: #6b7280; font-size: 14px;">
                    This link will expire in 24 hours.
                </p>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">

                <p style="color: #9ca3af; font-size: 12px;">
                    If the button doesn't work, copy and paste this link into your browser:
                    <br>
                    <a href="{verify_url}" style="color: #6b7280; word-break: break-all;">
                        {verify_url}
                    </a>
                </p>
            </div>

            <div style="text-align: center; padding: 20px; color: #9ca3af; font-size: 12px;">
                <p>&copy; Paper Scraper. All rights reserved.</p>
            </div>
        </body>
        </html>
        """

        text = f"""
Verify Your Email

Thank you for signing up for Paper Scraper! Please verify your email address by visiting the link below:

{verify_url}

If you didn't create an account with Paper Scraper, you can safely ignore this email.

This link will expire in 24 hours.
        """

        return await self.send_email(
            to=to,
            subject="Verify your Paper Scraper email",
            html=html,
            text=text,
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

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                     line-height: 1.6; color: #1f2937; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
                        padding: 30px; border-radius: 8px 8px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Reset Your Password</h1>
            </div>

            <div style="background: #f9fafb; padding: 24px; border: 1px solid #e5e7eb; border-top: none;">
                <p style="margin-top: 0;">
                    We received a request to reset your password for your Paper Scraper account.
                    Click the button below to create a new password.
                </p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}"
                       style="display: inline-block; background: #f59e0b; color: white;
                              padding: 14px 28px; border-radius: 6px; text-decoration: none;
                              font-weight: 600; font-size: 16px;">
                        Reset Password
                    </a>
                </div>

                <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 6px;
                            padding: 16px; margin: 20px 0;">
                    <p style="margin: 0; color: #92400e; font-size: 14px;">
                        <strong>Security notice:</strong> If you didn't request a password reset,
                        please ignore this email and your password will remain unchanged.
                    </p>
                </div>

                <p style="color: #6b7280; font-size: 14px;">
                    This link will expire in 1 hour for security reasons.
                </p>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">

                <p style="color: #9ca3af; font-size: 12px;">
                    If the button doesn't work, copy and paste this link into your browser:
                    <br>
                    <a href="{reset_url}" style="color: #6b7280; word-break: break-all;">
                        {reset_url}
                    </a>
                </p>
            </div>

            <div style="text-align: center; padding: 20px; color: #9ca3af; font-size: 12px;">
                <p>&copy; Paper Scraper. All rights reserved.</p>
            </div>
        </body>
        </html>
        """

        text = f"""
Reset Your Password

We received a request to reset your password for your Paper Scraper account.

Click the link below to create a new password:
{reset_url}

Security notice: If you didn't request a password reset, please ignore this email and your password will remain unchanged.

This link will expire in 1 hour for security reasons.
        """

        return await self.send_email(
            to=to,
            subject="Reset your Paper Scraper password",
            html=html,
            text=text,
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

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                     line-height: 1.6; color: #1f2937; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                        padding: 30px; border-radius: 8px 8px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">You're Invited!</h1>
            </div>

            <div style="background: #f9fafb; padding: 24px; border: 1px solid #e5e7eb; border-top: none;">
                <p style="margin-top: 0; font-size: 18px;">
                    <strong>{inviter_name}</strong> has invited you to join
                    <strong>{org_name}</strong> on Paper Scraper.
                </p>

                <p>
                    Paper Scraper is an AI-powered platform for discovering and analyzing
                    scientific research with commercial potential.
                </p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{invite_url}"
                       style="display: inline-block; background: #10b981; color: white;
                              padding: 14px 28px; border-radius: 6px; text-decoration: none;
                              font-weight: 600; font-size: 16px;">
                        Accept Invitation
                    </a>
                </div>

                <p style="color: #6b7280; font-size: 14px;">
                    This invitation will expire in 7 days.
                </p>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">

                <p style="color: #9ca3af; font-size: 12px;">
                    If the button doesn't work, copy and paste this link into your browser:
                    <br>
                    <a href="{invite_url}" style="color: #6b7280; word-break: break-all;">
                        {invite_url}
                    </a>
                </p>
            </div>

            <div style="text-align: center; padding: 20px; color: #9ca3af; font-size: 12px;">
                <p>&copy; Paper Scraper. All rights reserved.</p>
            </div>
        </body>
        </html>
        """

        text = f"""
You're Invited!

{inviter_name} has invited you to join {org_name} on Paper Scraper.

Paper Scraper is an AI-powered platform for discovering and analyzing scientific research with commercial potential.

Accept your invitation by visiting:
{invite_url}

This invitation will expire in 7 days.
        """

        return await self.send_email(
            to=to,
            subject=f"You're invited to join {org_name} on Paper Scraper",
            html=html,
            text=text,
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

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                     line-height: 1.6; color: #1f2937; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
                        padding: 30px; border-radius: 8px 8px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Welcome to Paper Scraper!</h1>
            </div>

            <div style="background: #f9fafb; padding: 24px; border: 1px solid #e5e7eb; border-top: none;">
                <p style="margin-top: 0; font-size: 18px;">
                    Hi{(" " + user_name) if user_name else ""},
                </p>

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

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{dashboard_url}"
                       style="display: inline-block; background: #3b82f6; color: white;
                              padding: 14px 28px; border-radius: 6px; text-decoration: none;
                              font-weight: 600; font-size: 16px;">
                        Go to Dashboard
                    </a>
                </div>

                <p style="color: #6b7280; font-size: 14px;">
                    Need help? Check out our documentation or contact support.
                </p>
            </div>

            <div style="text-align: center; padding: 20px; color: #9ca3af; font-size: 12px;">
                <p>&copy; Paper Scraper. All rights reserved.</p>
            </div>
        </body>
        </html>
        """

        text = f"""
Welcome to Paper Scraper!

Hi{(" " + user_name) if user_name else ""},

Thank you for joining Paper Scraper! You're now ready to discover and analyze scientific research with commercial potential.

Get Started:
- Import papers from OpenAlex, PubMed, arXiv, or by DOI
- Score papers with AI across 5 dimensions
- Organize research in KanBan projects
- Set up alerts for new research

Go to your dashboard: {dashboard_url}

Need help? Check out our documentation or contact support.
        """

        return await self.send_email(
            to=to,
            subject="Welcome to Paper Scraper!",
            html=html,
            text=text,
        )


# Singleton instance
email_service = EmailService()
