"""Custom exceptions for Paper Scraper."""

from typing import Any
from uuid import UUID


class PaperScraperException(Exception):
    """Base exception for all Paper Scraper errors."""

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.code = code or "PAPER_SCRAPER_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(PaperScraperException):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        resource: str,
        identifier: str | UUID | None = None,
        details: dict[str, Any] | None = None,
    ):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} with ID '{identifier}' not found"
        super().__init__(message=message, code="NOT_FOUND", details=details)
        self.resource = resource
        self.identifier = identifier


class UnauthorizedError(PaperScraperException):
    """Raised when authentication fails or is missing."""

    def __init__(
        self,
        message: str = "Authentication required",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message=message, code="UNAUTHORIZED", details=details)


class ForbiddenError(PaperScraperException):
    """Raised when user lacks permission for an action."""

    def __init__(
        self,
        message: str = "You don't have permission to perform this action",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message=message, code="FORBIDDEN", details=details)


class ValidationError(PaperScraperException):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message=message, code="VALIDATION_ERROR", details=details)
        self.field = field


class DuplicateError(PaperScraperException):
    """Raised when attempting to create a duplicate resource."""

    def __init__(
        self,
        resource: str,
        field: str,
        value: str,
        details: dict[str, Any] | None = None,
    ):
        message = f"{resource} with {field} '{value}' already exists"
        super().__init__(message=message, code="DUPLICATE", details=details)
        self.resource = resource
        self.field = field
        self.value = value


class ExternalAPIError(PaperScraperException):
    """Raised when an external API call fails."""

    def __init__(
        self,
        service: str,
        message: str,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        full_message = f"{service} API error: {message}"
        super().__init__(message=full_message, code="EXTERNAL_API_ERROR", details=details)
        self.service = service
        self.status_code = status_code


class ScoringError(PaperScraperException):
    """Raised when AI scoring fails."""

    def __init__(
        self,
        paper_id: UUID,
        dimension: str,
        reason: str,
        details: dict[str, Any] | None = None,
    ):
        message = f"Scoring failed for paper {paper_id}, dimension '{dimension}': {reason}"
        super().__init__(message=message, code="SCORING_ERROR", details=details)
        self.paper_id = paper_id
        self.dimension = dimension
        self.reason = reason


class RateLimitError(PaperScraperException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        limit: int,
        window: str,
        details: dict[str, Any] | None = None,
    ):
        message = f"Rate limit exceeded: {limit} requests per {window}"
        super().__init__(message=message, code="RATE_LIMIT_EXCEEDED", details=details)
        self.limit = limit
        self.window = window


class EmailError(PaperScraperException):
    """Raised when email sending fails."""

    def __init__(
        self,
        recipient: str,
        reason: str,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        message = f"Failed to send email to {recipient}: {reason}"
        super().__init__(message=message, code="EMAIL_ERROR", details=details)
        self.recipient = recipient
        self.reason = reason
        self.status_code = status_code
