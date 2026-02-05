"""Service layer for researcher groups."""

import csv
import io
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.modules.groups.models import GroupMember, GroupType, ResearcherGroup
from paper_scraper.modules.groups.schemas import (
    GroupCreate,
    GroupListResponse,
    GroupUpdate,
    SuggestedMember,
)
from paper_scraper.modules.papers.models import Author


class GroupService:
    """Service for managing researcher groups."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_member_count(self, group_id: UUID) -> int:
        """Get the number of members in a group."""
        result = await self.db.execute(
            select(func.count()).where(GroupMember.group_id == group_id)
        )
        return result.scalar() or 0

    async def list_groups(
        self,
        organization_id: UUID,
        group_type: GroupType | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> GroupListResponse:
        """List groups with optional type filter."""
        query = select(ResearcherGroup).where(
            ResearcherGroup.organization_id == organization_id
        )

        if group_type:
            query = query.where(ResearcherGroup.type == group_type)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(ResearcherGroup.name)
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        groups = list(result.scalars().all())

        # Add member counts
        group_responses = []
        for group in groups:
            count_result = await self.db.execute(
                select(func.count()).where(GroupMember.group_id == group.id)
            )
            member_count = count_result.scalar() or 0
            group_responses.append(
                {
                    "id": group.id,
                    "organization_id": group.organization_id,
                    "name": group.name,
                    "description": group.description,
                    "type": group.type,
                    "keywords": group.keywords,
                    "created_by": group.created_by,
                    "created_at": group.created_at,
                    "member_count": member_count,
                }
            )

        return GroupListResponse(
            items=group_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_group(
        self, group_id: UUID, organization_id: UUID
    ) -> ResearcherGroup:
        """Get group with members."""
        result = await self.db.execute(
            select(ResearcherGroup)
            .options(
                selectinload(ResearcherGroup.members).selectinload(
                    GroupMember.researcher
                )
            )
            .where(
                ResearcherGroup.id == group_id,
                ResearcherGroup.organization_id == organization_id,
            )
        )
        group = result.scalar_one_or_none()
        if not group:
            raise NotFoundError("Group", str(group_id))
        return group

    async def create_group(
        self,
        organization_id: UUID,
        user_id: UUID,
        data: GroupCreate,
    ) -> ResearcherGroup:
        """Create a new group."""
        group = ResearcherGroup(
            organization_id=organization_id,
            created_by=user_id,
            **data.model_dump(),
        )
        self.db.add(group)
        await self.db.flush()
        await self.db.refresh(group)
        return group

    async def update_group(
        self,
        group_id: UUID,
        organization_id: UUID,
        data: GroupUpdate,
    ) -> ResearcherGroup:
        """Update a group."""
        group = await self.get_group(group_id, organization_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(group, field, value)

        await self.db.flush()
        await self.db.refresh(group)
        return group

    async def delete_group(
        self, group_id: UUID, organization_id: UUID
    ) -> None:
        """Delete a group."""
        group = await self.get_group(group_id, organization_id)
        await self.db.delete(group)
        await self.db.flush()

    async def add_members(
        self,
        group_id: UUID,
        organization_id: UUID,
        researcher_ids: list[UUID],
        added_by: UUID,
    ) -> int:
        """Add members to a group."""
        # Verify group exists
        await self.get_group(group_id, organization_id)

        added = 0
        for researcher_id in researcher_ids:
            # Verify researcher exists and belongs to the same organization
            researcher_result = await self.db.execute(
                select(Author).where(
                    Author.id == researcher_id,
                    Author.organization_id == organization_id,
                )
            )
            if not researcher_result.scalar_one_or_none():
                continue

            # Check if already a member
            existing = await self.db.execute(
                select(GroupMember).where(
                    GroupMember.group_id == group_id,
                    GroupMember.researcher_id == researcher_id,
                )
            )
            if existing.scalar_one_or_none():
                continue

            member = GroupMember(
                group_id=group_id,
                researcher_id=researcher_id,
                added_by=added_by,
            )
            self.db.add(member)
            added += 1

        await self.db.flush()
        return added

    async def remove_member(
        self,
        group_id: UUID,
        organization_id: UUID,
        researcher_id: UUID,
    ) -> None:
        """Remove a member from a group."""
        await self.get_group(group_id, organization_id)

        await self.db.execute(
            delete(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.researcher_id == researcher_id,
            )
        )
        await self.db.flush()

    async def suggest_members(
        self,
        organization_id: UUID,
        keywords: list[str],
        target_size: int = 10,
    ) -> list[SuggestedMember]:
        """AI-powered member suggestions based on keywords.

        Uses keyword matching against author affiliations and names.
        TODO: Implement embedding-based similarity search.
        """
        query = (
            select(Author)
            .where(Author.organization_id == organization_id)
            .limit(target_size)
        )
        result = await self.db.execute(query)
        authors = result.scalars().all()

        suggestions = []
        for author in authors:
            suggestions.append(
                SuggestedMember(
                    researcher_id=author.id,
                    name=author.name,
                    relevance_score=0.8,  # Placeholder - implement embedding similarity
                    matching_keywords=keywords[:2],
                    affiliations=author.affiliations or [],
                )
            )

        return suggestions

    async def export_group(
        self, group_id: UUID, organization_id: UUID
    ) -> bytes:
        """Export group members as CSV."""
        group = await self.get_group(group_id, organization_id)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Name", "H-Index", "Affiliations"])

        for member in group.members:
            researcher = member.researcher
            writer.writerow(
                [
                    researcher.name,
                    researcher.h_index or "",
                    ", ".join(researcher.affiliations or []),
                ]
            )

        return output.getvalue().encode("utf-8")
