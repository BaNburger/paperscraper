"""FastAPI router for trends endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser
from paper_scraper.core.database import get_db
from paper_scraper.modules.trends.schemas import (
    TrendDashboardResponse,
    TrendPaperListResponse,
    TrendSnapshotResponse,
    TrendTopicCreate,
    TrendTopicListResponse,
    TrendTopicResponse,
    TrendTopicUpdate,
)
from paper_scraper.modules.trends.service import TrendsService

router = APIRouter()


def get_trends_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TrendsService:
    """Dependency to get trends service instance."""
    return TrendsService(db)


@router.post(
    "/",
    response_model=TrendTopicResponse,
    status_code=201,
    summary="Create trend topic",
)
async def create_trend_topic(
    data: TrendTopicCreate,
    current_user: CurrentUser,
    service: Annotated[TrendsService, Depends(get_trends_service)],
) -> TrendTopicResponse:
    """Create a new trend topic with semantic description."""
    return await service.create_topic(
        data=data,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )


@router.get(
    "/",
    response_model=TrendTopicListResponse,
    summary="List trend topics",
)
async def list_trend_topics(
    current_user: CurrentUser,
    service: Annotated[TrendsService, Depends(get_trends_service)],
    include_inactive: bool = Query(False, description="Include inactive topics"),
) -> TrendTopicListResponse:
    """List all trend topics for the organization."""
    return await service.list_topics(
        organization_id=current_user.organization_id,
        include_inactive=include_inactive,
    )


@router.get(
    "/{topic_id}",
    response_model=TrendTopicResponse,
    summary="Get trend topic",
)
async def get_trend_topic(
    topic_id: UUID,
    current_user: CurrentUser,
    service: Annotated[TrendsService, Depends(get_trends_service)],
) -> TrendTopicResponse:
    """Get a single trend topic by ID."""
    return await service.get_topic(topic_id, current_user.organization_id)


@router.patch(
    "/{topic_id}",
    response_model=TrendTopicResponse,
    summary="Update trend topic",
)
async def update_trend_topic(
    topic_id: UUID,
    data: TrendTopicUpdate,
    current_user: CurrentUser,
    service: Annotated[TrendsService, Depends(get_trends_service)],
) -> TrendTopicResponse:
    """Update a trend topic."""
    return await service.update_topic(
        topic_id, data, current_user.organization_id
    )


@router.delete(
    "/{topic_id}",
    status_code=204,
    summary="Delete trend topic",
)
async def delete_trend_topic(
    topic_id: UUID,
    current_user: CurrentUser,
    service: Annotated[TrendsService, Depends(get_trends_service)],
) -> None:
    """Delete a trend topic and all associated data."""
    await service.delete_topic(topic_id, current_user.organization_id)


@router.post(
    "/{topic_id}/analyze",
    response_model=TrendSnapshotResponse,
    summary="Analyze trend topic",
)
async def analyze_trend_topic(
    topic_id: UUID,
    current_user: CurrentUser,
    service: Annotated[TrendsService, Depends(get_trends_service)],
    min_similarity: float = Query(
        0.65, ge=0.0, le=1.0, description="Minimum similarity threshold"
    ),
    max_papers: int = Query(
        100, ge=1, le=500, description="Maximum papers to match"
    ),
) -> TrendSnapshotResponse:
    """Trigger analysis for a trend topic.

    Performs semantic paper matching, score aggregation, patent search, and AI summary.
    """
    return await service.analyze_topic(
        topic_id=topic_id,
        organization_id=current_user.organization_id,
        min_similarity=min_similarity,
        max_papers=max_papers,
    )


@router.get(
    "/{topic_id}/dashboard",
    response_model=TrendDashboardResponse,
    summary="Get trend dashboard",
)
async def get_trend_dashboard(
    topic_id: UUID,
    current_user: CurrentUser,
    service: Annotated[TrendsService, Depends(get_trends_service)],
) -> TrendDashboardResponse:
    """Get complete dashboard data for a trend topic."""
    return await service.get_dashboard(topic_id, current_user.organization_id)


@router.get(
    "/{topic_id}/papers",
    response_model=TrendPaperListResponse,
    summary="Get matched papers",
)
async def get_trend_papers(
    topic_id: UUID,
    current_user: CurrentUser,
    service: Annotated[TrendsService, Depends(get_trends_service)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> TrendPaperListResponse:
    """Get paginated list of papers matched to this trend."""
    return await service.get_matched_papers(
        topic_id=topic_id,
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
    )
