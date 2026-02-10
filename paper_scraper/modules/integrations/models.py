"""SQLAlchemy models for external data integration connectors."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text, Uuid, func
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
