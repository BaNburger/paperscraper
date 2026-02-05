"""Pydantic schemas for badges and gamification."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from paper_scraper.modules.badges.models import BadgeCategory, BadgeTier


class BadgeResponse(BaseModel):
    """Response schema for a badge definition."""

    id: UUID
    name: str
    description: str
    icon: str
    category: BadgeCategory
    tier: BadgeTier
    threshold: int
    points: int

    model_config = {"from_attributes": True}


class UserBadgeResponse(BaseModel):
    """Response schema for a user's earned badge."""

    id: UUID
    badge_id: UUID
    badge: BadgeResponse
    earned_at: datetime
    progress: int

    model_config = {"from_attributes": True}


class BadgeListResponse(BaseModel):
    """List of all available badges with user progress."""

    items: list[BadgeResponse]
    total: int


class UserBadgeListResponse(BaseModel):
    """List of badges earned by a user."""

    items: list[UserBadgeResponse]
    total: int
    total_points: int


class UserStatsResponse(BaseModel):
    """User activity statistics for gamification."""

    papers_imported: int = 0
    papers_scored: int = 0
    searches_performed: int = 0
    projects_created: int = 0
    notes_created: int = 0
    authors_contacted: int = 0
    badges_earned: int = 0
    total_points: int = 0
    level: int = 1
    level_progress: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Progress toward next level (0-1)"
    )


class BadgeEarnedNotification(BaseModel):
    """Notification payload when a badge is earned."""

    badge: BadgeResponse
    earned_at: datetime
    message: str
