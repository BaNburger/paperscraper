"""Service layer for notifications module."""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.notifications.models import Notification, NotificationType

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for notification operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: UUID,
        organization_id: UUID,
        type: NotificationType,
        title: str,
        message: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        metadata: dict | None = None,
    ) -> Notification:
        """Create a new notification.

        Args:
            user_id: ID of the user to notify.
            organization_id: Organization ID for tenant isolation.
            type: Notification type (alert, badge, system).
            title: Notification title.
            message: Optional notification body text.
            resource_type: Optional type of related resource (e.g. "paper", "badge").
            resource_id: Optional ID of the related resource.
            metadata: Optional additional metadata dict.

        Returns:
            Created Notification instance.
        """
        notification = Notification(
            user_id=user_id,
            organization_id=organization_id,
            type=type,
            title=title,
            message=message,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_=metadata or {},
        )

        self.db.add(notification)
        await self.db.flush()

        return notification

    async def list_notifications(
        self,
        user_id: UUID,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False,
    ) -> tuple[list[Notification], int, int]:
        """List notifications for a user with pagination.

        Args:
            user_id: ID of the user.
            organization_id: Organization ID for tenant isolation.
            page: Page number (1-indexed).
            page_size: Number of results per page.
            unread_only: If True, only return unread notifications.

        Returns:
            Tuple of (notifications, total_count, unread_count).
            unread_count is always the total unread regardless of
            pagination or the unread_only filter.
        """
        base_conditions = [
            Notification.user_id == user_id,
            Notification.organization_id == organization_id,
        ]

        # Build filter conditions (may add is_read filter)
        filter_conditions = list(base_conditions)
        if unread_only:
            filter_conditions.append(Notification.is_read == False)  # noqa: E712

        # Count query (respects unread_only filter)
        count_query = (
            select(func.count())
            .select_from(Notification)
            .where(*filter_conditions)
        )
        total = (await self.db.execute(count_query)).scalar() or 0

        # Unread count query (always unfiltered by unread_only)
        unread_query = (
            select(func.count())
            .select_from(Notification)
            .where(
                *base_conditions,
                Notification.is_read == False,  # noqa: E712
            )
        )
        unread_count = (await self.db.execute(unread_query)).scalar() or 0

        # Data query
        query = (
            select(Notification)
            .where(*filter_conditions)
            .order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        notifications = list(result.scalars().all())

        return notifications, total, unread_count

    async def mark_as_read(
        self,
        notification_ids: list[UUID],
        user_id: UUID,
        organization_id: UUID,
    ) -> int:
        """Mark specific notifications as read.

        Args:
            notification_ids: IDs of notifications to mark as read.
            user_id: ID of the user (for ownership verification).
            organization_id: Organization ID for tenant isolation.

        Returns:
            Count of updated notifications.
        """
        stmt = (
            update(Notification)
            .where(
                Notification.id.in_(notification_ids),
                Notification.user_id == user_id,
                Notification.organization_id == organization_id,
                Notification.is_read == False,  # noqa: E712
            )
            .values(is_read=True)
        )

        result = await self.db.execute(stmt)
        await self.db.flush()

        return result.rowcount

    async def mark_all_as_read(
        self,
        user_id: UUID,
        organization_id: UUID,
    ) -> int:
        """Mark all notifications as read for a user.

        Args:
            user_id: ID of the user.
            organization_id: Organization ID for tenant isolation.

        Returns:
            Count of updated notifications.
        """
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.organization_id == organization_id,
                Notification.is_read == False,  # noqa: E712
            )
            .values(is_read=True)
        )

        result = await self.db.execute(stmt)
        await self.db.flush()

        return result.rowcount

    async def get_unread_count(
        self,
        user_id: UUID,
        organization_id: UUID,
    ) -> int:
        """Get the count of unread notifications for a user.

        Args:
            user_id: ID of the user.
            organization_id: Organization ID for tenant isolation.

        Returns:
            Number of unread notifications.
        """
        query = (
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.organization_id == organization_id,
                Notification.is_read == False,  # noqa: E712
            )
        )

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def delete_old(
        self,
        user_id: UUID,
        organization_id: UUID,
        days: int = 90,
    ) -> int:
        """Delete notifications older than a specified number of days.

        Args:
            user_id: ID of the user.
            organization_id: Organization ID for tenant isolation.
            days: Age threshold in days. Notifications older than this
                are deleted. Defaults to 90.

        Returns:
            Count of deleted notifications.
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)

        # Find old notifications
        query = select(Notification).where(
            Notification.user_id == user_id,
            Notification.organization_id == organization_id,
            Notification.created_at < cutoff,
        )

        result = await self.db.execute(query)
        old_notifications = list(result.scalars().all())

        count = len(old_notifications)
        for notification in old_notifications:
            await self.db.delete(notification)

        if count > 0:
            await self.db.flush()
            logger.info(
                "Deleted %d old notifications for user %s (older than %d days)",
                count,
                user_id,
                days,
            )

        return count
