"""Background job for automated badge awarding.

This module provides event-driven badge awarding via arq background jobs.
Badges are checked and awarded after specific user actions like:
- Paper imports
- Paper scoring
- Group creation
- Author contacts
- Note creation
"""

import logging
from typing import Any
from uuid import UUID

from paper_scraper.core.database import get_db_session
from paper_scraper.modules.badges.service import BadgeService

logger = logging.getLogger(__name__)


async def check_and_award_badges_task(
    ctx: dict[str, Any],
    user_id: str,
    organization_id: str,
    trigger_action: str | None = None,
) -> dict[str, Any]:
    """Check user stats against badge criteria and award earned badges.

    This task is triggered after specific user actions to check if any
    new badges have been earned.

    Args:
        ctx: arq context.
        user_id: UUID string of the user to check.
        organization_id: UUID string of the organization.
        trigger_action: Optional action that triggered this check (for logging).

    Returns:
        Dict with awarded badge information.
    """
    # Validate UUID strings early to prevent invalid input processing
    try:
        user_uuid = UUID(user_id)
        org_uuid = UUID(organization_id)
    except ValueError:
        logger.warning(f"Invalid UUID in badge check: user_id={user_id[:36] if len(user_id) > 36 else user_id}")
        return {
            "status": "error",
            "error": "Invalid UUID format",
        }

    async with get_db_session() as db:
        service = BadgeService(db)

        try:
            awarded = await service.check_and_award_badges(
                user_id=user_uuid,
                organization_id=org_uuid,
            )

            if awarded:
                logger.info(
                    f"User {user_id} earned {len(awarded)} new badge(s) "
                    f"after {trigger_action or 'activity'}: "
                    f"{[b.name for b in awarded]}"
                )
                return {
                    "status": "badges_awarded",
                    "user_id": user_id,
                    "trigger_action": trigger_action,
                    "awarded_count": len(awarded),
                    "badges": [
                        {"name": b.name, "tier": b.tier.value, "points": b.points}
                        for b in awarded
                    ],
                }
            else:
                return {
                    "status": "no_new_badges",
                    "user_id": user_id,
                    "trigger_action": trigger_action,
                    "awarded_count": 0,
                    "badges": [],
                }

        except Exception as e:
            logger.error(f"Badge check failed for user {user_id}: {e}")
            return {
                "status": "error",
                "error": "Badge processing failed",
            }


async def batch_check_badges_task(
    ctx: dict[str, Any],
    organization_id: str,
    user_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Check and award badges for multiple users in an organization.

    Useful for periodic batch processing or after bulk operations.

    Args:
        ctx: arq context.
        organization_id: UUID string of the organization.
        user_ids: Optional list of specific user IDs to check.
                  If None, checks all active users in the organization.

    Returns:
        Dict with batch processing results.
    """
    # Validate organization UUID early
    try:
        org_uuid = UUID(organization_id)
    except ValueError:
        logger.warning(f"Invalid organization UUID in batch badge check: {organization_id[:36] if len(organization_id) > 36 else organization_id}")
        return {
            "status": "error",
            "error": "Invalid organization UUID format",
        }

    async with get_db_session() as db:
        from sqlalchemy import select

        from paper_scraper.modules.auth.models import User

        # Get users to check with UUID validation
        if user_ids:
            users_to_check = []
            for uid in user_ids:
                try:
                    users_to_check.append(UUID(uid))
                except ValueError:
                    logger.warning(f"Skipping invalid user UUID: {uid[:36] if len(uid) > 36 else uid}")
        else:
            # Get all active users in the organization
            result = await db.execute(
                select(User.id).where(
                    User.organization_id == org_uuid,
                    User.is_active == True,  # noqa: E712
                )
            )
            users_to_check = list(result.scalars().all())

        service = BadgeService(db)
        total_awarded = 0
        user_results: list[dict] = []

        for uid in users_to_check:
            try:
                awarded = await service.check_and_award_badges(
                    user_id=uid,
                    organization_id=org_uuid,
                )
                if awarded:
                    total_awarded += len(awarded)
                    user_results.append({
                        "user_id": str(uid),
                        "awarded_count": len(awarded),
                        "badges": [b.name for b in awarded],
                    })
            except Exception as e:
                logger.warning(f"Badge check failed for user {uid}: {e}")

        return {
            "status": "completed",
            "organization_id": organization_id,
            "users_checked": len(users_to_check),
            "total_badges_awarded": total_awarded,
            "user_results": user_results,
        }


# =============================================================================
# Helper functions for triggering badge checks from other modules
# =============================================================================

async def trigger_badge_check(
    user_id: UUID,
    organization_id: UUID,
    action: str,
) -> None:
    """Trigger an async badge check after a user action.

    This is a convenience function to enqueue a badge check job.
    It's safe to call this even if arq is not available - failures are logged
    but don't affect the main operation.

    Args:
        user_id: User who performed the action.
        organization_id: Organization the user belongs to.
        action: Description of the action (for logging).
    """
    try:
        from paper_scraper.jobs.worker import enqueue_job

        await enqueue_job(
            "check_and_award_badges_task",
            str(user_id),
            str(organization_id),
            action,
        )
        logger.debug(f"Badge check enqueued for user {user_id} after {action}")
    except Exception as e:
        # Don't fail the main operation if badge check fails to enqueue
        logger.warning(f"Failed to enqueue badge check: {e}")
