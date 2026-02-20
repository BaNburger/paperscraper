"""Service layer for usage tracking and quota enforcement."""

import logging
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.billing.models import OrganizationUsage

logger = logging.getLogger(__name__)

# Tier limits for quota enforcement
TIER_LIMITS: dict[str, dict[str, int | None]] = {
    "free": {
        "papers": 100,
        "scores_per_month": 50,
        "cost_cap_usd": 0,
    },
    "starter": {
        "papers": 10_000,
        "scores_per_month": 5_000,
        "cost_cap_usd": 50,
    },
    "professional": {
        "papers": 100_000,
        "scores_per_month": 50_000,
        "cost_cap_usd": 500,
    },
    "enterprise": {
        "papers": None,  # Unlimited
        "scores_per_month": None,
        "cost_cap_usd": None,
    },
}


class BillingService:
    """Service for tracking organization usage and enforcing quotas."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Usage Tracking
    # =========================================================================

    async def record_scoring_usage(
        self,
        organization_id: UUID,
        papers_scored: int = 1,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
    ) -> OrganizationUsage:
        """Record scoring usage for the current month.

        Uses INSERT ... ON CONFLICT to atomically increment counters.

        Args:
            organization_id: Organization UUID.
            papers_scored: Number of papers scored.
            input_tokens: LLM input tokens used.
            output_tokens: LLM output tokens used.
            cost_usd: Estimated cost in USD.

        Returns:
            Updated OrganizationUsage record.
        """
        period = datetime.now(UTC).strftime("%Y-%m")

        stmt = (
            pg_insert(OrganizationUsage)
            .values(
                organization_id=organization_id,
                period=period,
                papers_scored=papers_scored,
                llm_input_tokens=input_tokens,
                llm_output_tokens=output_tokens,
                estimated_cost_usd=cost_usd,
            )
            .on_conflict_do_update(
                constraint="uq_org_usage_period",
                set_={
                    "papers_scored": OrganizationUsage.papers_scored + papers_scored,
                    "llm_input_tokens": OrganizationUsage.llm_input_tokens + input_tokens,
                    "llm_output_tokens": OrganizationUsage.llm_output_tokens + output_tokens,
                    "estimated_cost_usd": OrganizationUsage.estimated_cost_usd
                    + Decimal(str(cost_usd)),
                    "updated_at": datetime.now(UTC),
                },
            )
            .returning(OrganizationUsage)
        )

        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def record_import_usage(
        self,
        organization_id: UUID,
        papers_imported: int = 1,
    ) -> OrganizationUsage:
        """Record paper import usage for the current month.

        Args:
            organization_id: Organization UUID.
            papers_imported: Number of papers imported.

        Returns:
            Updated OrganizationUsage record.
        """
        period = datetime.now(UTC).strftime("%Y-%m")

        stmt = (
            pg_insert(OrganizationUsage)
            .values(
                organization_id=organization_id,
                period=period,
                papers_imported=papers_imported,
            )
            .on_conflict_do_update(
                constraint="uq_org_usage_period",
                set_={
                    "papers_imported": OrganizationUsage.papers_imported + papers_imported,
                    "updated_at": datetime.now(UTC),
                },
            )
            .returning(OrganizationUsage)
        )

        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def record_embedding_usage(
        self,
        organization_id: UUID,
        embedding_tokens: int = 0,
        cost_usd: float = 0.0,
    ) -> OrganizationUsage:
        """Record embedding usage for the current month.

        Args:
            organization_id: Organization UUID.
            embedding_tokens: Embedding tokens used.
            cost_usd: Estimated cost in USD.

        Returns:
            Updated OrganizationUsage record.
        """
        period = datetime.now(UTC).strftime("%Y-%m")

        stmt = (
            pg_insert(OrganizationUsage)
            .values(
                organization_id=organization_id,
                period=period,
                embedding_tokens=embedding_tokens,
                estimated_cost_usd=cost_usd,
            )
            .on_conflict_do_update(
                constraint="uq_org_usage_period",
                set_={
                    "embedding_tokens": OrganizationUsage.embedding_tokens + embedding_tokens,
                    "estimated_cost_usd": OrganizationUsage.estimated_cost_usd
                    + Decimal(str(cost_usd)),
                    "updated_at": datetime.now(UTC),
                },
            )
            .returning(OrganizationUsage)
        )

        result = await self.db.execute(stmt)
        return result.scalar_one()

    # =========================================================================
    # Usage Queries
    # =========================================================================

    async def get_current_usage(
        self,
        organization_id: UUID,
    ) -> OrganizationUsage | None:
        """Get the current month's usage for an organization.

        Args:
            organization_id: Organization UUID.

        Returns:
            Usage record or None if no usage this month.
        """
        period = datetime.now(UTC).strftime("%Y-%m")
        result = await self.db.execute(
            select(OrganizationUsage).where(
                OrganizationUsage.organization_id == organization_id,
                OrganizationUsage.period == period,
            )
        )
        return result.scalar_one_or_none()

    async def get_usage_history(
        self,
        organization_id: UUID,
        months: int = 6,
    ) -> list[OrganizationUsage]:
        """Get usage history for the last N months.

        Args:
            organization_id: Organization UUID.
            months: Number of months to look back.

        Returns:
            List of usage records ordered by period descending.
        """
        result = await self.db.execute(
            select(OrganizationUsage)
            .where(OrganizationUsage.organization_id == organization_id)
            .order_by(OrganizationUsage.period.desc())
            .limit(months)
        )
        return list(result.scalars().all())

    # =========================================================================
    # Quota Enforcement
    # =========================================================================

    async def check_scoring_quota(
        self,
        organization_id: UUID,
        tier: str,
        papers_to_score: int = 1,
    ) -> tuple[bool, str | None]:
        """Check if organization can score more papers within their quota.

        Args:
            organization_id: Organization UUID.
            tier: Subscription tier (free, starter, professional, enterprise).
            papers_to_score: Number of papers requested to score.

        Returns:
            (allowed, error_message) tuple. allowed=True if within quota.
        """
        limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
        max_scores = limits.get("scores_per_month")

        if max_scores is None:
            return True, None  # Unlimited

        usage = await self.get_current_usage(organization_id)
        current_scores = usage.papers_scored if usage else 0

        if current_scores + papers_to_score > max_scores:
            remaining = max(0, max_scores - current_scores)
            return False, (
                f"Monthly scoring quota exceeded. "
                f"Used {current_scores}/{max_scores} scores this month. "
                f"Remaining: {remaining}. Upgrade plan for higher limits."
            )

        return True, None

    async def check_cost_cap(
        self,
        organization_id: UUID,
        tier: str,
    ) -> tuple[bool, str | None]:
        """Check if organization is within their monthly cost cap.

        Args:
            organization_id: Organization UUID.
            tier: Subscription tier.

        Returns:
            (allowed, error_message) tuple.
        """
        limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
        cost_cap = limits.get("cost_cap_usd")

        if cost_cap is None:
            return True, None  # Unlimited

        usage = await self.get_current_usage(organization_id)
        current_cost = float(usage.estimated_cost_usd) if usage else 0.0

        if current_cost >= cost_cap:
            return False, (
                f"Monthly cost cap reached. "
                f"Current spend: ${current_cost:.2f} / ${cost_cap:.2f}. "
                f"Upgrade plan for higher limits."
            )

        return True, None
