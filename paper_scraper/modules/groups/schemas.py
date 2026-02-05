"""Pydantic schemas for researcher groups."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from paper_scraper.modules.groups.models import GroupType


class GroupMemberResponse(BaseModel):
    """Response schema for group member."""

    researcher_id: UUID
    researcher_name: str
    researcher_email: str | None = None
    h_index: int | None = None
    added_at: datetime

    model_config = {"from_attributes": True}


class GroupBase(BaseModel):
    """Base schema for group."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    type: GroupType = GroupType.CUSTOM
    keywords: list[str] = Field(default_factory=list)


class GroupCreate(GroupBase):
    """Schema for creating a group."""

    pass


class GroupUpdate(BaseModel):
    """Schema for updating a group."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    type: GroupType | None = None
    keywords: list[str] | None = None


class GroupResponse(GroupBase):
    """Response schema for group."""

    id: UUID
    organization_id: UUID
    created_by: UUID | None
    created_at: datetime
    member_count: int = 0

    model_config = {"from_attributes": True}


class GroupDetail(GroupResponse):
    """Detailed response schema for group with members."""

    members: list[GroupMemberResponse] = Field(default_factory=list)


class GroupListResponse(BaseModel):
    """Paginated list of groups."""

    items: list[GroupResponse]
    total: int
    page: int
    page_size: int


class AddMembersRequest(BaseModel):
    """Request to add members to a group."""

    researcher_ids: list[UUID]


class RemoveMemberRequest(BaseModel):
    """Request to remove a member from a group."""

    researcher_id: UUID


class SuggestMembersRequest(BaseModel):
    """Request for AI-suggested members."""

    keywords: list[str] = Field(..., min_length=1)
    target_size: int = Field(default=10, ge=1, le=50)


class SuggestedMember(BaseModel):
    """AI-suggested group member."""

    researcher_id: UUID
    name: str
    relevance_score: float = Field(..., ge=0, le=1)
    matching_keywords: list[str]
    affiliations: list[str] = Field(default_factory=list)


class SuggestMembersResponse(BaseModel):
    """Response for suggested members."""

    suggestions: list[SuggestedMember]
    query_keywords: list[str]


class GroupExportResponse(BaseModel):
    """Response for group export."""

    group_name: str
    member_count: int
    export_url: str
