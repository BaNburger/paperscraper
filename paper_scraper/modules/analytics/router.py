"""FastAPI router for analytics endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser
from paper_scraper.core.database import get_db
from paper_scraper.modules.analytics.schemas import (
    DashboardSummaryResponse,
    PaperAnalyticsResponse,
    TeamOverviewResponse,
)
from paper_scraper.modules.analytics.service import AnalyticsService

router = APIRouter()


def get_analytics_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AnalyticsService:
    """Dependency to get analytics service instance."""
    return AnalyticsService(db)


@router.get(
    "/dashboard",
    response_model=DashboardSummaryResponse,
    summary="Get dashboard summary",
)
async def get_dashboard_summary(
    current_user: CurrentUser,
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> DashboardSummaryResponse:
    """Get dashboard summary with key metrics.

    Returns aggregated metrics including paper counts, scoring stats,
    project counts, and trends for the last 30 days.
    """
    return await analytics_service.get_dashboard_summary(current_user.organization_id)


@router.get(
    "/team",
    response_model=TeamOverviewResponse,
    summary="Get team analytics",
)
async def get_team_overview(
    current_user: CurrentUser,
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> TeamOverviewResponse:
    """Get team overview statistics.

    Returns user counts, activity metrics, and per-user statistics.
    """
    return await analytics_service.get_team_overview(current_user.organization_id)


@router.get(
    "/papers",
    response_model=PaperAnalyticsResponse,
    summary="Get paper analytics",
)
async def get_paper_analytics(
    current_user: CurrentUser,
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    days: int = Query(default=90, ge=7, le=365, description="Number of days to analyze"),
) -> PaperAnalyticsResponse:
    """Get paper analytics.

    Returns import trends, scoring distributions, and top papers.
    """
    return await analytics_service.get_paper_analytics(
        current_user.organization_id, days=days
    )
