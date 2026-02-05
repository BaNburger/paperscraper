"""Service layer for badges and gamification."""

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

from paper_scraper.modules.badges.models import Badge, BadgeCategory, BadgeTier, UserBadge
from paper_scraper.modules.badges.schemas import (
    BadgeListResponse,
    BadgeResponse,
    UserBadgeListResponse,
    UserBadgeResponse,
    UserStatsResponse,
)
from paper_scraper.modules.papers.models import Paper
from paper_scraper.modules.papers.notes import PaperNote
from paper_scraper.modules.projects.models import Project
from paper_scraper.modules.scoring.models import PaperScore
from paper_scraper.modules.authors.models import AuthorContact

# Points required per level (cumulative). Level N requires LEVEL_THRESHOLDS[N-1] total points.
POINTS_PER_LEVEL = 100

# Default badge definitions seeded when none exist.
DEFAULT_BADGES = [
    {
        "name": "First Import",
        "description": "Import your first paper",
        "icon": "file-plus",
        "category": BadgeCategory.IMPORT,
        "tier": BadgeTier.BRONZE,
        "criteria": {"action": "paper_imported", "count": 1},
        "threshold": 1,
        "points": 10,
    },
    {
        "name": "Paper Collector",
        "description": "Import 10 papers",
        "icon": "library",
        "category": BadgeCategory.IMPORT,
        "tier": BadgeTier.SILVER,
        "criteria": {"action": "paper_imported", "count": 10},
        "threshold": 10,
        "points": 25,
    },
    {
        "name": "Research Library",
        "description": "Import 50 papers",
        "icon": "archive",
        "category": BadgeCategory.IMPORT,
        "tier": BadgeTier.GOLD,
        "criteria": {"action": "paper_imported", "count": 50},
        "threshold": 50,
        "points": 50,
    },
    {
        "name": "Knowledge Vault",
        "description": "Import 200 papers",
        "icon": "database",
        "category": BadgeCategory.IMPORT,
        "tier": BadgeTier.PLATINUM,
        "criteria": {"action": "paper_imported", "count": 200},
        "threshold": 200,
        "points": 100,
    },
    {
        "name": "First Score",
        "description": "Score your first paper with AI",
        "icon": "sparkles",
        "category": BadgeCategory.SCORING,
        "tier": BadgeTier.BRONZE,
        "criteria": {"action": "paper_scored", "count": 1},
        "threshold": 1,
        "points": 10,
    },
    {
        "name": "AI Analyst",
        "description": "Score 10 papers",
        "icon": "brain",
        "category": BadgeCategory.SCORING,
        "tier": BadgeTier.SILVER,
        "criteria": {"action": "paper_scored", "count": 10},
        "threshold": 10,
        "points": 25,
    },
    {
        "name": "Scoring Master",
        "description": "Score 50 papers",
        "icon": "trophy",
        "category": BadgeCategory.SCORING,
        "tier": BadgeTier.GOLD,
        "criteria": {"action": "paper_scored", "count": 50},
        "threshold": 50,
        "points": 50,
    },
    {
        "name": "Explorer",
        "description": "Perform your first search",
        "icon": "search",
        "category": BadgeCategory.EXPLORATION,
        "tier": BadgeTier.BRONZE,
        "criteria": {"action": "search_performed", "count": 1},
        "threshold": 1,
        "points": 10,
    },
    {
        "name": "Pathfinder",
        "description": "Perform 25 searches",
        "icon": "compass",
        "category": BadgeCategory.EXPLORATION,
        "tier": BadgeTier.SILVER,
        "criteria": {"action": "search_performed", "count": 25},
        "threshold": 25,
        "points": 25,
    },
    {
        "name": "Team Player",
        "description": "Contact 5 researchers",
        "icon": "users",
        "category": BadgeCategory.COLLABORATION,
        "tier": BadgeTier.BRONZE,
        "criteria": {"action": "author_contacted", "count": 5},
        "threshold": 5,
        "points": 15,
    },
    {
        "name": "Networker",
        "description": "Contact 20 researchers",
        "icon": "network",
        "category": BadgeCategory.COLLABORATION,
        "tier": BadgeTier.SILVER,
        "criteria": {"action": "author_contacted", "count": 20},
        "threshold": 20,
        "points": 30,
    },
    {
        "name": "Project Starter",
        "description": "Create your first project",
        "icon": "kanban",
        "category": BadgeCategory.MILESTONE,
        "tier": BadgeTier.BRONZE,
        "criteria": {"action": "project_created", "count": 1},
        "threshold": 1,
        "points": 10,
    },
    {
        "name": "Note Taker",
        "description": "Write 10 notes on papers",
        "icon": "pencil",
        "category": BadgeCategory.EXPLORATION,
        "tier": BadgeTier.BRONZE,
        "criteria": {"action": "note_created", "count": 10},
        "threshold": 10,
        "points": 15,
    },
]


class BadgeService:
    """Service for managing badges and user gamification."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def seed_badges(self) -> int:
        """Seed default badges if none exist. Returns count of badges created."""
        result = await self.db.execute(select(func.count()).select_from(Badge))
        existing = result.scalar() or 0
        if existing > 0:
            return 0

        created = 0
        for badge_data in DEFAULT_BADGES:
            badge = Badge(**badge_data)
            self.db.add(badge)
            created += 1

        await self.db.flush()
        return created

    async def list_badges(self) -> BadgeListResponse:
        """List all available badge definitions."""
        await self.seed_badges()

        result = await self.db.execute(
            select(Badge).order_by(Badge.category, Badge.tier)
        )
        badges = list(result.scalars().all())

        return BadgeListResponse(
            items=[BadgeResponse.model_validate(b) for b in badges],
            total=len(badges),
        )

    async def get_user_badges(self, user_id: UUID) -> UserBadgeListResponse:
        """Get all badges earned by a user."""
        result = await self.db.execute(
            select(UserBadge)
            .options(selectinload(UserBadge.badge))
            .where(UserBadge.user_id == user_id)
            .order_by(UserBadge.earned_at.desc())
        )
        user_badges = list(result.scalars().all())

        total_points = sum(ub.badge.points for ub in user_badges)

        items = [
            UserBadgeResponse(
                id=ub.id,
                badge_id=ub.badge_id,
                badge=BadgeResponse.model_validate(ub.badge),
                earned_at=ub.earned_at,
                progress=ub.progress,
            )
            for ub in user_badges
        ]

        return UserBadgeListResponse(
            items=items,
            total=len(items),
            total_points=total_points,
        )

    async def get_user_stats(
        self, user_id: UUID, organization_id: UUID
    ) -> UserStatsResponse:
        """Get user activity statistics for gamification display."""
        # Papers imported (by org, since papers are org-scoped)
        papers_result = await self.db.execute(
            select(func.count()).select_from(Paper).where(
                Paper.organization_id == organization_id
            )
        )
        papers_imported = papers_result.scalar() or 0

        # Papers scored
        scores_result = await self.db.execute(
            select(func.count()).select_from(PaperScore).where(
                PaperScore.organization_id == organization_id
            )
        )
        papers_scored = scores_result.scalar() or 0

        # Projects created
        projects_result = await self.db.execute(
            select(func.count()).select_from(Project).where(
                Project.organization_id == organization_id
            )
        )
        projects_created = projects_result.scalar() or 0

        # Notes created by user
        notes_result = await self.db.execute(
            select(func.count()).select_from(PaperNote).where(
                PaperNote.user_id == user_id
            )
        )
        notes_created = notes_result.scalar() or 0

        # Authors contacted by user
        contacts_result = await self.db.execute(
            select(func.count()).select_from(AuthorContact).where(
                AuthorContact.contacted_by_id == user_id
            )
        )
        authors_contacted = contacts_result.scalar() or 0

        # Badges earned
        badges_result = await self.db.execute(
            select(func.count()).select_from(UserBadge).where(
                UserBadge.user_id == user_id
            )
        )
        badges_earned = badges_result.scalar() or 0

        # Total points
        points_result = await self.db.execute(
            select(func.coalesce(func.sum(Badge.points), 0))
            .select_from(UserBadge)
            .join(Badge, UserBadge.badge_id == Badge.id)
            .where(UserBadge.user_id == user_id)
        )
        total_points = points_result.scalar() or 0

        # Calculate level and progress
        level = max(1, total_points // POINTS_PER_LEVEL + 1)
        level_progress = (total_points % POINTS_PER_LEVEL) / POINTS_PER_LEVEL

        return UserStatsResponse(
            papers_imported=papers_imported,
            papers_scored=papers_scored,
            searches_performed=0,  # Would need search log tracking
            projects_created=projects_created,
            notes_created=notes_created,
            authors_contacted=authors_contacted,
            badges_earned=badges_earned,
            total_points=total_points,
            level=level,
            level_progress=round(level_progress, 2),
        )

    async def check_and_award_badges(
        self, user_id: UUID, organization_id: UUID
    ) -> list[Badge]:
        """Check if user qualifies for any new badges and award them.

        Returns list of newly awarded badges.
        """
        await self.seed_badges()

        # Get all badges
        all_badges_result = await self.db.execute(select(Badge))
        all_badges = list(all_badges_result.scalars().all())

        # Get already earned badge IDs
        earned_result = await self.db.execute(
            select(UserBadge.badge_id).where(UserBadge.user_id == user_id)
        )
        earned_ids = set(earned_result.scalars().all())

        # Get current stats
        stats = await self.get_user_stats(user_id, organization_id)

        # Map actions to stat values
        action_counts = {
            "paper_imported": stats.papers_imported,
            "paper_scored": stats.papers_scored,
            "search_performed": stats.searches_performed,
            "project_created": stats.projects_created,
            "note_created": stats.notes_created,
            "author_contacted": stats.authors_contacted,
        }

        newly_awarded = []
        for badge in all_badges:
            if badge.id in earned_ids:
                continue

            action = badge.criteria.get("action")
            required = badge.threshold
            current = action_counts.get(action, 0)

            if current >= required:
                user_badge = UserBadge(
                    user_id=user_id,
                    badge_id=badge.id,
                    progress=current,
                )
                self.db.add(user_badge)
                newly_awarded.append(badge)

        if newly_awarded:
            try:
                await self.db.flush()
            except IntegrityError:
                await self.db.rollback()
                logger.warning("Duplicate badge award detected for user %s", user_id)
                return []

        return newly_awarded
