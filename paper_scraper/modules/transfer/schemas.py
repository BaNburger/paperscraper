"""Pydantic schemas for technology transfer module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from paper_scraper.modules.transfer.models import TransferStage, TransferType


# =============================================================================
# Conversation Schemas
# =============================================================================


class ConversationCreate(BaseModel):
    """Schema for creating a transfer conversation."""

    title: str = Field(max_length=500)
    type: TransferType
    paper_id: UUID | None = None
    researcher_id: UUID | None = None


class ConversationUpdate(BaseModel):
    """Schema for updating a transfer conversation (stage transition)."""

    stage: TransferStage
    notes: str | None = Field(default=None, description="Notes for the stage change")


class ConversationResponse(BaseModel):
    """Response schema for a transfer conversation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    paper_id: UUID | None = None
    researcher_id: UUID | None = None
    type: TransferType
    stage: TransferStage
    title: str
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    resource_count: int = 0


class ConversationDetailResponse(ConversationResponse):
    """Detailed conversation response with messages, resources, and history."""

    messages: list["MessageResponse"] = Field(default_factory=list)
    resources: list["ResourceResponse"] = Field(default_factory=list)
    stage_history: list["StageChangeResponse"] = Field(default_factory=list)
    creator_name: str | None = None
    paper_title: str | None = None
    researcher_name: str | None = None


class ConversationListResponse(BaseModel):
    """Paginated list of conversations."""

    items: list[ConversationResponse]
    total: int
    page: int
    page_size: int
    pages: int


# =============================================================================
# Message Schemas
# =============================================================================


class MessageCreate(BaseModel):
    """Schema for creating a conversation message."""

    content: str = Field(min_length=1, max_length=50000)
    mentions: list[UUID] = Field(default_factory=list, max_length=50)


class MessageFromTemplateCreate(BaseModel):
    """Schema for creating a message from a template."""

    template_id: UUID
    mentions: list[UUID] = Field(default_factory=list)


class MessageResponse(BaseModel):
    """Response schema for a conversation message."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    sender_id: UUID | None = None
    content: str
    mentions: list[UUID] = Field(default_factory=list)
    created_at: datetime
    sender_name: str | None = None


# =============================================================================
# Resource Schemas
# =============================================================================


class ResourceCreate(BaseModel):
    """Schema for attaching a resource to a conversation."""

    name: str = Field(max_length=255)
    url: str | None = Field(default=None, max_length=1000)
    file_path: str | None = Field(default=None, max_length=500)
    resource_type: str = Field(
        max_length=50, description="Type of resource: file, link, document"
    )


class ResourceResponse(BaseModel):
    """Response schema for a conversation resource."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    name: str
    url: str | None = None
    file_path: str | None = None
    resource_type: str
    created_at: datetime


# =============================================================================
# Stage Change Schemas
# =============================================================================


class StageChangeResponse(BaseModel):
    """Response schema for a stage change."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    from_stage: TransferStage
    to_stage: TransferStage
    changed_by: UUID | None = None
    notes: str | None = None
    changed_at: datetime
    changed_by_name: str | None = None


# =============================================================================
# Template Schemas
# =============================================================================


class TemplateCreate(BaseModel):
    """Schema for creating a message template."""

    name: str = Field(max_length=255)
    subject: str | None = Field(default=None, max_length=500)
    content: str = Field(max_length=50000)
    stage: TransferStage | None = None


class TemplateUpdate(BaseModel):
    """Schema for updating a message template."""

    name: str | None = Field(default=None, max_length=255)
    subject: str | None = Field(default=None, max_length=500)
    content: str | None = Field(default=None, max_length=50000)
    stage: TransferStage | None = None


class TemplateResponse(BaseModel):
    """Response schema for a message template."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    subject: str | None = None
    content: str
    stage: TransferStage | None = None
    created_at: datetime


# =============================================================================
# AI Next Steps Schema
# =============================================================================


class NextStep(BaseModel):
    """A suggested next step for a conversation."""

    action: str = Field(description="What action to take")
    priority: str = Field(description="high, medium, or low")
    rationale: str = Field(description="Why this step is recommended")
    suggested_template: str | None = Field(
        default=None,
        description="Name of recommended message template to use",
    )


class NextStepsResponse(BaseModel):
    """AI-suggested next steps for a conversation."""

    conversation_id: UUID
    steps: list[NextStep]
    summary: str = Field(description="Brief summary of current conversation status")
    stage_recommendation: str | None = Field(
        default=None,
        description="Recommendation to move to a different stage with reasoning",
    )


# Resolve forward references
ConversationDetailResponse.model_rebuild()
