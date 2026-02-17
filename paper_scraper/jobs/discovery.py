"""Background jobs for discovery profile processing."""

import logging
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


async def process_discovery_daily_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Process all daily discovery profiles.

    Triggered by cron at 5:00 AM UTC.
    """
    from paper_scraper.core.database import get_db_session
    from paper_scraper.modules.discovery.service import DiscoveryService

    async with get_db_session() as db:
        service = DiscoveryService(db)
        result = await service.process_all_profiles(frequency="daily")
        logger.info("Daily discovery processing: %s", result)
        return result


async def process_discovery_weekly_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Process all weekly discovery profiles.

    Triggered by cron on Monday at 5:00 AM UTC.
    """
    from paper_scraper.core.database import get_db_session
    from paper_scraper.modules.discovery.service import DiscoveryService

    async with get_db_session() as db:
        service = DiscoveryService(db)
        result = await service.process_all_profiles(frequency="weekly")
        logger.info("Weekly discovery processing: %s", result)
        return result


async def run_discovery_task(
    ctx: dict[str, Any],
    saved_search_id: str,
    organization_id: str,
    user_id: str,
) -> dict[str, Any]:
    """Run discovery for a specific saved search on demand.

    Args:
        ctx: Worker context.
        saved_search_id: UUID string of the saved search.
        organization_id: UUID string of the organization.
        user_id: UUID string of the triggering user.

    Returns:
        Dict with discovery results.
    """
    from paper_scraper.core.database import get_db_session
    from paper_scraper.modules.discovery.service import DiscoveryService

    async with get_db_session() as db:
        service = DiscoveryService(db)
        result = await service.run_discovery(
            saved_search_id=UUID(saved_search_id),
            organization_id=UUID(organization_id),
            user_id=UUID(user_id),
        )
        return result.model_dump(mode="json")
