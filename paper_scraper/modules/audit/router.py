"""FastAPI router for audit log endpoints."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, require_admin
from paper_scraper.core.database import get_db
from paper_scraper.modules.audit.models import AuditAction
from paper_scraper.modules.audit.schemas import (
    AuditLogFilters,
    AuditLogListResponse,
    AuditLogResponse,
)
from paper_scraper.modules.audit.service import AuditService

router = APIRouter()


def get_audit_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AuditService:
    """Dependency to get audit service instance."""
    return AuditService(db)


@router.get(
    "/",
    response_model=AuditLogListResponse,
    summary="List audit logs",
    dependencies=[Depends(require_admin)],
)
async def list_audit_logs(
    current_user: CurrentUser,
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    action: AuditAction | None = Query(None, description="Filter by action type"),
    user_id: UUID | None = Query(None, description="Filter by user ID"),
    resource_type: str | None = Query(None, description="Filter by resource type"),
    start_date: datetime | None = Query(None, description="Filter from date"),
    end_date: datetime | None = Query(None, description="Filter to date"),
) -> AuditLogListResponse:
    """List audit logs for the organization.

    Only admins can view audit logs.
    """
    filters = AuditLogFilters(
        action=action,
        user_id=user_id,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date,
    )

    return await audit_service.list_logs(
        organization_id=current_user.organization_id,
        filters=filters,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/users/{user_id}",
    response_model=list[AuditLogResponse],
    summary="Get user activity",
    dependencies=[Depends(require_admin)],
)
async def get_user_activity(
    user_id: UUID,
    current_user: CurrentUser,
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    limit: int = Query(100, ge=1, le=500, description="Maximum entries to return"),
) -> list[AuditLogResponse]:
    """Get recent activity for a specific user.

    Only admins can view user activity logs.
    """
    return await audit_service.get_user_activity(
        user_id=user_id,
        organization_id=current_user.organization_id,
        limit=limit,
    )


@router.get(
    "/my-activity",
    response_model=list[AuditLogResponse],
    summary="Get my activity",
)
async def get_my_activity(
    current_user: CurrentUser,
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    limit: int = Query(50, ge=1, le=100, description="Maximum entries to return"),
) -> list[AuditLogResponse]:
    """Get the current user's own activity log."""
    return await audit_service.get_user_activity(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        limit=limit,
    )
