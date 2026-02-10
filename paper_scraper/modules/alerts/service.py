"""Service layer for alerts module."""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from paper_scraper.core.config import settings
from paper_scraper.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from paper_scraper.modules.alerts.email_service import email_service
from paper_scraper.modules.alerts.models import Alert, AlertChannel, AlertResult, AlertStatus
from paper_scraper.modules.alerts.schemas import (
    AlertCreate,
    AlertResponse,
    AlertUpdate,
    SavedSearchBrief,
)
from paper_scraper.modules.notifications.models import NotificationType
from paper_scraper.modules.notifications.service import NotificationService
from paper_scraper.modules.saved_searches.models import SavedSearch
from paper_scraper.modules.search.schemas import SearchFilters, SearchMode, SearchRequest
from paper_scraper.modules.search.service import SearchService

logger = logging.getLogger(__name__)


class AlertService:
    """Service for alert operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        data: AlertCreate,
        organization_id: UUID,
        user_id: UUID,
    ) -> Alert:
        """
        Create a new alert.

        Args:
            data: Alert creation data.
            organization_id: Organization ID for tenant isolation.
            user_id: ID of the user creating the alert.

        Returns:
            Created Alert instance.

        Raises:
            NotFoundError: If saved search not found.
            ForbiddenError: If user doesn't have access to saved search.
        """
        # Verify saved search exists and user has access
        result = await self.db.execute(
            select(SavedSearch).where(
                SavedSearch.id == data.saved_search_id,
                SavedSearch.organization_id == organization_id,
            )
        )
        saved_search = result.scalar_one_or_none()

        if not saved_search:
            raise NotFoundError("SavedSearch", data.saved_search_id)

        # Check access: owner or public
        if saved_search.created_by_id != user_id and not saved_search.is_public:
            raise ForbiddenError("You don't have access to this saved search")

        alert = Alert(
            organization_id=organization_id,
            user_id=user_id,
            saved_search_id=data.saved_search_id,
            name=data.name,
            description=data.description,
            channel=AlertChannel(data.channel.value),
            frequency=data.frequency.value,
            min_results=data.min_results,
        )

        self.db.add(alert)
        await self.db.flush()
        await self.db.refresh(alert, ["saved_search"])

        return alert

    async def get(
        self,
        alert_id: UUID,
        organization_id: UUID,
        user_id: UUID,
    ) -> Alert:
        """
        Get an alert by ID.

        Args:
            alert_id: Alert ID.
            organization_id: Organization ID for tenant isolation.
            user_id: Current user ID.

        Returns:
            Alert instance.

        Raises:
            NotFoundError: If alert not found.
            ForbiddenError: If user doesn't own the alert.
        """
        result = await self.db.execute(
            select(Alert)
            .options(selectinload(Alert.saved_search))
            .where(
                Alert.id == alert_id,
                Alert.organization_id == organization_id,
            )
        )
        alert = result.scalar_one_or_none()

        if not alert:
            raise NotFoundError("Alert", alert_id)

        if alert.user_id != user_id:
            raise ForbiddenError("You don't have access to this alert")

        return alert

    async def list_alerts(
        self,
        organization_id: UUID,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        active_only: bool = False,
    ) -> tuple[list[Alert], int]:
        """
        List alerts for a user.

        Args:
            organization_id: Organization ID for tenant isolation.
            user_id: Current user ID.
            page: Page number.
            page_size: Results per page.
            active_only: Only return active alerts.

        Returns:
            Tuple of (alerts list, total count).
        """
        conditions = [
            Alert.organization_id == organization_id,
            Alert.user_id == user_id,
        ]

        if active_only:
            conditions.append(Alert.is_active == True)  # noqa: E712

        # Count query
        count_query = select(func.count()).select_from(Alert).where(*conditions)
        total = (await self.db.execute(count_query)).scalar() or 0

        # Data query
        query = (
            select(Alert)
            .options(selectinload(Alert.saved_search))
            .where(*conditions)
            .order_by(Alert.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        alerts = list(result.scalars().all())

        return alerts, total

    async def update(
        self,
        alert_id: UUID,
        data: AlertUpdate,
        organization_id: UUID,
        user_id: UUID,
    ) -> Alert:
        """
        Update an alert.

        Args:
            alert_id: Alert ID.
            data: Update data.
            organization_id: Organization ID for tenant isolation.
            user_id: Current user ID.

        Returns:
            Updated Alert instance.

        Raises:
            NotFoundError: If alert not found.
            ForbiddenError: If user doesn't own the alert.
        """
        result = await self.db.execute(
            select(Alert).where(
                Alert.id == alert_id,
                Alert.organization_id == organization_id,
            )
        )
        alert = result.scalar_one_or_none()

        if not alert:
            raise NotFoundError("Alert", alert_id)

        if alert.user_id != user_id:
            raise ForbiddenError("You don't have access to this alert")

        # Apply updates
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "channel" and value:
                value = AlertChannel(value.value if hasattr(value, "value") else value)
            if field == "frequency" and value:
                value = value.value if hasattr(value, "value") else value
            setattr(alert, field, value)

        await self.db.flush()
        # Re-query to get fresh column values (updated_at from onupdate) + relationship
        result = await self.db.execute(
            select(Alert)
            .options(selectinload(Alert.saved_search))
            .where(Alert.id == alert_id)
        )
        alert = result.scalar_one()

        return alert

    async def delete(
        self,
        alert_id: UUID,
        organization_id: UUID,
        user_id: UUID,
    ) -> None:
        """
        Delete an alert.

        Args:
            alert_id: Alert ID.
            organization_id: Organization ID for tenant isolation.
            user_id: Current user ID.

        Raises:
            NotFoundError: If alert not found.
            ForbiddenError: If user doesn't own the alert.
        """
        result = await self.db.execute(
            select(Alert).where(
                Alert.id == alert_id,
                Alert.organization_id == organization_id,
            )
        )
        alert = result.scalar_one_or_none()

        if not alert:
            raise NotFoundError("Alert", alert_id)

        if alert.user_id != user_id:
            raise ForbiddenError("You don't have access to this alert")

        await self.db.delete(alert)
        await self.db.flush()

    async def get_results(
        self,
        alert_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AlertResult], int]:
        """
        Get results/history for an alert.

        Args:
            alert_id: Alert ID.
            organization_id: Organization ID for tenant isolation.
            user_id: Current user ID.
            page: Page number.
            page_size: Results per page.

        Returns:
            Tuple of (results list, total count).

        Raises:
            NotFoundError: If alert not found.
            ForbiddenError: If user doesn't own the alert.
        """
        # Verify access
        await self.get(alert_id, organization_id, user_id)

        # Count query
        count_query = (
            select(func.count())
            .select_from(AlertResult)
            .where(AlertResult.alert_id == alert_id)
        )
        total = (await self.db.execute(count_query)).scalar() or 0

        # Data query
        query = (
            select(AlertResult)
            .where(AlertResult.alert_id == alert_id)
            .order_by(AlertResult.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        results = list(result.scalars().all())

        return results, total

    async def test_alert(
        self,
        alert_id: UUID,
        organization_id: UUID,
        user_id: UUID,
    ) -> dict:
        """
        Test an alert by running its search (without sending notification).

        Args:
            alert_id: Alert ID.
            organization_id: Organization ID for tenant isolation.
            user_id: Current user ID.

        Returns:
            Test results with sample papers.
        """
        alert = await self.get(alert_id, organization_id, user_id)
        saved_search = alert.saved_search

        if not saved_search:
            raise ValidationError("Alert has no associated saved search")

        # Execute search
        search_service = SearchService(self.db)
        filters = SearchFilters(**saved_search.filters) if saved_search.filters else None

        search_request = SearchRequest(
            query=saved_search.query,
            mode=SearchMode(saved_search.mode),
            filters=filters,
            page=1,
            page_size=5,
        )

        search_response = await search_service.search(search_request, organization_id)

        return {
            "success": True,
            "message": f"Found {search_response.total} papers matching the search",
            "papers_found": search_response.total,
            "sample_papers": [
                {
                    "id": str(item.id),
                    "title": item.title,
                    "journal": item.journal,
                    "publication_date": item.publication_date.isoformat() if item.publication_date else None,
                }
                for item in search_response.items
            ],
        }

    async def process_alerts(
        self,
        frequency: str,
    ) -> dict:
        """
        Process all alerts for a given frequency.

        This is called by the background job.

        Args:
            frequency: Alert frequency to process (daily, weekly).

        Returns:
            Processing summary.
        """
        # Get all active alerts for this frequency
        result = await self.db.execute(
            select(Alert)
            .options(
                selectinload(Alert.saved_search),
                selectinload(Alert.user),
            )
            .where(
                Alert.is_active == True,  # noqa: E712
                Alert.frequency == frequency,
            )
        )
        alerts = list(result.scalars().all())

        processed = 0
        sent = 0
        skipped = 0
        failed = 0

        for alert in alerts:
            try:
                result = await self._process_single_alert(alert)
                processed += 1
                if result == "sent":
                    sent += 1
                elif result == "skipped":
                    skipped += 1
            except Exception as e:
                logger.exception(f"Failed to process alert {alert.id}: {e}")
                failed += 1

        return {
            "frequency": frequency,
            "total_alerts": len(alerts),
            "processed": processed,
            "sent": sent,
            "skipped": skipped,
            "failed": failed,
        }

    async def _process_single_alert(
        self,
        alert: Alert,
    ) -> str:
        """
        Process a single alert.

        Args:
            alert: Alert to process.

        Returns:
            Result status (sent, skipped, failed).
        """
        saved_search = alert.saved_search
        if not saved_search:
            return "skipped"

        # Determine time window based on frequency
        if alert.frequency == "daily":
            since = datetime.now(timezone.utc) - timedelta(days=1)
        elif alert.frequency == "weekly":
            since = datetime.now(timezone.utc) - timedelta(days=7)
        else:  # immediately - use last trigger time
            since = alert.last_triggered_at or (datetime.now(timezone.utc) - timedelta(hours=1))

        # Execute search
        search_service = SearchService(self.db)
        filters_dict = saved_search.filters.copy() if saved_search.filters else {}

        # "New" should be based on ingestion freshness, not publication date.
        if "ingested_from" not in filters_dict or not filters_dict.get("ingested_from"):
            filters_dict["ingested_from"] = since.isoformat()

        filters = SearchFilters(**filters_dict) if filters_dict else None

        search_request = SearchRequest(
            query=saved_search.query,
            mode=SearchMode(saved_search.mode),
            filters=filters,
            page=1,
            page_size=50,
        )

        search_response = await search_service.search(search_request, alert.organization_id)

        # Create alert result
        alert_result = AlertResult(
            alert_id=alert.id,
            papers_found=search_response.total,
            new_papers=len(search_response.items),
            paper_ids=[str(item.id) for item in search_response.items],
        )
        self.db.add(alert_result)

        # Check if we have enough results to trigger
        if len(search_response.items) < alert.min_results:
            alert_result.status = AlertStatus.SKIPPED
            await self.db.flush()
            return "skipped"

        # Send notification
        try:
            if alert.channel == AlertChannel.EMAIL and alert.user and alert.user.email:
                view_url = f"{settings.FRONTEND_URL}/saved-searches/{saved_search.id}/results"

                await email_service.send_alert_notification(
                    to=alert.user.email,
                    alert_name=alert.name,
                    search_query=saved_search.query,
                    new_papers_count=len(search_response.items),
                    papers=[
                        {
                            "id": str(item.id),
                            "title": item.title,
                            "journal": item.journal,
                            "publication_date": item.publication_date.isoformat() if item.publication_date else None,
                        }
                        for item in search_response.items
                    ],
                    view_url=view_url,
                )

            alert_result.status = AlertStatus.SENT
            alert_result.delivered_at = datetime.now(timezone.utc)
            alert.last_triggered_at = datetime.now(timezone.utc)
            alert.trigger_count += 1

            # Create in-app notification
            notification_service = NotificationService(self.db)
            await notification_service.create(
                user_id=alert.user_id,
                organization_id=alert.organization_id,
                type=NotificationType.ALERT,
                title=f"Alert: {alert.name}",
                message=f"Found {len(search_response.items)} new papers ({search_response.total} total)",
                resource_type="alert",
                resource_id=str(alert.id),
                metadata={
                    "alert_result_id": str(alert_result.id),
                    "papers_found": search_response.total,
                    "new_papers": len(search_response.items),
                },
            )

            await self.db.flush()
            return "sent"

        except Exception as e:
            logger.exception(f"Failed to send alert notification: {e}")
            alert_result.status = AlertStatus.FAILED
            alert_result.error_message = str(e)[:500]
            await self.db.flush()
            return "failed"

    def to_response(
        self,
        alert: Alert,
    ) -> AlertResponse:
        """
        Convert an Alert model to response schema.

        Args:
            alert: Alert model instance.

        Returns:
            AlertResponse schema.
        """
        saved_search_brief = None
        if alert.saved_search:
            saved_search_brief = SavedSearchBrief(
                id=alert.saved_search.id,
                name=alert.saved_search.name,
                query=alert.saved_search.query,
            )

        return AlertResponse(
            id=alert.id,
            name=alert.name,
            description=alert.description,
            channel=alert.channel.value,
            frequency=alert.frequency,
            min_results=alert.min_results,
            is_active=alert.is_active,
            last_triggered_at=alert.last_triggered_at,
            trigger_count=alert.trigger_count,
            saved_search=saved_search_brief,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
        )
