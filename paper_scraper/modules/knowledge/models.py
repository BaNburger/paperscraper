"""SQLAlchemy models for knowledge sources."""

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from paper_scraper.core.database import Base


class KnowledgeScope(str, enum.Enum):
    """Scope of a knowledge source."""

    PERSONAL = "personal"
    ORGANIZATION = "organization"


class KnowledgeType(str, enum.Enum):
    """Type of knowledge source."""

    RESEARCH_FOCUS = "research_focus"
    INDUSTRY_CONTEXT = "industry_context"
    EVALUATION_CRITERIA = "evaluation_criteria"
    DOMAIN_EXPERTISE = "domain_expertise"
    CUSTOM = "custom"


KNOWLEDGE_SCOPE_ENUM = Enum(
    KnowledgeScope,
    name="knowledgescope",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)

KNOWLEDGE_TYPE_ENUM = Enum(
    KnowledgeType,
    name="knowledgetype",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)


class KnowledgeSource(Base):
    """Knowledge source for AI personalization.

    Can be personal (per-user) or organizational (shared across org).
    Used to contextualize AI scoring and analysis prompts.
    """

    __tablename__ = "knowledge_sources"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    scope: Mapped[KnowledgeScope] = mapped_column(
        KNOWLEDGE_SCOPE_ENUM, nullable=False
    )
    type: Mapped[KnowledgeType] = mapped_column(
        KNOWLEDGE_TYPE_ENUM, nullable=False, default=KnowledgeType.CUSTOM
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<KnowledgeSource {self.title} ({self.scope.value})>"
