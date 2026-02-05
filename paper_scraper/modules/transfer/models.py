"""SQLAlchemy models for technology transfer conversations."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base

if TYPE_CHECKING:
    from paper_scraper.modules.auth.models import Organization, User
    from paper_scraper.modules.papers.models import Author, Paper


class TransferType(str, enum.Enum):
    """Type of technology transfer."""

    PATENT = "patent"
    LICENSING = "licensing"
    STARTUP = "startup"
    PARTNERSHIP = "partnership"
    OTHER = "other"


class TransferStage(str, enum.Enum):
    """Stage of transfer conversation."""

    INITIAL_CONTACT = "initial_contact"
    DISCOVERY = "discovery"
    EVALUATION = "evaluation"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class TransferConversation(Base):
    """Technology transfer conversation."""

    __tablename__ = "transfer_conversations"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    paper_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("papers.id", ondelete="SET NULL"), nullable=True
    )
    researcher_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("authors.id", ondelete="SET NULL"), nullable=True
    )

    type: Mapped[TransferType] = mapped_column(Enum(TransferType), nullable=False)
    stage: Mapped[TransferStage] = mapped_column(
        Enum(TransferStage), default=TransferStage.INITIAL_CONTACT
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)

    created_by: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
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

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    paper: Mapped["Paper | None"] = relationship("Paper")
    researcher: Mapped["Author | None"] = relationship("Author")
    creator: Mapped["User | None"] = relationship("User", foreign_keys=[created_by])
    messages: Mapped[list["ConversationMessage"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
    resources: Mapped[list["ConversationResource"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
    stage_history: Mapped[list["StageChange"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_transfer_conversations_org_stage", "organization_id", "stage"),
        Index("ix_transfer_conversations_paper", "paper_id"),
        Index("ix_transfer_conversations_researcher", "researcher_id"),
    )

    def __repr__(self) -> str:
        return f"<TransferConversation {self.title} ({self.stage.value})>"


class ConversationMessage(Base):
    """Message in a transfer conversation."""

    __tablename__ = "conversation_messages"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("transfer_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    mentions: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    conversation: Mapped["TransferConversation"] = relationship(
        back_populates="messages"
    )
    sender: Mapped["User | None"] = relationship("User")

    __table_args__ = (
        Index("ix_conversation_messages_conv_created", "conversation_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ConversationMessage {self.id}>"


class ConversationResource(Base):
    """Resource attached to a conversation."""

    __tablename__ = "conversation_resources"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("transfer_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    conversation: Mapped["TransferConversation"] = relationship(
        back_populates="resources"
    )

    def __repr__(self) -> str:
        return f"<ConversationResource {self.name}>"


class StageChange(Base):
    """History of stage changes."""

    __tablename__ = "stage_changes"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("transfer_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_stage: Mapped[TransferStage] = mapped_column(Enum(TransferStage))
    to_stage: Mapped[TransferStage] = mapped_column(Enum(TransferStage))
    changed_by: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    conversation: Mapped["TransferConversation"] = relationship(
        back_populates="stage_history"
    )
    changed_by_user: Mapped["User | None"] = relationship("User")

    def __repr__(self) -> str:
        return f"<StageChange {self.from_stage.value} -> {self.to_stage.value}>"


class MessageTemplate(Base):
    """Reusable message templates."""

    __tablename__ = "message_templates"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    stage: Mapped[TransferStage | None] = mapped_column(
        Enum(TransferStage), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")

    __table_args__ = (
        Index("ix_message_templates_org_stage", "organization_id", "stage"),
    )

    def __repr__(self) -> str:
        return f"<MessageTemplate {self.name}>"
