"""Service layer for audit logging."""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.audit.models import AuditAction, AuditLog
from paper_scraper.modules.audit.schemas import AuditLogFilters, AuditLogListResponse, AuditLogResponse


class AuditService:
    """Service for audit logging operations."""

    def __init__(self, db: AsyncSession):
        """Initialize audit service with database session.

        Args:
            db: Async database session.
        """
        self.db = db

    async def log(
        self,
        action: AuditAction | str,
        user_id: UUID | None = None,
        organization_id: UUID | None = None,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        details: dict[str, Any] | None = None,
        request: Request | None = None,
    ) -> AuditLog:
        """Create an audit log entry.

        Args:
            action: The action being logged.
            user_id: ID of the user performing the action (if applicable).
            organization_id: ID of the organization context.
            resource_type: Type of resource affected (e.g., "paper", "user").
            resource_id: ID of the resource affected.
            details: Additional context as JSON.
            request: FastAPI request for extracting IP and user agent.

        Returns:
            The created AuditLog entry.
        """
        ip_address = None
        user_agent = None

        if request:
            # Extract client IP (handle proxies)
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                ip_address = forwarded.split(",")[0].strip()
            else:
                ip_address = request.client.host if request.client else None

            user_agent = request.headers.get("User-Agent", "")[:500]

        action_str = action.value if isinstance(action, AuditAction) else action

        audit_log = AuditLog(
            action=action_str,
            user_id=user_id,
            organization_id=organization_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(audit_log)
        await self.db.flush()

        return audit_log

    async def list_logs(
        self,
        organization_id: UUID,
        filters: AuditLogFilters | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> AuditLogListResponse:
        """List audit logs for an organization with filtering and pagination.

        Args:
            organization_id: The organization ID (tenant isolation).
            filters: Optional filters to apply.
            page: Page number (1-indexed).
            page_size: Number of items per page.

        Returns:
            Paginated list of audit logs.
        """
        query = select(AuditLog).where(AuditLog.organization_id == organization_id)

        if filters:
            if filters.action:
                query = query.where(AuditLog.action == filters.action.value)
            if filters.user_id:
                query = query.where(AuditLog.user_id == filters.user_id)
            if filters.resource_type:
                query = query.where(AuditLog.resource_type == filters.resource_type)
            if filters.start_date:
                query = query.where(AuditLog.created_at >= filters.start_date)
            if filters.end_date:
                query = query.where(AuditLog.created_at <= filters.end_date)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        logs = list(result.scalars().all())

        return AuditLogListResponse(
            items=[AuditLogResponse.model_validate(log) for log in logs],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size,
        )

    async def get_user_activity(
        self,
        user_id: UUID,
        organization_id: UUID,
        limit: int = 100,
    ) -> list[AuditLogResponse]:
        """Get recent activity for a specific user.

        Args:
            user_id: The user ID.
            organization_id: The organization ID (tenant isolation).
            limit: Maximum number of entries to return.

        Returns:
            List of recent audit log entries for the user.
        """
        result = await self.db.execute(
            select(AuditLog)
            .where(
                AuditLog.user_id == user_id,
                AuditLog.organization_id == organization_id,
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        logs = list(result.scalars().all())
        return [AuditLogResponse.model_validate(log) for log in logs]


# Singleton instance for use without dependency injection
# (e.g., in background tasks or middleware)
class AuditServiceFactory:
    """Factory for creating audit service instances."""

    @staticmethod
    def create(db: AsyncSession) -> AuditService:
        """Create an audit service instance.

        Args:
            db: Async database session.

        Returns:
            AuditService instance.
        """
        return AuditService(db)


audit_service = AuditServiceFactory()
