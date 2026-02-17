"""Tests for research groups module (formerly projects/KanBan)."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.auth.models import Organization, User
from paper_scraper.modules.papers.models import Paper, PaperSource
from paper_scraper.modules.projects.models import (
    Project,
    ProjectPaper,
)


class TestResearchGroupEndpoints:
    """Test research group CRUD endpoints."""

    @pytest.mark.asyncio
    async def test_create_research_group(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test creating a new research group."""
        response = await client.post(
            "/api/v1/projects/",
            json={
                "name": "ML Lab @ MIT",
                "description": "Machine Learning Lab",
                "institution_name": "MIT",
                "openalex_institution_id": "I63966007",
                "max_papers": 50,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "ML Lab @ MIT"
        assert data["description"] == "Machine Learning Lab"
        assert data["institution_name"] == "MIT"
        assert data["organization_id"] == str(test_user.organization_id)
        assert data["paper_count"] == 0
        assert data["cluster_count"] == 0
        assert data["sync_status"] in ("idle", "importing")

    @pytest.mark.asyncio
    async def test_list_research_groups_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test listing research groups when none exist."""
        response = await client.get("/api/v1/projects/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_research_groups(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test listing research groups."""
        group1 = Project(
            organization_id=test_user.organization_id,
            name="Group Alpha",
            institution_name="MIT",
        )
        group2 = Project(
            organization_id=test_user.organization_id,
            name="Group Beta",
            pi_name="Prof. Smith",
        )
        db_session.add_all([group1, group2])
        await db_session.flush()

        response = await client.get("/api/v1/projects/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_get_research_group(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test getting a research group by ID."""
        group = Project(
            organization_id=test_user.organization_id,
            name="My Research Group",
            description="Studying AI safety",
            institution_name="Stanford",
            pi_name="Prof. Johnson",
        )
        db_session.add(group)
        await db_session.flush()

        response = await client.get(
            f"/api/v1/projects/{group.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "My Research Group"
        assert data["description"] == "Studying AI safety"
        assert data["institution_name"] == "Stanford"
        assert data["pi_name"] == "Prof. Johnson"

    @pytest.mark.asyncio
    async def test_get_research_group_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test getting a non-existent research group."""
        response = await client.get(
            f"/api/v1/projects/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_research_group(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test updating a research group."""
        group = Project(
            organization_id=test_user.organization_id,
            name="Original Name",
        )
        db_session.add(group)
        await db_session.flush()

        response = await client.patch(
            f"/api/v1/projects/{group.id}",
            json={
                "name": "Updated Name",
                "description": "New description",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "New description"

    @pytest.mark.asyncio
    async def test_delete_research_group(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test deleting a research group."""
        group = Project(
            organization_id=test_user.organization_id,
            name="To Delete",
        )
        db_session.add(group)
        await db_session.flush()
        group_id = group.id

        response = await client.delete(
            f"/api/v1/projects/{group_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify deleted
        response = await client.get(
            f"/api/v1/projects/{group_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestResearchGroupPapers:
    """Test research group paper listing."""

    @pytest.mark.asyncio
    async def test_list_papers_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test listing papers for a group with no papers."""
        group = Project(
            organization_id=test_user.organization_id,
            name="Empty Group",
        )
        db_session.add(group)
        await db_session.flush()

        response = await client.get(
            f"/api/v1/projects/{group.id}/papers",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data == []

    @pytest.mark.asyncio
    async def test_list_papers_with_papers(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test listing papers for a group that has papers."""
        group = Project(
            organization_id=test_user.organization_id,
            name="Group with Papers",
        )
        db_session.add(group)
        await db_session.flush()

        paper = Paper(
            organization_id=test_user.organization_id,
            title="Test Paper",
            source=PaperSource.MANUAL,
        )
        db_session.add(paper)
        await db_session.flush()

        pp = ProjectPaper(
            project_id=group.id,
            paper_id=paper.id,
        )
        db_session.add(pp)
        await db_session.flush()

        response = await client.get(
            f"/api/v1/projects/{group.id}/papers",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Paper"


class TestResearchGroupClusters:
    """Test cluster endpoints."""

    @pytest.mark.asyncio
    async def test_list_clusters_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test listing clusters for a group with no clusters."""
        group = Project(
            organization_id=test_user.organization_id,
            name="No Clusters Group",
        )
        db_session.add(group)
        await db_session.flush()

        response = await client.get(
            f"/api/v1/projects/{group.id}/clusters",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data == []


class TestResearchGroupTenantIsolation:
    """Test tenant isolation for research groups."""

    @pytest.mark.asyncio
    async def test_cannot_see_other_org_groups(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that users cannot see research groups from other organizations."""
        other_org = Organization(name="Other Org", type="university")
        db_session.add(other_org)
        await db_session.flush()
        await db_session.refresh(other_org)

        my_group = Project(
            organization_id=test_user.organization_id,
            name="My Group",
        )
        db_session.add(my_group)

        other_group = Project(
            organization_id=other_org.id,
            name="Other Org Group",
        )
        db_session.add(other_group)
        await db_session.flush()

        response = await client.get("/api/v1/projects/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "My Group"

    @pytest.mark.asyncio
    async def test_cannot_access_other_org_group(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that users cannot access research groups from other orgs by ID."""
        other_org = Organization(name="Other Org", type="university")
        db_session.add(other_org)
        await db_session.flush()
        await db_session.refresh(other_org)

        other_group = Project(
            organization_id=other_org.id,
            name="Other Org Group",
        )
        db_session.add(other_group)
        await db_session.flush()

        response = await client.get(
            f"/api/v1/projects/{other_group.id}",
            headers=auth_headers,
        )
        assert response.status_code == 404
