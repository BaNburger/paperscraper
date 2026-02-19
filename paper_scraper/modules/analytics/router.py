"""FastAPI router for analytics endpoints."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, require_permission
from paper_scraper.core.database import get_db
from paper_scraper.core.permissions import Permission
from paper_scraper.modules.analytics.schemas import (
    BenchmarkResponse,
    DashboardSummaryResponse,
    FunnelResponse,
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
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
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
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
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
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def get_paper_analytics(
    current_user: CurrentUser,
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    days: int = Query(default=90, ge=7, le=365, description="Number of days to analyze"),
) -> PaperAnalyticsResponse:
    """Get paper analytics.

    Returns import trends, scoring distributions, and top papers.
    """
    return await analytics_service.get_paper_analytics(current_user.organization_id, days=days)


@router.get(
    "/funnel",
    response_model=FunnelResponse,
    summary="Get innovation funnel analytics",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def get_funnel_analytics(
    current_user: CurrentUser,
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    project_id: UUID | None = Query(default=None, description="Filter by project"),
    start_date: date | None = Query(default=None, description="Start date filter"),
    end_date: date | None = Query(default=None, description="End date filter"),
) -> FunnelResponse:
    """Get innovation funnel analytics.

    Shows the progression of papers through stages:
    Imported -> Scored -> In Pipeline -> Contacted -> Transferred

    Returns stage counts and conversion rates.
    """
    return await analytics_service.get_funnel_analytics(
        organization_id=current_user.organization_id,
        project_id=project_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/benchmarks",
    response_model=BenchmarkResponse,
    summary="Get benchmark comparisons",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def get_benchmarks(
    current_user: CurrentUser,
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> BenchmarkResponse:
    """Get benchmark comparisons against platform averages.

    Compares organization metrics against anonymized aggregates from all organizations:
    - Papers per month
    - Scoring velocity (% of papers scored)
    - Pipeline conversion rate (% reaching contacted stage)
    """
    return await analytics_service.get_benchmarks(current_user.organization_id)
