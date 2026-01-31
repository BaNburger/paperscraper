"""Background jobs for alert processing."""

import logging
from typing import Any

from paper_scraper.core.database import get_db_session
from paper_scraper.modules.alerts.service import AlertService

logger = logging.getLogger(__name__)


async def process_daily_alerts_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Process all daily alerts.

    This job should be scheduled to run once per day.

    Args:
        ctx: Worker context.

    Returns:
        Dict with processing results.
    """
    logger.info("Starting daily alert processing")

    async with get_db_session() as db:
        service = AlertService(db)
        result = await service.process_alerts(frequency="daily")

    logger.info(
        f"Daily alert processing complete: "
        f"processed={result['processed']}, "
        f"sent={result['sent']}, "
        f"skipped={result['skipped']}, "
        f"failed={result['failed']}"
    )

    return result


async def process_weekly_alerts_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Process all weekly alerts.

    This job should be scheduled to run once per week.

    Args:
        ctx: Worker context.

    Returns:
        Dict with processing results.
    """
    logger.info("Starting weekly alert processing")

    async with get_db_session() as db:
        service = AlertService(db)
        result = await service.process_alerts(frequency="weekly")

    logger.info(
        f"Weekly alert processing complete: "
        f"processed={result['processed']}, "
        f"sent={result['sent']}, "
        f"skipped={result['skipped']}, "
        f"failed={result['failed']}"
    )

    return result


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
    from uuid import UUID

    logger.info(f"Processing immediate alert: {alert_id}")

    async with get_db_session() as db:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        from paper_scraper.modules.alerts.models import Alert

        # Get the alert
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
            logger.warning(f"Alert not found: {alert_id}")
            return {"status": "not_found", "alert_id": alert_id}

        if not alert.is_active:
            logger.info(f"Alert is inactive: {alert_id}")
            return {"status": "inactive", "alert_id": alert_id}

        service = AlertService(db)
        status = await service._process_single_alert(alert)

    logger.info(f"Immediate alert processing complete: {alert_id} -> {status}")

    return {
        "status": status,
        "alert_id": alert_id,
    }
