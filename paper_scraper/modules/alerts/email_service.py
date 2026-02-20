"""Email service for sending alert notifications."""

import logging
from typing import Any

import httpx

from paper_scraper.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email sending service using Resend API."""

    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        self.from_email = settings.EMAIL_FROM_ADDRESS
        self.base_url = "https://api.resend.com"

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
            Exception: If email sending fails.
        """
        if not self.api_key:
            logger.warning("RESEND_API_KEY not configured, skipping email")
            return {"id": "skipped", "message": "Email service not configured"}

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
                logger.error(f"Failed to send email: {response.text}")
                raise Exception(f"Email sending failed: {response.text}")

            return response.json()

    async def send_alert_notification(
        self,
        to: str,
        alert_name: str,
        search_query: str,
        new_papers_count: int,
        papers: list[dict[str, Any]],
        view_url: str,
    ) -> dict[str, Any]:
        """
        Send an alert notification email.

        Args:
            to: Recipient email.
            alert_name: Name of the alert.
            search_query: The search query that triggered this.
            new_papers_count: Number of new papers found.
            papers: List of paper details to include.
            view_url: URL to view full results.

        Returns:
            Response from email service.
        """
        subject = f"[Paper Scraper] {new_papers_count} new paper(s) for '{alert_name}'"

        # Build paper list HTML
        paper_items = ""
        for paper in papers[:10]:  # Limit to 10 papers in email
            paper_items += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #eee;">
                    <a href="{settings.FRONTEND_URL}/papers/{paper.get("id")}"
                       style="color: #2563eb; text-decoration: none; font-weight: 500;">
                        {paper.get("title", "Untitled")}
                    </a>
                    <br>
                    <span style="color: #6b7280; font-size: 14px;">
                        {paper.get("journal", "Unknown Journal")}
                        {" - " + paper.get("publication_date", "")[:10] if paper.get("publication_date") else ""}
                    </span>
                </td>
            </tr>
            """

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
                <h1 style="color: white; margin: 0; font-size: 24px;">New Papers Found</h1>
            </div>

            <div style="background: #f9fafb; padding: 24px; border: 1px solid #e5e7eb; border-top: none;">
                <p style="margin-top: 0;">
                    Your saved search <strong>"{alert_name}"</strong> found
                    <strong>{new_papers_count} new paper(s)</strong>.
                </p>

                <p style="color: #6b7280; font-size: 14px;">
                    Search query: <em>{search_query}</em>
                </p>

                <table style="width: 100%; border-collapse: collapse; background: white;
                              border-radius: 8px; overflow: hidden; margin: 20px 0;">
                    <tbody>
                        {paper_items}
                    </tbody>
                </table>

                {f'<p style="color: #6b7280; font-size: 14px;">...and {new_papers_count - 10} more papers</p>' if new_papers_count > 10 else ""}

                <div style="text-align: center; margin-top: 24px;">
                    <a href="{view_url}"
                       style="display: inline-block; background: #3b82f6; color: white;
                              padding: 12px 24px; border-radius: 6px; text-decoration: none;
                              font-weight: 500;">
                        View All Results
                    </a>
                </div>
            </div>

            <div style="text-align: center; padding: 20px; color: #9ca3af; font-size: 12px;">
                <p>
                    You received this email because you have alerts enabled for this saved search.
                    <br>
                    <a href="{settings.FRONTEND_URL}/settings/alerts" style="color: #6b7280;">
                        Manage your alert settings
                    </a>
                </p>
            </div>
        </body>
        </html>
        """

        text = f"""
New Papers Found

Your saved search "{alert_name}" found {new_papers_count} new paper(s).

Search query: {search_query}

Papers:
{chr(10).join([f"- {p.get('title', 'Untitled')}" for p in papers[:10]])}

View all results: {view_url}

---
You received this email because you have alerts enabled for this saved search.
        """

        return await self.send_email(
            to=to,
            subject=subject,
            html=html,
            text=text,
        )


# Singleton instance
email_service = EmailService()
