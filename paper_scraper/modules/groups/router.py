"""FastAPI router for researcher groups."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser
from paper_scraper.core.database import get_db
from paper_scraper.modules.groups.models import GroupType
from paper_scraper.modules.groups.schemas import (
    AddMembersRequest,
    GroupCreate,
    GroupDetail,
    GroupListResponse,
    GroupResponse,
    GroupUpdate,
    SuggestMembersRequest,
    SuggestMembersResponse,
)
from paper_scraper.modules.groups.service import GroupService

router = APIRouter()


def get_group_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GroupService:
    return GroupService(db)


@router.get("/", response_model=GroupListResponse)
async def list_groups(
    current_user: CurrentUser,
    service: Annotated[GroupService, Depends(get_group_service)],
    type: GroupType | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """List researcher groups."""
    return await service.list_groups(
        current_user.organization_id,
        group_type=type,
        page=page,
        page_size=page_size,
    )


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: GroupCreate,
    current_user: CurrentUser,
    service: Annotated[GroupService, Depends(get_group_service)],
):
    """Create a new researcher group."""
    group = await service.create_group(
        current_user.organization_id,
        current_user.id,
        data,
    )
    return GroupResponse(
        id=group.id,
        organization_id=group.organization_id,
        name=group.name,
        description=group.description,
        type=group.type,
        keywords=group.keywords,
        created_by=group.created_by,
        created_at=group.created_at,
        member_count=0,
    )


@router.get("/{group_id}", response_model=GroupDetail)
async def get_group(
    group_id: UUID,
    current_user: CurrentUser,
    service: Annotated[GroupService, Depends(get_group_service)],
):
    """Get group details with members."""
    group = await service.get_group(group_id, current_user.organization_id)
    members = [
        {
            "researcher_id": m.researcher_id,
            "researcher_name": m.researcher.name,
            "researcher_email": None,
            "h_index": m.researcher.h_index,
            "added_at": m.added_at,
        }
        for m in group.members
    ]
    return GroupDetail(
        id=group.id,
        organization_id=group.organization_id,
        name=group.name,
        description=group.description,
        type=group.type,
        keywords=group.keywords,
        created_by=group.created_by,
        created_at=group.created_at,
        member_count=len(group.members),
        members=members,
    )


@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: UUID,
    data: GroupUpdate,
    current_user: CurrentUser,
    service: Annotated[GroupService, Depends(get_group_service)],
):
    """Update a group."""
    group = await service.update_group(
        group_id, current_user.organization_id, data
    )
    member_count = await service.get_member_count(group.id)
    return GroupResponse(
        id=group.id,
        organization_id=group.organization_id,
        name=group.name,
        description=group.description,
        type=group.type,
        keywords=group.keywords,
        created_by=group.created_by,
        created_at=group.created_at,
        member_count=member_count,
    )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: UUID,
    current_user: CurrentUser,
    service: Annotated[GroupService, Depends(get_group_service)],
):
    """Delete a group."""
    await service.delete_group(group_id, current_user.organization_id)


@router.post("/{group_id}/members", status_code=status.HTTP_201_CREATED)
async def add_members(
    group_id: UUID,
    data: AddMembersRequest,
    current_user: CurrentUser,
    service: Annotated[GroupService, Depends(get_group_service)],
):
    """Add members to a group."""
    added = await service.add_members(
        group_id,
        current_user.organization_id,
        data.researcher_ids,
        current_user.id,
    )
    return {"added": added}


@router.delete(
    "/{group_id}/members/{researcher_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_member(
    group_id: UUID,
    researcher_id: UUID,
    current_user: CurrentUser,
    service: Annotated[GroupService, Depends(get_group_service)],
):
    """Remove a member from a group."""
    await service.remove_member(
        group_id, current_user.organization_id, researcher_id
    )


@router.post("/suggest-members", response_model=SuggestMembersResponse)
async def suggest_members(
    data: SuggestMembersRequest,
    current_user: CurrentUser,
    service: Annotated[GroupService, Depends(get_group_service)],
):
    """Get AI-suggested members based on keywords."""
    suggestions = await service.suggest_members(
        current_user.organization_id,
        data.keywords,
        data.target_size,
    )
    return SuggestMembersResponse(
        suggestions=suggestions,
        query_keywords=data.keywords,
    )


@router.get("/{group_id}/export")
async def export_group(
    group_id: UUID,
    current_user: CurrentUser,
    service: Annotated[GroupService, Depends(get_group_service)],
):
    """Export group members as CSV."""
    csv_data = await service.export_group(
        group_id, current_user.organization_id
    )
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=group_{group_id}.csv"
        },
    )
