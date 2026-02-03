"""Background jobs for alert processing."""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from paper_scraper.core.database import get_db_session
from paper_scraper.modules.alerts.models import Alert
from paper_scraper.modules.alerts.service import AlertService

logger = logging.getLogger(__name__)


async def _process_alerts_by_frequency(frequency: str) -> dict[str, Any]:
    """Process alerts for a given frequency and log results.

    Args:
        frequency: Alert frequency ('daily' or 'weekly').

    Returns:
        Dict with processing results.
    """
    logger.info("Starting %s alert processing", frequency)

    async with get_db_session() as db:
        service = AlertService(db)
        result = await service.process_alerts(frequency=frequency)

    logger.info(
        "%s alert processing complete: processed=%d, sent=%d, skipped=%d, failed=%d",
        frequency.capitalize(),
        result["processed"],
        result["sent"],
        result["skipped"],
        result["failed"],
    )

    return result


async def process_daily_alerts_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Process all daily alerts. Scheduled to run once per day."""
    return await _process_alerts_by_frequency("daily")


async def process_weekly_alerts_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Process all weekly alerts. Scheduled to run once per week."""
    return await _process_alerts_by_frequency("weekly")


async def process_immediate_alert_task(
    ctx: dict[str, Any],
    alert_id: str,
) -> dict[str, Any]:
    """Process a single alert immediately.

    Called when a saved search has alert_frequency='immediately'.

    Args:
        ctx: Worker context.
        alert_id: ID of the alert to process.

    Returns:
        Dict with processing result.
    """
    logger.info("Processing immediate alert: %s", alert_id)

    async with get_db_session() as db:
        result = await db.execute(
            select(Alert)
            .options(
                selectinload(Alert.saved_search),
                selectinload(Alert.user),
            )
            .where(Alert.id == UUID(alert_id))
        )
        alert = result.scalar_one_or_none()

        if not alert:
            logger.warning("Alert not found: %s", alert_id)
            return {"status": "not_found", "alert_id": alert_id}

        if not alert.is_active:
            logger.info("Alert is inactive: %s", alert_id)
            return {"status": "inactive", "alert_id": alert_id}

        service = AlertService(db)
        status = await service._process_single_alert(alert)

    logger.info("Immediate alert processing complete: %s -> %s", alert_id, status)

    return {"status": status, "alert_id": alert_id}
