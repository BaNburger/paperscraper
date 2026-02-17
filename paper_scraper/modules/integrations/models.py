"""SQLAlchemy models for external data integration connectors."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base

if TYPE_CHECKING:
    from paper_scraper.modules.auth.models import Organization


class ConnectorType(str, enum.Enum):
    """Supported connector categories."""

    MARKET_FEED = "market_feed"
    PATENT_EPO = "patent_epo"
    RESEARCH_GRAPH = "research_graph"
    CUSTOM = "custom"


class ConnectorStatus(str, enum.Enum):
    """Operational status for a connector."""

    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"


class IntegrationConnector(Base):
    """Tenant-scoped external integration connector configuration."""

    __tablename__ = "integration_connectors"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    connector_type: Mapped[ConnectorType] = mapped_column(
        Enum(ConnectorType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    config_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[ConnectorStatus] = mapped_column(
        Enum(ConnectorStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ConnectorStatus.ACTIVE,
    )
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    organization: Mapped["Organization"] = relationship("Organization")

    __table_args__ = (
        Index("ix_integration_connectors_org_type", "organization_id", "connector_type"),
    )

    def __repr__(self) -> str:
        return f"<IntegrationConnector {self.connector_type.value} org={self.organization_id}>"


class ZoteroConnectionStatus(str, enum.Enum):
    """Status of Zotero integration connection."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class ZoteroSyncDirection(str, enum.Enum):
    """Sync direction for Zotero runs."""

    OUTBOUND = "outbound"
    INBOUND = "inbound"


class ZoteroSyncRunStatus(str, enum.Enum):
    """Lifecycle status for Zotero sync runs."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ZoteroConnection(Base):
    """Organization-scoped Zotero API connection."""

    __tablename__ = "zotero_connections"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    api_key: Mapped[str] = mapped_column(Text, nullable=False)
    base_url: Mapped[str] = mapped_column(String(255), nullable=False, default="https://api.zotero.org")
    library_type: Mapped[str] = mapped_column(String(16), nullable=False, default="users")
    status: Mapped[ZoteroConnectionStatus] = mapped_column(
        Enum(ZoteroConnectionStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ZoteroConnectionStatus.CONNECTED,
        index=True,
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    organization: Mapped["Organization"] = relationship("Organization")

    def __repr__(self) -> str:
        return f"<ZoteroConnection org={self.organization_id} status={self.status.value}>"


class ZoteroItemLink(Base):
    """Mapping between local papers and Zotero item keys."""

    __tablename__ = "zotero_item_links"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    paper_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    zotero_item_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    zotero_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_zotero_item_links_org_paper_active",
            "organization_id",
            "paper_id",
            "is_active",
        ),
        Index(
            "uq_zotero_item_links",
            "organization_id",
            "paper_id",
            "zotero_item_key",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return f"<ZoteroItemLink paper={self.paper_id} item={self.zotero_item_key}>"


class ZoteroSyncRun(Base):
    """Track outbound/inbound Zotero synchronization runs."""

    __tablename__ = "zotero_sync_runs"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    direction: Mapped[ZoteroSyncDirection] = mapped_column(
        Enum(ZoteroSyncDirection, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    status: Mapped[ZoteroSyncRunStatus] = mapped_column(
        Enum(ZoteroSyncRunStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ZoteroSyncRunStatus.QUEUED,
        index=True,
    )
    triggered_by: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stats_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index(
            "ix_zotero_sync_runs_org_direction_started",
            "organization_id",
            "direction",
            "started_at",
        ),
    )

    def __repr__(self) -> str:
        return f"<ZoteroSyncRun {self.direction.value} {self.status.value}>"
