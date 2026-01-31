"""API router for alerts module."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, OrganizationId
from paper_scraper.core.database import get_db
from paper_scraper.modules.alerts.schemas import (
    AlertCreate,
    AlertListResponse,
    AlertResponse,
    AlertResultListResponse,
    AlertResultResponse,
    AlertTestResponse,
    AlertUpdate,
)
from paper_scraper.modules.alerts.service import AlertService

router = APIRouter()


def get_alert_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AlertService:
    """Dependency to get AlertService instance."""
    return AlertService(db)


@router.post(
    "",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create alert",
)
async def create_alert(
    data: AlertCreate,
    service: Annotated[AlertService, Depends(get_alert_service)],
    current_user: CurrentUser,
    organization_id: OrganizationId,
) -> AlertResponse:
    """Create a new alert for a saved search."""
    alert = await service.create(
        data=data,
        organization_id=organization_id,
        user_id=current_user.id,
    )
    return service.to_response(alert)


@router.get(
    "",
    response_model=AlertListResponse,
    summary="List alerts",
)
async def list_alerts(
    service: Annotated[AlertService, Depends(get_alert_service)],
    current_user: CurrentUser,
    organization_id: OrganizationId,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    active_only: bool = Query(default=False, description="Only return active alerts"),
) -> AlertListResponse:
    """List alerts for the current user."""
    alerts, total = await service.list_alerts(
        organization_id=organization_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        active_only=active_only,
    )

    return AlertListResponse(
        items=[service.to_response(a) for a in alerts],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
    summary="Get alert",
)
async def get_alert(
    alert_id: UUID,
    service: Annotated[AlertService, Depends(get_alert_service)],
    current_user: CurrentUser,
    organization_id: OrganizationId,
) -> AlertResponse:
    """Get an alert by ID."""
    alert = await service.get(
        alert_id=alert_id,
        organization_id=organization_id,
        user_id=current_user.id,
    )
    return service.to_response(alert)


@router.patch(
    "/{alert_id}",
    response_model=AlertResponse,
    summary="Update alert",
)
async def update_alert(
    alert_id: UUID,
    data: AlertUpdate,
    service: Annotated[AlertService, Depends(get_alert_service)],
    current_user: CurrentUser,
    organization_id: OrganizationId,
) -> AlertResponse:
    """Update an alert."""
    alert = await service.update(
        alert_id=alert_id,
        data=data,
        organization_id=organization_id,
        user_id=current_user.id,
    )
    return service.to_response(alert)


@router.delete(
    "/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete alert",
)
async def delete_alert(
    alert_id: UUID,
    service: Annotated[AlertService, Depends(get_alert_service)],
    current_user: CurrentUser,
    organization_id: OrganizationId,
) -> None:
    """Delete an alert."""
    await service.delete(
        alert_id=alert_id,
        organization_id=organization_id,
        user_id=current_user.id,
    )


@router.get(
    "/{alert_id}/results",
    response_model=AlertResultListResponse,
    summary="Get alert history",
)
async def get_alert_results(
    alert_id: UUID,
    service: Annotated[AlertService, Depends(get_alert_service)],
    current_user: CurrentUser,
    organization_id: OrganizationId,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> AlertResultListResponse:
    """Get the history/results for an alert."""
    results, total = await service.get_results(
        alert_id=alert_id,
        organization_id=organization_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )

    return AlertResultListResponse(
        items=[
            AlertResultResponse(
                id=r.id,
                alert_id=r.alert_id,
                status=r.status.value,
                papers_found=r.papers_found,
                new_papers=r.new_papers,
                paper_ids=r.paper_ids,
                delivered_at=r.delivered_at,
                error_message=r.error_message,
                created_at=r.created_at,
            )
            for r in results
        ],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.post(
    "/{alert_id}/test",
    response_model=AlertTestResponse,
    summary="Test alert",
)
async def test_alert(
    alert_id: UUID,
    service: Annotated[AlertService, Depends(get_alert_service)],
    current_user: CurrentUser,
    organization_id: OrganizationId,
) -> AlertTestResponse:
    """Test an alert by running its search without sending notification."""
    result = await service.test_alert(
        alert_id=alert_id,
        organization_id=organization_id,
        user_id=current_user.id,
    )
    return AlertTestResponse(**result)


@router.post(
    "/{alert_id}/trigger",
    response_model=AlertResultResponse,
    summary="Manually trigger alert",
)
async def trigger_alert(
    alert_id: UUID,
    service: Annotated[AlertService, Depends(get_alert_service)],
    current_user: CurrentUser,
    organization_id: OrganizationId,
) -> AlertResultResponse:
    """Manually trigger an alert (useful for testing)."""
    alert = await service.get(
        alert_id=alert_id,
        organization_id=organization_id,
        user_id=current_user.id,
    )

    # Process the alert
    await service._process_single_alert(alert)

    # Get the latest result
    results, _ = await service.get_results(
        alert_id=alert_id,
        organization_id=organization_id,
        user_id=current_user.id,
        page=1,
        page_size=1,
    )

    if results:
        r = results[0]
        return AlertResultResponse(
            id=r.id,
            alert_id=r.alert_id,
            status=r.status.value,
            papers_found=r.papers_found,
            new_papers=r.new_papers,
            paper_ids=r.paper_ids,
            delivered_at=r.delivered_at,
            error_message=r.error_message,
            created_at=r.created_at,
        )

    # Should not happen, but return empty result if no result found
    from uuid import uuid4
    from datetime import datetime
    return AlertResultResponse(
        id=uuid4(),
        alert_id=alert_id,
        status="skipped",
        papers_found=0,
        new_papers=0,
        paper_ids=[],
        delivered_at=None,
        error_message=None,
        created_at=datetime.utcnow(),
    )
