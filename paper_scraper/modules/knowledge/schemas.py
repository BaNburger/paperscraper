"""Pydantic schemas for knowledge sources."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from paper_scraper.modules.knowledge.models import KnowledgeScope, KnowledgeType


class KnowledgeSourceBase(BaseModel):
    """Base schema for knowledge source."""

    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1, max_length=50000)
    type: KnowledgeType = KnowledgeType.CUSTOM
    tags: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("tags")
    @classmethod
    def validate_tag_lengths(cls, v: list[str]) -> list[str]:
        for tag in v:
            if not tag or len(tag) > 50:
                raise ValueError("Each tag must be 1-50 characters")
        return v


class KnowledgeSourceCreate(KnowledgeSourceBase):
    """Schema for creating a knowledge source."""

    pass


class KnowledgeSourceUpdate(BaseModel):
    """Schema for updating a knowledge source."""

    title: str | None = Field(None, min_length=1, max_length=255)
    content: str | None = Field(None, min_length=1, max_length=50000)
    type: KnowledgeType | None = None
    tags: list[str] | None = Field(None, max_length=20)

    @field_validator("tags")
    @classmethod
    def validate_tag_lengths(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            for tag in v:
                if not tag or len(tag) > 50:
                    raise ValueError("Each tag must be 1-50 characters")
        return v


class KnowledgeSourceResponse(KnowledgeSourceBase):
    """Response schema for knowledge source."""

    id: UUID
    organization_id: UUID
    user_id: UUID | None
    scope: KnowledgeScope
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeSourceListResponse(BaseModel):
    """Paginated list of knowledge sources."""

    items: list[KnowledgeSourceResponse]
    total: int
    page: int = 1
    page_size: int = 50
    pages: int = 1
