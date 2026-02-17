"""SQLAlchemy models for model settings module."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base

if TYPE_CHECKING:
    from paper_scraper.modules.auth.models import Organization, User


class ModelConfiguration(Base):
    """AI model configuration per organization."""

    __tablename__ = "model_configurations"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    hosting_info: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="4096")
    temperature: Mapped[float] = mapped_column(Float, nullable=False, server_default="0.3")
    workflow: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")

    __table_args__ = (
        Index("ix_model_configurations_org_default", "organization_id", "is_default"),
        Index("ix_model_configurations_org_workflow", "organization_id", "workflow"),
    )

    def __repr__(self) -> str:
        return f"<ModelConfiguration {self.provider}/{self.model_name} org={self.organization_id}>"


class ModelUsage(Base):
    """Track model usage and costs per organization."""

    __tablename__ = "model_usage"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_configuration_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("model_configurations.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    operation: Mapped[str] = mapped_column(String(50), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    model_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    model_configuration: Mapped["ModelConfiguration | None"] = relationship("ModelConfiguration")

    __table_args__ = (
        Index("ix_model_usage_org_created", "organization_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ModelUsage {self.operation} tokens={self.input_tokens + self.output_tokens}>"
