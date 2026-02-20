"""Database models for organization usage tracking and quota enforcement."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from paper_scraper.core.database import Base


class OrganizationUsage(Base):
    """Monthly usage tracking per organization for quota enforcement.

    Each row tracks one month's usage for one organization. The period
    column is formatted as 'YYYY-MM' for easy aggregation.
    """

    __tablename__ = "organization_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period = Column(String(7), nullable=False)  # 'YYYY-MM'

    # Paper counts
    papers_imported = Column(Integer, nullable=False, default=0)
    papers_scored = Column(Integer, nullable=False, default=0)

    # Token usage
    llm_input_tokens = Column(Integer, nullable=False, default=0)
    llm_output_tokens = Column(Integer, nullable=False, default=0)
    embedding_tokens = Column(Integer, nullable=False, default=0)

    # Cost tracking
    estimated_cost_usd = Column(Numeric(10, 4), nullable=False, default=0)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (UniqueConstraint("organization_id", "period", name="uq_org_usage_period"),)
