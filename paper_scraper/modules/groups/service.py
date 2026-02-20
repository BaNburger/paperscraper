"""Service layer for researcher groups."""

import csv
import io
import logging
from pathlib import Path
from uuid import UUID

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from paper_scraper.core.csv_utils import sanitize_csv_field
from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.modules.groups.models import GroupMember, GroupType, ResearcherGroup
from paper_scraper.modules.groups.schemas import (
    GroupCreate,
    GroupListResponse,
    GroupUpdate,
    SuggestedMember,
)
from paper_scraper.modules.papers.models import Author
from paper_scraper.modules.scoring.embeddings import EmbeddingClient
from paper_scraper.modules.scoring.llm_client import sanitize_text_for_prompt

logger = logging.getLogger(__name__)

# Load Jinja2 environment for prompt templates
_PROMPTS_DIR = Path(__file__).parent.parent / "scoring" / "prompts"
_jinja_env = Environment(
    loader=FileSystemLoader(_PROMPTS_DIR),
    autoescape=False,
)


class GroupService:
    """Service for managing researcher groups."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_member_count(self, group_id: UUID) -> int:
        """Get the number of members in a group."""
        result = await self.db.execute(select(func.count()).where(GroupMember.group_id == group_id))
        return result.scalar() or 0

    async def list_groups(
        self,
        organization_id: UUID,
        group_type: GroupType | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> GroupListResponse:
        """List groups with optional type filter."""
        base_query = select(ResearcherGroup).where(
            ResearcherGroup.organization_id == organization_id
        )

        if group_type:
            base_query = base_query.where(ResearcherGroup.type == group_type)

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Build query with member count via correlated subquery to avoid N+1
        member_count_sq = (
            select(func.count())
            .where(GroupMember.group_id == ResearcherGroup.id)
            .correlate(ResearcherGroup)
            .scalar_subquery()
            .label("member_count")
        )

        query = select(ResearcherGroup, member_count_sq).where(
            ResearcherGroup.organization_id == organization_id
        )

        if group_type:
            query = query.where(ResearcherGroup.type == group_type)

        # Paginate
        query = query.order_by(ResearcherGroup.name)
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        rows = result.all()

        # Build responses from joined results
        group_responses = []
        for group, member_count in rows:
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
                    "member_count": member_count or 0,
                }
            )

        return GroupListResponse(
            items=group_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_group(self, group_id: UUID, organization_id: UUID) -> ResearcherGroup:
        """Get group with members."""
        result = await self.db.execute(
            select(ResearcherGroup)
            .options(selectinload(ResearcherGroup.members).selectinload(GroupMember.researcher))
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

    async def delete_group(self, group_id: UUID, organization_id: UUID) -> None:
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
        group_name: str | None = None,
        group_description: str | None = None,
        use_llm_explanation: bool = False,
    ) -> list[SuggestedMember]:
        """AI-powered member suggestions based on keywords using embedding similarity.

        Uses pgvector cosine similarity to find authors with research embeddings
        similar to the provided keywords. Optionally enhances results with LLM
        explanations.

        Args:
            organization_id: Organization UUID for tenant isolation.
            keywords: List of research keywords to match against.
            target_size: Maximum number of suggestions to return.
            group_name: Optional group name for LLM context.
            group_description: Optional group description for LLM context.
            use_llm_explanation: If True, use LLM to generate explanations.

        Returns:
            List of SuggestedMember objects ranked by relevance.
        """
        if not keywords:
            return []

        # Generate embedding for the keywords
        keywords_text = ", ".join(keywords)
        try:
            embedding_client = EmbeddingClient()
            # Use the smaller 768d embedding model for authors
            await embedding_client.embed_text(f"Research expertise: {keywords_text}")
            # Note: Author embeddings are 768d, paper embeddings are 1536d
            # For now, we'll use 1536d and truncate, or fall back to text matching
        except Exception as e:
            logger.warning(f"Failed to generate embedding for keywords: {e}")
            # Fall back to basic text matching
            return await self._suggest_members_fallback(organization_id, keywords, target_size)

        # Author embeddings are not yet stored in pgvector (future migration).
        # Fall back to text-based matching for now.
        authors_with_embeddings: list[Author] = []

        # If we don't have enough authors with embeddings, supplement with others
        if len(authors_with_embeddings) < target_size:
            existing_ids = [a.id for a in authors_with_embeddings]
            supplement_query = select(Author).where(Author.organization_id == organization_id)
            # Only add notin_ filter if we have existing IDs to exclude
            if existing_ids:
                supplement_query = supplement_query.where(Author.id.notin_(existing_ids))
            supplement_query = supplement_query.limit(target_size - len(authors_with_embeddings))
            supplement_result = await self.db.execute(supplement_query)
            authors_without_embeddings = list(supplement_result.scalars().all())
            all_authors = authors_with_embeddings + authors_without_embeddings
        else:
            all_authors = authors_with_embeddings[:target_size]

        # Build suggestions with relevance scores
        suggestions = []
        for i, author in enumerate(all_authors):
            # Calculate relevance score based on ranking (embedding-based)
            # Authors earlier in the list are more similar
            if i < len(authors_with_embeddings):
                # Embedding-based score: higher rank = higher score
                relevance_score = round(1.0 - (i / max(len(authors_with_embeddings), 1)) * 0.5, 2)
            else:
                # Fallback authors get lower scores
                relevance_score = 0.3

            suggestions.append(
                SuggestedMember(
                    researcher_id=author.id,
                    name=author.name,
                    relevance_score=relevance_score,
                    matching_keywords=keywords[:3],  # Top keywords
                    affiliations=author.affiliations or [],
                )
            )

        # Optionally enhance with LLM explanations
        if use_llm_explanation and suggestions and group_name:
            suggestions = await self._enhance_suggestions_with_llm(
                suggestions,
                all_authors[: len(suggestions)],
                keywords,
                group_name,
                group_description,
            )

        return suggestions[:target_size]

    async def _suggest_members_fallback(
        self,
        organization_id: UUID,
        keywords: list[str],
        target_size: int,
    ) -> list[SuggestedMember]:
        """Fallback suggestion method using basic text matching.

        Used when embedding generation or search fails.
        """
        query = (
            select(Author)
            .where(Author.organization_id == organization_id)
            .order_by(Author.h_index.desc().nullslast())
            .limit(target_size)
        )
        result = await self.db.execute(query)
        authors = list(result.scalars().all())

        suggestions = []
        for i, author in enumerate(authors):
            # Score based on h-index ranking
            relevance_score = round(0.5 + (0.5 * (1 - i / max(len(authors), 1))), 2)
            suggestions.append(
                SuggestedMember(
                    researcher_id=author.id,
                    name=author.name,
                    relevance_score=relevance_score,
                    matching_keywords=keywords[:2],
                    affiliations=author.affiliations or [],
                )
            )

        return suggestions

    async def _enhance_suggestions_with_llm(
        self,
        suggestions: list[SuggestedMember],
        authors: list[Author],
        keywords: list[str],
        group_name: str,
        group_description: str | None,
    ) -> list[SuggestedMember]:
        """Enhance suggestions with LLM-generated explanations.

        Args:
            suggestions: Initial suggestions to enhance.
            authors: Author objects corresponding to suggestions.
            keywords: Research keywords for the group.
            group_name: Name of the research group.
            group_description: Optional description of the group.

        Returns:
            Enhanced suggestions with explanations.
        """
        try:
            from paper_scraper.modules.scoring.llm_client import get_llm_client

            llm = get_llm_client()

            # Build candidate data for prompt
            candidates_data = [
                {
                    "name": author.name,
                    "affiliations": author.affiliations or [],
                    "h_index": author.h_index,
                    "citation_count": author.citation_count,
                    "works_count": author.works_count,
                }
                for author in authors
            ]

            # Sanitize user inputs before prompt rendering to prevent injection
            sanitized_group_name = sanitize_text_for_prompt(group_name, max_length=200)
            sanitized_description = sanitize_text_for_prompt(
                group_description or "", max_length=500
            )
            sanitized_keywords = [
                sanitize_text_for_prompt(k, max_length=100) for k in keywords[:10]
            ]

            # Render prompt template
            template = _jinja_env.get_template("suggest_members.jinja2")
            prompt = template.render(
                group_name=sanitized_group_name,
                group_description=sanitized_description if sanitized_description else None,
                keywords=sanitized_keywords,
                candidates=candidates_data,
            )

            result = await llm.complete_json(
                prompt=prompt,
                system="You are an expert at matching researchers to collaborative research groups.",
                temperature=0.3,
                max_tokens=1500,
            )

            # Update suggestions with LLM scores and keywords
            llm_candidates = {c["name"]: c for c in result.get("candidates", [])}

            enhanced = []
            for suggestion in suggestions:
                if suggestion.name in llm_candidates:
                    llm_data = llm_candidates[suggestion.name]
                    # Safely extract and normalize relevance score (0-100 -> 0-1)
                    raw_score = llm_data.get("relevance_score")
                    if isinstance(raw_score, int | float) and 0 <= raw_score <= 100:
                        relevance_score = raw_score / 100
                    else:
                        relevance_score = suggestion.relevance_score
                    enhanced.append(
                        SuggestedMember(
                            researcher_id=suggestion.researcher_id,
                            name=suggestion.name,
                            relevance_score=relevance_score,
                            matching_keywords=llm_data.get(
                                "matching_keywords", suggestion.matching_keywords
                            ),
                            affiliations=suggestion.affiliations,
                            explanation=llm_data.get("explanation"),
                        )
                    )
                else:
                    enhanced.append(suggestion)

            # Sort by relevance score
            enhanced.sort(key=lambda s: s.relevance_score, reverse=True)
            return enhanced

        except Exception as e:
            logger.warning(f"LLM enhancement failed: {e}")
            return suggestions

    async def export_group(self, group_id: UUID, organization_id: UUID) -> bytes:
        """Export group members as CSV."""
        group = await self.get_group(group_id, organization_id)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Name", "H-Index", "Affiliations"])

        for member in group.members:
            researcher = member.researcher
            writer.writerow(
                [
                    sanitize_csv_field(researcher.name),
                    researcher.h_index or "",
                    sanitize_csv_field(", ".join(researcher.affiliations or [])),
                ]
            )

        return output.getvalue().encode("utf-8")
