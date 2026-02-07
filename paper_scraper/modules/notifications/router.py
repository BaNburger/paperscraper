"""API router for notifications module."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, OrganizationId, require_permission
from paper_scraper.core.database import get_db
from paper_scraper.core.permissions import Permission
from paper_scraper.modules.notifications.schemas import (
    MarkReadRequest,
    NotificationListResponse,
    NotificationResponse,
)
from paper_scraper.modules.notifications.service import NotificationService

router = APIRouter()


def get_notification_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationService:
    """Dependency to get NotificationService instance."""
    return NotificationService(db)


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="List notifications",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def list_notifications(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    current_user: CurrentUser,
    organization_id: OrganizationId,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    unread_only: bool = Query(default=False, description="Only return unread notifications"),
) -> NotificationListResponse:
    """List notifications for the current user."""
    notifications, total, unread_count = await service.list_notifications(
        user_id=current_user.id,
        organization_id=organization_id,
        page=page,
        page_size=page_size,
        unread_only=unread_only,
    )

    return NotificationListResponse(
        items=[
            NotificationResponse(
                id=n.id,
                type=n.type.value,
                title=n.title,
                message=n.message,
                is_read=n.is_read,
                resource_type=n.resource_type,
                resource_id=n.resource_id,
                created_at=n.created_at,
            )
            for n in notifications
        ],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0,
        unread_count=unread_count,
    )


@router.get(
    "/unread-count",
    summary="Get unread notification count",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def get_unread_count(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    current_user: CurrentUser,
    organization_id: OrganizationId,
) -> dict[str, int]:
    """Get the count of unread notifications for badge display."""
    count = await service.get_unread_count(
        user_id=current_user.id,
        organization_id=organization_id,
    )
    return {"unread_count": count}


@router.post(
    "/mark-read",
    summary="Mark notifications as read",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def mark_notifications_read(
    data: MarkReadRequest,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    current_user: CurrentUser,
    organization_id: OrganizationId,
) -> dict[str, int]:
    """Mark specific notifications as read."""
    updated = await service.mark_as_read(
        notification_ids=data.notification_ids,
        user_id=current_user.id,
        organization_id=organization_id,
    )
    return {"updated": updated}


@router.post(
    "/mark-all-read",
    summary="Mark all notifications as read",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def mark_all_notifications_read(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    current_user: CurrentUser,
    organization_id: OrganizationId,
) -> dict[str, int]:
    """Mark all notifications as read for the current user."""
    updated = await service.mark_all_as_read(
        user_id=current_user.id,
        organization_id=organization_id,
    )
    return {"updated": updated}
