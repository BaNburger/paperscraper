"""SQLAlchemy models for audit logging."""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from paper_scraper.core.database import Base


class AuditAction(str, Enum):
    """Enumeration of auditable actions."""

    # Authentication
    LOGIN = "login"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET_REQUEST = "password_reset_request"
    PASSWORD_RESET = "password_reset"

    # Account management
    REGISTER = "register"
    EMAIL_VERIFY = "email_verify"
    ACCOUNT_DELETE = "account_delete"
    DATA_EXPORT = "data_export"

    # User management
    USER_INVITE = "user_invite"
    USER_INVITE_ACCEPT = "user_invite_accept"
    USER_ROLE_CHANGE = "user_role_change"
    USER_DEACTIVATE = "user_deactivate"
    USER_REACTIVATE = "user_reactivate"

    # Paper operations
    PAPER_CREATE = "paper_create"
    PAPER_DELETE = "paper_delete"
    PAPER_SCORE = "paper_score"

    # Project operations
    PROJECT_CREATE = "project_create"
    PROJECT_DELETE = "project_delete"

    # API access
    API_KEY_CREATE = "api_key_create"
    API_KEY_REVOKE = "api_key_revoke"

    # Group operations
    GROUP_CREATE = "group_create"
    GROUP_UPDATE = "group_update"
    GROUP_DELETE = "group_delete"
    GROUP_MEMBER_ADD = "group_member_add"
    GROUP_MEMBER_REMOVE = "group_member_remove"

    # Transfer operations
    TRANSFER_CREATE = "transfer_create"
    TRANSFER_STAGE_CHANGE = "transfer_stage_change"
    TRANSFER_MESSAGE_SEND = "transfer_message_send"

    # Submission operations
    SUBMISSION_CREATE = "submission_create"
    SUBMISSION_STATUS_CHANGE = "submission_status_change"
    SUBMISSION_REVIEW = "submission_review"

    # Badge operations
    BADGE_AWARD = "badge_award"

    # Knowledge operations
    KNOWLEDGE_CREATE = "knowledge_create"
    KNOWLEDGE_UPDATE = "knowledge_update"
    KNOWLEDGE_DELETE = "knowledge_delete"

    # Admin actions
    ORGANIZATION_UPDATE = "organization_update"
    SUBSCRIPTION_CHANGE = "subscription_change"

    # Token operations
    TOKEN_REFRESH = "token_refresh"

    # Paper pipeline operations
    PAPER_STAGE_CHANGE = "paper_stage_change"
    PAPER_CLASSIFY = "paper_classify"

    # Model settings
    MODEL_CONFIG_CREATE = "model_config_create"
    MODEL_CONFIG_UPDATE = "model_config_update"
    MODEL_CONFIG_DELETE = "model_config_delete"

    # Repository operations
    REPOSITORY_CREATE = "repository_create"
    REPOSITORY_UPDATE = "repository_update"
    REPOSITORY_DELETE = "repository_delete"
    REPOSITORY_SYNC = "repository_sync"

    # Webhook operations
    WEBHOOK_CREATE = "webhook_create"
    WEBHOOK_UPDATE = "webhook_update"
    WEBHOOK_DELETE = "webhook_delete"
    WEBHOOK_TEST = "webhook_test"

    # Saved search operations
    SAVED_SEARCH_CREATE = "saved_search_create"
    SAVED_SEARCH_UPDATE = "saved_search_update"
    SAVED_SEARCH_DELETE = "saved_search_delete"
    SAVED_SEARCH_SHARE = "saved_search_share"

    # Alert operations
    ALERT_CREATE = "alert_create"
    ALERT_UPDATE = "alert_update"
    ALERT_DELETE = "alert_delete"
    ALERT_TRIGGER = "alert_trigger"

    # Report operations
    REPORT_CREATE = "report_create"
    REPORT_UPDATE = "report_update"
    REPORT_DELETE = "report_delete"
    REPORT_RUN = "report_run"

    # Retention operations
    RETENTION_POLICY_APPLY = "retention_policy_apply"


class AuditLog(Base):
    """Audit trail for security-relevant actions.

    This model captures all security-sensitive operations for compliance
    and security monitoring purposes. Each record is immutable once created.
    """

    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Actor information
    user_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), nullable=True, index=True
    )
    organization_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), nullable=True, index=True
    )

    # Action details
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), nullable=True
    )

    # Additional context
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Request metadata
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Timestamp (immutable)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    __table_args__ = (
        # Composite index for organization + time range queries
        Index("ix_audit_logs_org_created", "organization_id", "created_at"),
        # Index for user activity queries
        Index("ix_audit_logs_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation of audit log entry."""
        return f"<AuditLog {self.action} by user={self.user_id} at {self.created_at}>"
