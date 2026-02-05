"""Tests for researcher groups module."""

import pytest
import pytest_asyncio
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.modules.auth.models import Organization, User
from paper_scraper.modules.groups.models import GroupMember, GroupType, ResearcherGroup
from paper_scraper.modules.groups.service import GroupService
from paper_scraper.modules.groups.schemas import GroupCreate, GroupUpdate
from paper_scraper.modules.papers.models import Author


# =============================================================================
# Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def group_service(db_session: AsyncSession) -> GroupService:
    """Create a group service instance for testing."""
    return GroupService(db_session)


@pytest_asyncio.fixture
async def second_organization(db_session: AsyncSession) -> Organization:
    """Create a second organization for tenant isolation tests."""
    organization = Organization(
        name="Second Organization",
        type="university",
    )
    db_session.add(organization)
    await db_session.flush()
    await db_session.refresh(organization)
    return organization


@pytest_asyncio.fixture
async def test_author(
    db_session: AsyncSession,
    test_organization: Organization,
) -> Author:
    """Create a test author."""
    author = Author(
        name="Dr. Jane Smith",
        orcid="0000-0001-2345-6789",
        affiliations=["MIT", "Stanford"],
        h_index=25,
        citation_count=1500,
        works_count=45,
        organization_id=test_organization.id,
    )
    db_session.add(author)
    await db_session.flush()
    await db_session.refresh(author)
    return author


@pytest_asyncio.fixture
async def second_author(
    db_session: AsyncSession,
    test_organization: Organization,
) -> Author:
    """Create a second test author."""
    author = Author(
        name="Dr. John Doe",
        affiliations=["Harvard"],
        h_index=18,
        citation_count=800,
        works_count=30,
        organization_id=test_organization.id,
    )
    db_session.add(author)
    await db_session.flush()
    await db_session.refresh(author)
    return author


@pytest_asyncio.fixture
async def other_org_author(
    db_session: AsyncSession,
    second_organization: Organization,
) -> Author:
    """Create an author in a different organization."""
    author = Author(
        name="Dr. External Researcher",
        affiliations=["Oxford"],
        h_index=30,
        organization_id=second_organization.id,
    )
    db_session.add(author)
    await db_session.flush()
    await db_session.refresh(author)
    return author


@pytest_asyncio.fixture
async def test_group(
    db_session: AsyncSession,
    test_organization: Organization,
    test_user: User,
) -> ResearcherGroup:
    """Create a test group."""
    group = ResearcherGroup(
        name="AI Researchers",
        description="Researchers working on AI",
        type=GroupType.CUSTOM,
        keywords=["machine learning", "deep learning"],
        organization_id=test_organization.id,
        created_by=test_user.id,
    )
    db_session.add(group)
    await db_session.flush()
    await db_session.refresh(group)
    return group


@pytest_asyncio.fixture
async def group_with_member(
    db_session: AsyncSession,
    test_group: ResearcherGroup,
    test_author: Author,
    test_user: User,
) -> ResearcherGroup:
    """Create a group with a member."""
    member = GroupMember(
        group_id=test_group.id,
        researcher_id=test_author.id,
        added_by=test_user.id,
    )
    db_session.add(member)
    await db_session.flush()
    return test_group


# =============================================================================
# Service Tests
# =============================================================================


class TestGroupService:
    """Tests for GroupService class."""

    async def test_create_group(
        self,
        group_service: GroupService,
        test_organization: Organization,
        test_user: User,
    ):
        """Test creating a new group."""
        data = GroupCreate(
            name="Biotech Group",
            description="Researchers in biotech",
            type=GroupType.MAILING_LIST,
            keywords=["biotech", "genomics"],
        )

        group = await group_service.create_group(
            test_organization.id, test_user.id, data
        )

        assert group.id is not None
        assert group.name == "Biotech Group"
        assert group.type == GroupType.MAILING_LIST
        assert group.keywords == ["biotech", "genomics"]
        assert group.organization_id == test_organization.id
        assert group.created_by == test_user.id

    async def test_create_group_minimal(
        self,
        group_service: GroupService,
        test_organization: Organization,
        test_user: User,
    ):
        """Test creating a group with only required fields."""
        data = GroupCreate(name="Minimal Group")

        group = await group_service.create_group(
            test_organization.id, test_user.id, data
        )

        assert group.name == "Minimal Group"
        assert group.type == GroupType.CUSTOM
        assert group.keywords == []
        assert group.description is None

    async def test_get_group(
        self,
        group_service: GroupService,
        test_group: ResearcherGroup,
        test_organization: Organization,
    ):
        """Test retrieving a group by ID."""
        group = await group_service.get_group(
            test_group.id, test_organization.id
        )

        assert group.id == test_group.id
        assert group.name == "AI Researchers"

    async def test_get_group_not_found(
        self,
        group_service: GroupService,
        test_organization: Organization,
    ):
        """Test that getting a non-existent group raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await group_service.get_group(uuid4(), test_organization.id)

    async def test_get_group_tenant_isolation(
        self,
        group_service: GroupService,
        test_group: ResearcherGroup,
        second_organization: Organization,
    ):
        """Test that group retrieval respects organization boundaries."""
        with pytest.raises(NotFoundError):
            await group_service.get_group(
                test_group.id, second_organization.id
            )

    async def test_list_groups(
        self,
        group_service: GroupService,
        test_group: ResearcherGroup,
        test_organization: Organization,
    ):
        """Test listing groups with pagination."""
        response = await group_service.list_groups(
            test_organization.id, page=1, page_size=20
        )

        assert response.total == 1
        assert len(response.items) == 1
        assert response.items[0].name == "AI Researchers"

    async def test_list_groups_empty(
        self,
        group_service: GroupService,
        test_organization: Organization,
    ):
        """Test listing groups when none exist."""
        response = await group_service.list_groups(
            test_organization.id, page=1, page_size=20
        )

        assert response.total == 0
        assert len(response.items) == 0

    async def test_list_groups_tenant_isolation(
        self,
        group_service: GroupService,
        test_group: ResearcherGroup,
        second_organization: Organization,
    ):
        """Test that listing groups respects organization boundaries."""
        response = await group_service.list_groups(
            second_organization.id, page=1, page_size=20
        )

        assert response.total == 0
        assert len(response.items) == 0

    async def test_list_groups_filter_by_type(
        self,
        group_service: GroupService,
        test_group: ResearcherGroup,
        test_organization: Organization,
        test_user: User,
    ):
        """Test filtering groups by type."""
        await group_service.create_group(
            test_organization.id,
            test_user.id,
            GroupCreate(name="Newsletter", type=GroupType.MAILING_LIST),
        )

        response = await group_service.list_groups(
            test_organization.id,
            group_type=GroupType.MAILING_LIST,
        )

        assert response.total == 1
        assert response.items[0].name == "Newsletter"

    async def test_update_group(
        self,
        group_service: GroupService,
        test_group: ResearcherGroup,
        test_organization: Organization,
    ):
        """Test updating a group."""
        data = GroupUpdate(
            name="Updated AI Researchers",
            keywords=["AI", "NLP"],
        )

        group = await group_service.update_group(
            test_group.id, test_organization.id, data
        )

        assert group.name == "Updated AI Researchers"
        assert group.keywords == ["AI", "NLP"]
        assert group.description == "Researchers working on AI"

    async def test_update_group_not_found(
        self,
        group_service: GroupService,
        test_organization: Organization,
    ):
        """Test that updating a non-existent group raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await group_service.update_group(
                uuid4(), test_organization.id, GroupUpdate(name="X")
            )

    async def test_update_group_tenant_isolation(
        self,
        group_service: GroupService,
        test_group: ResearcherGroup,
        second_organization: Organization,
    ):
        """Test that update respects organization boundaries."""
        with pytest.raises(NotFoundError):
            await group_service.update_group(
                test_group.id,
                second_organization.id,
                GroupUpdate(name="Hacked"),
            )

    async def test_delete_group(
        self,
        group_service: GroupService,
        test_group: ResearcherGroup,
        test_organization: Organization,
        db_session: AsyncSession,
    ):
        """Test deleting a group."""
        await group_service.delete_group(
            test_group.id, test_organization.id
        )

        result = await db_session.execute(
            select(ResearcherGroup).where(
                ResearcherGroup.id == test_group.id
            )
        )
        assert result.scalar_one_or_none() is None

    async def test_delete_group_not_found(
        self,
        group_service: GroupService,
        test_organization: Organization,
    ):
        """Test that deleting a non-existent group raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await group_service.delete_group(uuid4(), test_organization.id)

    async def test_delete_group_tenant_isolation(
        self,
        group_service: GroupService,
        test_group: ResearcherGroup,
        second_organization: Organization,
    ):
        """Test that delete respects organization boundaries."""
        with pytest.raises(NotFoundError):
            await group_service.delete_group(
                test_group.id, second_organization.id
            )

    async def test_delete_group_cascades_members(
        self,
        group_service: GroupService,
        group_with_member: ResearcherGroup,
        test_organization: Organization,
        db_session: AsyncSession,
    ):
        """Test that deleting a group also removes its members."""
        group_id = group_with_member.id
        await group_service.delete_group(group_id, test_organization.id)

        result = await db_session.execute(
            select(GroupMember).where(GroupMember.group_id == group_id)
        )
        assert result.scalar_one_or_none() is None

    async def test_add_members(
        self,
        group_service: GroupService,
        test_group: ResearcherGroup,
        test_author: Author,
        test_organization: Organization,
        test_user: User,
    ):
        """Test adding members to a group."""
        added = await group_service.add_members(
            test_group.id,
            test_organization.id,
            [test_author.id],
            test_user.id,
        )

        assert added == 1

    async def test_add_members_duplicate(
        self,
        group_service: GroupService,
        group_with_member: ResearcherGroup,
        test_author: Author,
        test_organization: Organization,
        test_user: User,
    ):
        """Test that adding an existing member is skipped."""
        added = await group_service.add_members(
            group_with_member.id,
            test_organization.id,
            [test_author.id],
            test_user.id,
        )

        assert added == 0

    async def test_add_multiple_members(
        self,
        group_service: GroupService,
        test_group: ResearcherGroup,
        test_author: Author,
        second_author: Author,
        test_organization: Organization,
        test_user: User,
    ):
        """Test adding multiple members at once."""
        added = await group_service.add_members(
            test_group.id,
            test_organization.id,
            [test_author.id, second_author.id],
            test_user.id,
        )

        assert added == 2

    async def test_add_members_cross_tenant_rejected(
        self,
        group_service: GroupService,
        test_group: ResearcherGroup,
        other_org_author: Author,
        test_organization: Organization,
        test_user: User,
    ):
        """Test that researchers from other organizations cannot be added."""
        added = await group_service.add_members(
            test_group.id,
            test_organization.id,
            [other_org_author.id],
            test_user.id,
        )

        assert added == 0

    async def test_add_members_nonexistent_researcher(
        self,
        group_service: GroupService,
        test_group: ResearcherGroup,
        test_organization: Organization,
        test_user: User,
    ):
        """Test that adding a nonexistent researcher is silently skipped."""
        added = await group_service.add_members(
            test_group.id,
            test_organization.id,
            [uuid4()],
            test_user.id,
        )

        assert added == 0

    async def test_add_members_empty_list(
        self,
        group_service: GroupService,
        test_group: ResearcherGroup,
        test_organization: Organization,
        test_user: User,
    ):
        """Test adding an empty list of members."""
        added = await group_service.add_members(
            test_group.id,
            test_organization.id,
            [],
            test_user.id,
        )

        assert added == 0

    async def test_remove_member(
        self,
        group_service: GroupService,
        group_with_member: ResearcherGroup,
        test_author: Author,
        test_organization: Organization,
        db_session: AsyncSession,
    ):
        """Test removing a member from a group."""
        await group_service.remove_member(
            group_with_member.id, test_organization.id, test_author.id
        )

        result = await db_session.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_with_member.id,
                GroupMember.researcher_id == test_author.id,
            )
        )
        assert result.scalar_one_or_none() is None

    async def test_remove_member_group_not_found(
        self,
        group_service: GroupService,
        test_organization: Organization,
    ):
        """Test that removing from a nonexistent group raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await group_service.remove_member(
                uuid4(), test_organization.id, uuid4()
            )

    async def test_suggest_members(
        self,
        group_service: GroupService,
        test_author: Author,
        test_organization: Organization,
    ):
        """Test AI-powered member suggestions."""
        suggestions = await group_service.suggest_members(
            test_organization.id,
            keywords=["machine learning"],
            target_size=5,
        )

        assert len(suggestions) >= 1
        assert suggestions[0].name == "Dr. Jane Smith"

    async def test_suggest_members_empty_org(
        self,
        group_service: GroupService,
        second_organization: Organization,
    ):
        """Test suggestions when organization has no authors."""
        suggestions = await group_service.suggest_members(
            second_organization.id,
            keywords=["machine learning"],
        )

        assert len(suggestions) == 0

    async def test_export_group(
        self,
        group_service: GroupService,
        group_with_member: ResearcherGroup,
        test_organization: Organization,
    ):
        """Test exporting group members as CSV."""
        csv_data = await group_service.export_group(
            group_with_member.id, test_organization.id
        )

        csv_str = csv_data.decode("utf-8")
        assert "Name" in csv_str
        assert "H-Index" in csv_str
        assert "Affiliations" in csv_str
        assert "Dr. Jane Smith" in csv_str
        assert "MIT" in csv_str

    async def test_export_group_no_members(
        self,
        group_service: GroupService,
        test_group: ResearcherGroup,
        test_organization: Organization,
    ):
        """Test exporting a group with no members produces headers only."""
        csv_data = await group_service.export_group(
            test_group.id, test_organization.id
        )

        csv_str = csv_data.decode("utf-8")
        lines = csv_str.strip().split("\n")
        assert len(lines) == 1  # Only header row
        assert "Name" in lines[0]

    async def test_export_group_not_found(
        self,
        group_service: GroupService,
        test_organization: Organization,
    ):
        """Test that exporting a nonexistent group raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await group_service.export_group(uuid4(), test_organization.id)

    async def test_get_member_count(
        self,
        group_service: GroupService,
        group_with_member: ResearcherGroup,
    ):
        """Test getting member count."""
        count = await group_service.get_member_count(group_with_member.id)
        assert count == 1

    async def test_get_member_count_empty(
        self,
        group_service: GroupService,
        test_group: ResearcherGroup,
    ):
        """Test getting member count for group with no members."""
        count = await group_service.get_member_count(test_group.id)
        assert count == 0


# =============================================================================
# API Router Tests
# =============================================================================


class TestGroupsRouter:
    """Tests for groups API endpoints."""

    async def test_create_group(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test creating a group via API."""
        response = await authenticated_client.post(
            "/api/v1/groups/",
            json={
                "name": "AI Researchers",
                "description": "Researchers working on AI",
                "type": "custom",
                "keywords": ["machine learning", "deep learning"],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "AI Researchers"
        assert data["type"] == "custom"
        assert data["keywords"] == ["machine learning", "deep learning"]
        assert data["member_count"] == 0
        assert "id" in data
        assert "organization_id" in data
        assert "created_at" in data

    async def test_create_group_empty_name(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test that creating a group with empty name returns 422."""
        response = await authenticated_client.post(
            "/api/v1/groups/",
            json={"name": ""},
        )

        assert response.status_code == 422

    async def test_list_groups(
        self,
        authenticated_client: AsyncClient,
        test_group: ResearcherGroup,
    ):
        """Test listing groups via API."""
        response = await authenticated_client.get("/api/v1/groups/")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "AI Researchers"

    async def test_list_groups_filter_type(
        self,
        authenticated_client: AsyncClient,
        test_group: ResearcherGroup,
    ):
        """Test filtering groups by type via API."""
        response = await authenticated_client.get(
            "/api/v1/groups/", params={"type": "custom"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    async def test_get_group(
        self,
        authenticated_client: AsyncClient,
        test_group: ResearcherGroup,
    ):
        """Test getting a group detail via API."""
        response = await authenticated_client.get(
            f"/api/v1/groups/{test_group.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_group.id)
        assert data["name"] == "AI Researchers"
        assert "members" in data
        assert isinstance(data["members"], list)

    async def test_get_group_not_found(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test getting a non-existent group returns 404."""
        response = await authenticated_client.get(
            f"/api/v1/groups/{uuid4()}"
        )

        assert response.status_code == 404

    async def test_update_group(
        self,
        authenticated_client: AsyncClient,
        test_group: ResearcherGroup,
    ):
        """Test updating a group via API."""
        response = await authenticated_client.patch(
            f"/api/v1/groups/{test_group.id}",
            json={"name": "Updated Researchers"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Researchers"
        # Unchanged fields should remain
        assert data["description"] == "Researchers working on AI"
        assert data["type"] == "custom"

    async def test_update_group_not_found(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test updating a non-existent group returns 404."""
        response = await authenticated_client.patch(
            f"/api/v1/groups/{uuid4()}",
            json={"name": "X"},
        )

        assert response.status_code == 404

    async def test_update_group_empty_name(
        self,
        authenticated_client: AsyncClient,
        test_group: ResearcherGroup,
    ):
        """Test that updating with empty name returns 422."""
        response = await authenticated_client.patch(
            f"/api/v1/groups/{test_group.id}",
            json={"name": ""},
        )

        assert response.status_code == 422

    async def test_delete_group(
        self,
        authenticated_client: AsyncClient,
        test_group: ResearcherGroup,
    ):
        """Test deleting a group via API."""
        response = await authenticated_client.delete(
            f"/api/v1/groups/{test_group.id}"
        )

        assert response.status_code == 204

    async def test_delete_group_not_found(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test deleting a non-existent group returns 404."""
        response = await authenticated_client.delete(
            f"/api/v1/groups/{uuid4()}"
        )

        assert response.status_code == 404

    async def test_add_members(
        self,
        authenticated_client: AsyncClient,
        test_group: ResearcherGroup,
        test_author: Author,
    ):
        """Test adding members to a group via API."""
        response = await authenticated_client.post(
            f"/api/v1/groups/{test_group.id}/members",
            json={"researcher_ids": [str(test_author.id)]},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["added"] == 1

    async def test_add_members_group_not_found(
        self,
        authenticated_client: AsyncClient,
        test_author: Author,
    ):
        """Test adding members to a non-existent group returns 404."""
        response = await authenticated_client.post(
            f"/api/v1/groups/{uuid4()}/members",
            json={"researcher_ids": [str(test_author.id)]},
        )

        assert response.status_code == 404

    async def test_remove_member(
        self,
        authenticated_client: AsyncClient,
        group_with_member: ResearcherGroup,
        test_author: Author,
    ):
        """Test removing a member from a group via API."""
        response = await authenticated_client.delete(
            f"/api/v1/groups/{group_with_member.id}/members/{test_author.id}"
        )

        assert response.status_code == 204

    async def test_suggest_members(
        self,
        authenticated_client: AsyncClient,
        test_author: Author,
    ):
        """Test getting AI-suggested members via API."""
        response = await authenticated_client.post(
            "/api/v1/groups/suggest-members",
            json={"keywords": ["machine learning"], "target_size": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert "query_keywords" in data
        assert data["query_keywords"] == ["machine learning"]

    async def test_suggest_members_invalid_target_size(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test that target_size > 50 returns 422."""
        response = await authenticated_client.post(
            "/api/v1/groups/suggest-members",
            json={"keywords": ["AI"], "target_size": 100},
        )

        assert response.status_code == 422

    async def test_export_group(
        self,
        authenticated_client: AsyncClient,
        group_with_member: ResearcherGroup,
    ):
        """Test exporting group members as CSV via API."""
        response = await authenticated_client.get(
            f"/api/v1/groups/{group_with_member.id}/export"
        )

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "Dr. Jane Smith" in response.text
        assert "content-disposition" in response.headers

    async def test_export_group_not_found(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test exporting a non-existent group returns 404."""
        response = await authenticated_client.get(
            f"/api/v1/groups/{uuid4()}/export"
        )

        assert response.status_code == 404

    async def test_unauthorized_access(
        self,
        client: AsyncClient,
    ):
        """Test that unauthenticated requests are rejected."""
        response = await client.get("/api/v1/groups/")
        assert response.status_code == 401

    async def test_unauthorized_create(
        self,
        client: AsyncClient,
    ):
        """Test that unauthenticated create is rejected."""
        response = await client.post(
            "/api/v1/groups/",
            json={"name": "Test"},
        )
        assert response.status_code == 401
