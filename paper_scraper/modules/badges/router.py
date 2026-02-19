"""FastAPI router for badges and gamification."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, require_permission
from paper_scraper.core.database import get_db
from paper_scraper.core.permissions import Permission
from paper_scraper.modules.badges.schemas import (
    BadgeListResponse,
    UserBadgeListResponse,
    UserStatsResponse,
)
from paper_scraper.modules.badges.service import BadgeService

router = APIRouter()


def get_badge_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BadgeService:
    return BadgeService(db)


@router.get(
    "/",
    response_model=BadgeListResponse,
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def list_badges(
    current_user: CurrentUser,
    service: Annotated[BadgeService, Depends(get_badge_service)],
):
    """List all available badges (system + organization-specific)."""
    return await service.list_badges(organization_id=current_user.organization_id)


@router.get(
    "/me",
    response_model=UserBadgeListResponse,
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def get_my_badges(
    current_user: CurrentUser,
    service: Annotated[BadgeService, Depends(get_badge_service)],
):
    """Get badges earned by the current user."""
    return await service.get_user_badges(current_user.id)


@router.get(
    "/me/stats",
    response_model=UserStatsResponse,
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def get_my_stats(
    current_user: CurrentUser,
    service: Annotated[BadgeService, Depends(get_badge_service)],
):
    """Get current user's activity statistics and gamification level."""
    return await service.get_user_stats(current_user.id, current_user.organization_id)


@router.post(
    "/me/check",
    response_model=UserBadgeListResponse,
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def check_badges(
    current_user: CurrentUser,
    service: Annotated[BadgeService, Depends(get_badge_service)],
):
    """Check and award any newly earned badges for the current user."""
    await service.check_and_award_badges(current_user.id, current_user.organization_id)
    return await service.get_user_badges(current_user.id)
