"""Background jobs for data retention policy execution."""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select

from paper_scraper.core.database import get_db_session
from paper_scraper.modules.compliance.models import RetentionPolicy
from paper_scraper.modules.compliance.service import ComplianceService

logger = logging.getLogger(__name__)


async def apply_retention_policies_task(
    ctx: dict[str, Any],
    organization_id: UUID | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Apply retention policies for an organization or all organizations.

    This job is designed to be run nightly via arq cron to automatically
    enforce data retention policies.

    Args:
        ctx: Worker context.
        organization_id: Optional specific organization to process.
        dry_run: If True, only report what would be affected.

    Returns:
        Dict with results summary.
    """
    results_summary: dict[str, Any] = {
        "organizations_processed": 0,
        "policies_applied": 0,
        "total_records_affected": 0,
        "errors": [],
        "is_dry_run": dry_run,
        "started_at": datetime.now(UTC).isoformat(),
    }
    errors: list[dict[str, str]] = results_summary["errors"]

    logger.info(
        "Starting retention policies task (dry_run=%s, org=%s)",
        dry_run,
        organization_id or "all",
    )

    # First, determine which organizations to process
    async with get_db_session() as db:
        try:
            if organization_id:
                org_ids = [organization_id]
            else:
                query = (
                    select(RetentionPolicy.organization_id)
                    .where(RetentionPolicy.is_active == True)  # noqa: E712
                    .distinct()
                )
                result = await db.execute(query)
                org_ids = [row[0] for row in result]
        except Exception as e:
            logger.error("Failed to fetch organizations for retention: %s", e)
            errors.append(
                {
                    "organization_id": "global",
                    "error": str(e),
                }
            )
            results_summary["completed_at"] = datetime.now(UTC).isoformat()
            return results_summary

    logger.info("Processing retention for %d organizations", len(org_ids))

    # Process each organization in its own session for transaction isolation
    for org_id in org_ids:
        try:
            async with get_db_session() as db:
                service = ComplianceService(db)
                policy_results = await service.apply_retention_policies(
                    organization_id=org_id,
                    dry_run=dry_run,
                )

                org_affected = sum(r.records_affected for r in policy_results)
                results_summary["organizations_processed"] += 1
                results_summary["policies_applied"] += len(policy_results)
                results_summary["total_records_affected"] += org_affected

                if dry_run:
                    await db.rollback()

                logger.info(
                    "Retention for org %s: %d policies, %d records affected",
                    org_id,
                    len(policy_results),
                    org_affected,
                )

        except Exception as e:
            logger.error("Retention failed for org %s: %s", org_id, e, exc_info=True)
            errors.append(
                {
                    "organization_id": str(org_id),
                    "error": str(e),
                }
            )

    results_summary["completed_at"] = datetime.now(UTC).isoformat()
    logger.info(
        "Retention task completed: %d orgs, %d policies, %d records, %d errors",
        results_summary["organizations_processed"],
        results_summary["policies_applied"],
        results_summary["total_records_affected"],
        len(errors),
    )
    return results_summary


async def run_nightly_retention_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Scheduled task to run retention policies nightly.

    This is the cron job entry point that runs at a scheduled time
    to apply retention policies for all organizations.

    Args:
        ctx: Worker context.

    Returns:
        Dict with results summary.
    """
    logger.info("Nightly retention task started")
    return await apply_retention_policies_task(ctx, organization_id=None, dry_run=False)


async def preview_retention_impact_task(
    ctx: dict[str, Any],
    organization_id: UUID,
) -> dict[str, Any]:
    """Preview what data would be affected by retention policies.

    Useful for administrators to understand the impact before
    enabling policies.

    Args:
        ctx: Worker context.
        organization_id: The organization to preview.

    Returns:
        Dict with preview results.
    """
    return await apply_retention_policies_task(
        ctx,
        organization_id=organization_id,
        dry_run=True,
    )
