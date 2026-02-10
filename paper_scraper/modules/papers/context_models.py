"""SQLAlchemy models for paper enrichment context snapshots."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base

if TYPE_CHECKING:
    from paper_scraper.modules.auth.models import Organization
    from paper_scraper.modules.papers.models import Paper


class PaperContextSnapshot(Base):
    """Versioned, tenant-scoped enrichment context snapshot for scoring."""

    __tablename__ = "paper_context_snapshots"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    paper_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    enrichment_version: Mapped[str] = mapped_column(String(64), nullable=False, default="v1")
    context_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    freshness_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
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

    paper: Mapped["Paper"] = relationship("Paper")
    organization: Mapped["Organization"] = relationship("Organization")

    __table_args__ = (
        Index(
            "ix_paper_context_snapshots_org_paper_version",
            "organization_id",
            "paper_id",
            "enrichment_version",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return f"<PaperContextSnapshot paper={self.paper_id} version={self.enrichment_version}>"
