"""Service layer for compliance operations."""

import csv
import io
import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.csv_utils import sanitize_csv_field
from paper_scraper.core.exceptions import NotFoundError, ValidationError
from paper_scraper.modules.audit.models import AuditLog
from paper_scraper.modules.compliance.models import (
    RetentionAction,
    RetentionEntityType,
    RetentionLog,
    RetentionPolicy,
)
from paper_scraper.modules.compliance.schemas import (
    ApplyRetentionResult,
    AuditLogSummary,
    CreateRetentionPolicyRequest,
    DataProcessingInfo,
    RetentionEntityTypeEnum,
    RetentionPolicyResponse,
    UpdateRetentionPolicyRequest,
)
from paper_scraper.modules.compliance.soc2 import get_control_evidence, get_soc2_status


class ComplianceService:
    """Service for compliance and data retention operations."""

    def __init__(self, db: AsyncSession):
        """Initialize compliance service.

        Args:
            db: Async database session.
        """
        self.db = db

    # Retention Policy CRUD

    async def list_retention_policies(
        self,
        organization_id: UUID,
    ) -> list[RetentionPolicy]:
        """List all retention policies for an organization.

        Args:
            organization_id: The organization ID.

        Returns:
            List of retention policies.
        """
        result = await self.db.execute(
            select(RetentionPolicy)
            .where(RetentionPolicy.organization_id == organization_id)
            .order_by(RetentionPolicy.entity_type)
        )
        return list(result.scalars().all())

    async def get_retention_policy(
        self,
        policy_id: UUID,
        organization_id: UUID,
    ) -> RetentionPolicy:
        """Get a specific retention policy.

        Args:
            policy_id: The policy ID.
            organization_id: The organization ID.

        Returns:
            The retention policy.

        Raises:
            NotFoundError: If policy not found.
        """
        result = await self.db.execute(
            select(RetentionPolicy).where(
                RetentionPolicy.id == policy_id,
                RetentionPolicy.organization_id == organization_id,
            )
        )
        policy = result.scalar_one_or_none()
        if not policy:
            raise NotFoundError("RetentionPolicy", str(policy_id))
        return policy

    async def create_retention_policy(
        self,
        organization_id: UUID,
        data: CreateRetentionPolicyRequest,
    ) -> RetentionPolicy:
        """Create a new retention policy.

        Args:
            organization_id: The organization ID.
            data: The policy creation data.

        Returns:
            The created policy.

        Raises:
            ValidationError: If policy for entity type already exists.
        """
        # Check for existing policy for this entity type
        existing = await self.db.execute(
            select(RetentionPolicy).where(
                RetentionPolicy.organization_id == organization_id,
                RetentionPolicy.entity_type == data.entity_type.value,
            )
        )
        if existing.scalar_one_or_none():
            raise ValidationError(
                f"Retention policy for {data.entity_type.value} already exists"
            )

        policy = RetentionPolicy(
            organization_id=organization_id,
            entity_type=data.entity_type.value,
            retention_days=data.retention_days,
            action=data.action.value,
            description=data.description,
            is_active=data.is_active,
        )
        self.db.add(policy)
        await self.db.flush()
        return policy

    async def update_retention_policy(
        self,
        policy_id: UUID,
        organization_id: UUID,
        data: UpdateRetentionPolicyRequest,
    ) -> RetentionPolicy:
        """Update a retention policy.

        Args:
            policy_id: The policy ID.
            organization_id: The organization ID.
            data: The update data.

        Returns:
            The updated policy.
        """
        policy = await self.get_retention_policy(policy_id, organization_id)

        if data.retention_days is not None:
            policy.retention_days = data.retention_days
        if data.action is not None:
            policy.action = data.action.value
        if data.description is not None:
            policy.description = data.description
        if data.is_active is not None:
            policy.is_active = data.is_active

        await self.db.flush()
        await self.db.refresh(policy)
        return policy

    async def delete_retention_policy(
        self,
        policy_id: UUID,
        organization_id: UUID,
    ) -> None:
        """Delete a retention policy.

        Args:
            policy_id: The policy ID.
            organization_id: The organization ID.
        """
        policy = await self.get_retention_policy(policy_id, organization_id)
        await self.db.delete(policy)
        await self.db.flush()

    # Apply Retention

    async def apply_retention_policies(
        self,
        organization_id: UUID,
        dry_run: bool = True,
        entity_types: list[RetentionEntityTypeEnum] | None = None,
    ) -> list[ApplyRetentionResult]:
        """Apply retention policies to data.

        Args:
            organization_id: The organization ID.
            dry_run: If True, only report what would be affected.
            entity_types: Optional list of entity types to process.

        Returns:
            List of results for each processed policy.
        """
        results = []

        # Get active policies
        query = select(RetentionPolicy).where(
            RetentionPolicy.organization_id == organization_id,
            RetentionPolicy.is_active == True,  # noqa: E712
        )
        if entity_types:
            query = query.where(
                RetentionPolicy.entity_type.in_([et.value for et in entity_types])
            )

        policy_result = await self.db.execute(query)
        policies = list(policy_result.scalars().all())

        for policy in policies:
            result = await self._apply_single_policy(policy, dry_run)
            results.append(result)

        return results

    async def _apply_single_policy(
        self,
        policy: RetentionPolicy,
        dry_run: bool,
    ) -> ApplyRetentionResult:
        """Apply a single retention policy.

        Args:
            policy: The retention policy.
            dry_run: If True, only count affected records.

        Returns:
            Result of applying the policy.
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=policy.retention_days)
        records_affected = 0
        status = "completed"

        try:
            if policy.entity_type == RetentionEntityType.AUDIT_LOGS.value:
                records_affected = await self._apply_to_audit_logs(
                    policy.organization_id, cutoff_date, policy.action, dry_run
                )
            elif policy.entity_type == RetentionEntityType.PAPERS.value:
                records_affected = await self._apply_to_papers(
                    policy.organization_id, cutoff_date, policy.action, dry_run
                )
            elif policy.entity_type == RetentionEntityType.CONVERSATIONS.value:
                records_affected = await self._apply_to_conversations(
                    policy.organization_id, cutoff_date, policy.action, dry_run
                )
            elif policy.entity_type == RetentionEntityType.SUBMISSIONS.value:
                records_affected = await self._apply_to_submissions(
                    policy.organization_id, cutoff_date, policy.action, dry_run
                )
            elif policy.entity_type == RetentionEntityType.ALERTS.value:
                records_affected = await self._apply_to_alerts(
                    policy.organization_id, cutoff_date, policy.action, dry_run
                )
            elif policy.entity_type == RetentionEntityType.KNOWLEDGE.value:
                records_affected = await self._apply_to_knowledge(
                    policy.organization_id, cutoff_date, policy.action, dry_run
                )
            elif policy.entity_type == RetentionEntityType.SEARCH_ACTIVITIES.value:
                records_affected = await self._apply_to_search_activities(
                    policy.organization_id, cutoff_date, policy.action, dry_run
                )

            # Update policy tracking
            if not dry_run and records_affected > 0:
                policy.last_applied_at = datetime.now(timezone.utc)
                policy.records_affected += records_affected

            # Log the retention application
            log = RetentionLog(
                organization_id=policy.organization_id,
                policy_id=policy.id,
                entity_type=policy.entity_type,
                action=policy.action,
                records_affected=records_affected,
                is_dry_run=dry_run,
                status=status,
                completed_at=datetime.now(timezone.utc) if not dry_run else None,
            )
            self.db.add(log)

        except Exception as e:
            status = "failed"
            # Log the failure
            log = RetentionLog(
                organization_id=policy.organization_id,
                policy_id=policy.id,
                entity_type=policy.entity_type,
                action=policy.action,
                records_affected=0,
                is_dry_run=dry_run,
                status=status,
                error_message=str(e),
            )
            self.db.add(log)
            await self.db.flush()  # Persist the error log
            raise  # Re-raise to let caller handle the failure

        return ApplyRetentionResult(
            entity_type=policy.entity_type,
            action=policy.action,
            records_affected=records_affected,
            is_dry_run=dry_run,
            status=status,
        )

    async def _apply_to_audit_logs(
        self,
        organization_id: UUID,
        cutoff_date: datetime,
        action: str,
        dry_run: bool,
    ) -> int:
        """Apply retention to audit logs."""
        count_result = await self.db.execute(
            select(func.count(AuditLog.id)).where(
                AuditLog.organization_id == organization_id,
                AuditLog.created_at < cutoff_date,
            )
        )
        count = count_result.scalar() or 0

        if not dry_run and action == RetentionAction.DELETE.value:
            await self.db.execute(
                delete(AuditLog).where(
                    AuditLog.organization_id == organization_id,
                    AuditLog.created_at < cutoff_date,
                )
            )

        return count

    async def _apply_to_papers(
        self,
        organization_id: UUID,
        cutoff_date: datetime,
        action: str,
        dry_run: bool,
    ) -> int:
        """Apply retention to papers."""
        # Import here to avoid circular imports
        from paper_scraper.modules.papers.models import Paper

        count_result = await self.db.execute(
            select(func.count(Paper.id)).where(
                Paper.organization_id == organization_id,
                Paper.created_at < cutoff_date,
            )
        )
        count = count_result.scalar() or 0

        if not dry_run:
            if action == RetentionAction.DELETE.value:
                await self.db.execute(
                    delete(Paper).where(
                        Paper.organization_id == organization_id,
                        Paper.created_at < cutoff_date,
                    )
                )
            elif action == RetentionAction.ANONYMIZE.value:
                # Anonymize by clearing personal identifiers
                await self.db.execute(
                    update(Paper)
                    .where(
                        Paper.organization_id == organization_id,
                        Paper.created_at < cutoff_date,
                    )
                    .values(
                        notes=None,
                        pitch=None,
                    )
                )

        return count

    async def _apply_to_conversations(
        self,
        organization_id: UUID,
        cutoff_date: datetime,
        action: str,
        dry_run: bool,
    ) -> int:
        """Apply retention to transfer conversations."""
        from paper_scraper.modules.transfer.models import Conversation

        count_result = await self.db.execute(
            select(func.count(Conversation.id)).where(
                Conversation.organization_id == organization_id,
                Conversation.created_at < cutoff_date,
            )
        )
        count = count_result.scalar() or 0

        if not dry_run and action == RetentionAction.DELETE.value:
            await self.db.execute(
                delete(Conversation).where(
                    Conversation.organization_id == organization_id,
                    Conversation.created_at < cutoff_date,
                )
            )

        return count

    async def _apply_to_submissions(
        self,
        organization_id: UUID,
        cutoff_date: datetime,
        action: str,
        dry_run: bool,
    ) -> int:
        """Apply retention to submissions."""
        from paper_scraper.modules.submissions.models import Submission

        count_result = await self.db.execute(
            select(func.count(Submission.id)).where(
                Submission.organization_id == organization_id,
                Submission.created_at < cutoff_date,
            )
        )
        count = count_result.scalar() or 0

        if not dry_run and action == RetentionAction.DELETE.value:
            await self.db.execute(
                delete(Submission).where(
                    Submission.organization_id == organization_id,
                    Submission.created_at < cutoff_date,
                )
            )

        return count

    async def _apply_to_alerts(
        self,
        organization_id: UUID,
        cutoff_date: datetime,
        action: str,
        dry_run: bool,
    ) -> int:
        """Apply retention to alert results."""
        from paper_scraper.modules.alerts.models import Alert, AlertResult

        # Must filter through Alert table since AlertResult has no org_id column
        org_alert_ids = (
            select(Alert.id).where(Alert.organization_id == organization_id)
        )

        count_result = await self.db.execute(
            select(func.count(AlertResult.id)).where(
                AlertResult.alert_id.in_(org_alert_ids),
                AlertResult.created_at < cutoff_date,
            )
        )
        count = count_result.scalar() or 0

        if not dry_run and action == RetentionAction.DELETE.value:
            await self.db.execute(
                delete(AlertResult).where(
                    AlertResult.alert_id.in_(org_alert_ids),
                    AlertResult.created_at < cutoff_date,
                )
            )

        return count

    async def _apply_to_knowledge(
        self,
        organization_id: UUID,
        cutoff_date: datetime,
        action: str,
        dry_run: bool,
    ) -> int:
        """Apply retention to knowledge sources."""
        from paper_scraper.modules.knowledge.models import KnowledgeSource

        count_result = await self.db.execute(
            select(func.count(KnowledgeSource.id)).where(
                KnowledgeSource.organization_id == organization_id,
                KnowledgeSource.updated_at < cutoff_date,
            )
        )
        count = count_result.scalar() or 0

        if not dry_run and action == RetentionAction.DELETE.value:
            await self.db.execute(
                delete(KnowledgeSource).where(
                    KnowledgeSource.organization_id == organization_id,
                    KnowledgeSource.updated_at < cutoff_date,
                )
            )

        return count

    async def _apply_to_search_activities(
        self,
        organization_id: UUID,
        cutoff_date: datetime,
        action: str,
        dry_run: bool,
    ) -> int:
        """Apply retention to search activities."""
        from paper_scraper.modules.search.models import SearchActivity

        count_result = await self.db.execute(
            select(func.count(SearchActivity.id)).where(
                SearchActivity.organization_id == organization_id,
                SearchActivity.created_at < cutoff_date,
            )
        )
        count = count_result.scalar() or 0

        if not dry_run and action == RetentionAction.DELETE.value:
            await self.db.execute(
                delete(SearchActivity).where(
                    SearchActivity.organization_id == organization_id,
                    SearchActivity.created_at < cutoff_date,
                )
            )

        return count

    # Retention Logs

    async def list_retention_logs(
        self,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[RetentionLog], int]:
        """List retention application logs.

        Args:
            organization_id: The organization ID.
            page: Page number.
            page_size: Items per page.

        Returns:
            Tuple of (logs list, total count).
        """
        # Get total count
        count_result = await self.db.execute(
            select(func.count(RetentionLog.id)).where(
                RetentionLog.organization_id == organization_id
            )
        )
        total = count_result.scalar() or 0

        # Get paginated logs
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(RetentionLog)
            .where(RetentionLog.organization_id == organization_id)
            .order_by(RetentionLog.started_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        logs = list(result.scalars().all())

        return logs, total

    # Audit Log Analysis

    async def get_audit_log_summary(
        self,
        organization_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> AuditLogSummary:
        """Get summary statistics for audit logs.

        Args:
            organization_id: The organization ID.
            start_date: Optional start date filter.
            end_date: Optional end date filter.

        Returns:
            Summary statistics.
        """
        base_query = select(AuditLog).where(
            AuditLog.organization_id == organization_id
        )
        if start_date:
            base_query = base_query.where(AuditLog.created_at >= start_date)
        if end_date:
            base_query = base_query.where(AuditLog.created_at <= end_date)

        # Total count
        total_result = await self.db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total_logs = total_result.scalar() or 0

        # Build date filter conditions for consistent use across all queries
        date_conditions = [AuditLog.organization_id == organization_id]
        if start_date:
            date_conditions.append(AuditLog.created_at >= start_date)
        if end_date:
            date_conditions.append(AuditLog.created_at <= end_date)

        # Count by action
        action_result = await self.db.execute(
            select(AuditLog.action, func.count(AuditLog.id))
            .where(*date_conditions)
            .group_by(AuditLog.action)
        )
        logs_by_action = {row[0]: row[1] for row in action_result}

        # Count by resource type
        resource_result = await self.db.execute(
            select(AuditLog.resource_type, func.count(AuditLog.id))
            .where(
                *date_conditions,
                AuditLog.resource_type.isnot(None),
            )
            .group_by(AuditLog.resource_type)
        )
        logs_by_resource = {row[0]: row[1] for row in resource_result}

        # Top users
        user_result = await self.db.execute(
            select(AuditLog.user_id, func.count(AuditLog.id))
            .where(
                *date_conditions,
                AuditLog.user_id.isnot(None),
            )
            .group_by(AuditLog.user_id)
            .order_by(func.count(AuditLog.id).desc())
            .limit(10)
        )
        logs_by_user = [
            {"user_id": str(row[0]), "count": row[1]} for row in user_result
        ]

        # Time range
        range_result = await self.db.execute(
            select(
                func.min(AuditLog.created_at),
                func.max(AuditLog.created_at),
            ).where(*date_conditions)
        )
        range_row = range_result.first()
        time_range = {
            "earliest": range_row[0].isoformat() if range_row and range_row[0] else None,
            "latest": range_row[1].isoformat() if range_row and range_row[1] else None,
        }

        return AuditLogSummary(
            total_logs=total_logs,
            logs_by_action=logs_by_action,
            logs_by_resource_type=logs_by_resource,
            logs_by_user=logs_by_user,
            time_range=time_range,
        )

    async def export_audit_logs_csv(
        self,
        organization_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        actions: list[str] | None = None,
    ) -> str:
        """Export audit logs to CSV format.

        Args:
            organization_id: The organization ID.
            start_date: Optional start date filter.
            end_date: Optional end date filter.
            actions: Optional list of action types to include.

        Returns:
            CSV string.
        """
        query = select(AuditLog).where(AuditLog.organization_id == organization_id)

        if start_date:
            query = query.where(AuditLog.created_at >= start_date)
        if end_date:
            query = query.where(AuditLog.created_at <= end_date)
        if actions:
            query = query.where(AuditLog.action.in_(actions))

        query = query.order_by(AuditLog.created_at.desc())

        result = await self.db.execute(query)
        logs = list(result.scalars().all())

        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "ID",
            "Timestamp",
            "User ID",
            "Action",
            "Resource Type",
            "Resource ID",
            "IP Address",
            "User Agent",
            "Details",
        ])

        # Data rows (sanitize to prevent CSV formula injection)
        for log in logs:
            writer.writerow([
                str(log.id),
                log.created_at.isoformat(),
                str(log.user_id) if log.user_id else "",
                sanitize_csv_field(log.action),
                sanitize_csv_field(log.resource_type or ""),
                str(log.resource_id) if log.resource_id else "",
                sanitize_csv_field(log.ip_address or ""),
                sanitize_csv_field(log.user_agent or ""),
                sanitize_csv_field(str(log.details) if log.details else ""),
            ])

        return output.getvalue()

    # SOC2

    def get_soc2_status(self) -> dict:
        """Get SOC2 control status.

        Returns:
            Dict containing control status.
        """
        return get_soc2_status()

    def get_soc2_evidence(self, control_id: str) -> dict | None:
        """Get evidence for a SOC2 control.

        Args:
            control_id: The control ID.

        Returns:
            Dict containing evidence items.
        """
        return get_control_evidence(control_id)

    # Data Processing Info (GDPR)

    async def get_data_processing_info(
        self,
        organization_id: UUID,
    ) -> DataProcessingInfo:
        """Get GDPR data processing transparency information.

        Args:
            organization_id: The organization ID.

        Returns:
            Data processing information.
        """
        # Get retention policies
        policies = await self.list_retention_policies(organization_id)
        policy_responses = [
            RetentionPolicyResponse.model_validate(p) for p in policies
        ]

        return DataProcessingInfo(
            hosting_info={
                "provider": "Cloud Infrastructure",
                "region": "EU (Frankfurt)",
                "certifications": ["ISO 27001", "SOC 2 Type II"],
            },
            data_locations=["EU (Primary)", "US (Backup)"],
            processors=[
                {
                    "name": "OpenAI",
                    "purpose": "AI-powered paper scoring",
                    "data_types": ["Paper abstracts", "Paper metadata"],
                    "location": "US",
                },
                {
                    "name": "Resend",
                    "purpose": "Email delivery",
                    "data_types": ["Email addresses", "Email content"],
                    "location": "US",
                },
                {
                    "name": "Sentry",
                    "purpose": "Error monitoring",
                    "data_types": ["Error logs", "Stack traces"],
                    "location": "EU",
                },
            ],
            retention_policies=policy_responses,
            data_categories=[
                {
                    "category": "User Data",
                    "types": ["Email", "Name", "Password hash"],
                    "purpose": "Account management",
                    "legal_basis": "Contract",
                },
                {
                    "category": "Paper Data",
                    "types": ["DOI", "Title", "Abstract", "Authors"],
                    "purpose": "Core service functionality",
                    "legal_basis": "Contract",
                },
                {
                    "category": "Usage Data",
                    "types": ["Audit logs", "Analytics"],
                    "purpose": "Security and improvement",
                    "legal_basis": "Legitimate interest",
                },
            ],
            legal_basis={
                "processing_grounds": "Contract performance and legitimate interest",
                "dpo_contact": "dpo@paperscraper.io",
                "data_subject_rights": [
                    "Access",
                    "Rectification",
                    "Erasure",
                    "Portability",
                    "Restriction",
                    "Objection",
                ],
            },
        )
