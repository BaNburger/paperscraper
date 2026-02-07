"""Tests for projects module."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.auth.models import Organization, User
from paper_scraper.modules.papers.models import Paper, PaperSource
from paper_scraper.modules.projects.models import (
    PaperProjectStatus,
    Project,
    RejectionReason,
)


class TestProjectEndpoints:
    """Test project API endpoints."""

    @pytest.mark.asyncio
    async def test_create_project(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test creating a new project."""
        response = await client.post(
            "/api/v1/projects/",
            json={
                "name": "Test Project",
                "description": "A test project for screening papers",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["description"] == "A test project for screening papers"
        assert data["organization_id"] == str(test_user.organization_id)
        assert len(data["stages"]) == 7  # Default stages
        assert data["stages"][0]["name"] == "inbox"

    @pytest.mark.asyncio
    async def test_create_project_with_custom_stages(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test creating a project with custom stages."""
        response = await client.post(
            "/api/v1/projects/",
            json={
                "name": "Custom Pipeline",
                "stages": [
                    {"name": "new", "label": "New", "order": 0},
                    {"name": "review", "label": "Under Review", "order": 1},
                    {"name": "approved", "label": "Approved", "order": 2},
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["stages"]) == 3
        assert data["stages"][0]["name"] == "new"
        assert data["stages"][1]["label"] == "Under Review"

    @pytest.mark.asyncio
    async def test_list_projects_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test listing projects when none exist."""
        response = await client.get("/api/v1/projects/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_projects(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test listing projects."""
        # Create projects
        project1 = Project(
            organization_id=test_user.organization_id,
            name="Project Alpha",
        )
        project2 = Project(
            organization_id=test_user.organization_id,
            name="Project Beta",
        )
        db_session.add_all([project1, project2])
        await db_session.flush()

        response = await client.get("/api/v1/projects/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_get_project(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test getting a project by ID."""
        project = Project(
            organization_id=test_user.organization_id,
            name="My Project",
            description="Project description",
        )
        db_session.add(project)
        await db_session.flush()

        response = await client.get(
            f"/api/v1/projects/{project.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "My Project"
        assert data["description"] == "Project description"

    @pytest.mark.asyncio
    async def test_get_project_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test getting a non-existent project."""
        response = await client.get(
            f"/api/v1/projects/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_project(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test updating a project."""
        project = Project(
            organization_id=test_user.organization_id,
            name="Original Name",
        )
        db_session.add(project)
        await db_session.flush()

        response = await client.patch(
            f"/api/v1/projects/{project.id}",
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
    async def test_delete_project(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test deleting a project."""
        project = Project(
            organization_id=test_user.organization_id,
            name="To Delete",
        )
        db_session.add(project)
        await db_session.flush()
        project_id = project.id

        response = await client.delete(
            f"/api/v1/projects/{project_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify deleted
        response = await client.get(
            f"/api/v1/projects/{project_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestKanBanEndpoints:
    """Test KanBan board endpoints."""

    @pytest.mark.asyncio
    async def test_add_paper_to_project(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test adding a paper to a project."""
        # Create project and paper
        project = Project(
            organization_id=test_user.organization_id,
            name="Test Project",
        )
        paper = Paper(
            organization_id=test_user.organization_id,
            title="Test Paper",
            source=PaperSource.MANUAL,
        )
        db_session.add_all([project, paper])
        await db_session.flush()

        response = await client.post(
            f"/api/v1/projects/{project.id}/papers",
            json={
                "paper_id": str(paper.id),
                "stage": "screening",
                "priority": 2,
                "tags": ["important", "urgent"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["paper_id"] == str(paper.id)
        assert data["stage"] == "screening"
        assert data["priority"] == 2
        assert data["tags"] == ["important", "urgent"]

    @pytest.mark.asyncio
    async def test_add_paper_duplicate(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test adding the same paper twice fails."""
        project = Project(
            organization_id=test_user.organization_id,
            name="Test Project",
        )
        paper = Paper(
            organization_id=test_user.organization_id,
            title="Test Paper",
            source=PaperSource.MANUAL,
        )
        db_session.add_all([project, paper])
        await db_session.flush()

        # Add paper first time
        await client.post(
            f"/api/v1/projects/{project.id}/papers",
            json={"paper_id": str(paper.id)},
            headers=auth_headers,
        )

        # Try to add again
        response = await client.post(
            f"/api/v1/projects/{project.id}/papers",
            json={"paper_id": str(paper.id)},
            headers=auth_headers,
        )
        assert response.status_code == 409  # Conflict

    @pytest.mark.asyncio
    async def test_get_kanban_board(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test getting the KanBan board view."""
        project = Project(
            organization_id=test_user.organization_id,
            name="KanBan Test",
        )
        db_session.add(project)
        await db_session.flush()

        # Add papers to different stages
        papers = []
        for i, stage in enumerate(["inbox", "screening", "inbox"]):
            paper = Paper(
                organization_id=test_user.organization_id,
                title=f"Paper {i}",
                source=PaperSource.MANUAL,
            )
            db_session.add(paper)
            await db_session.flush()
            papers.append(paper)

            status = PaperProjectStatus(
                paper_id=paper.id,
                project_id=project.id,
                stage=stage,
                position=i,
            )
            db_session.add(status)
        await db_session.flush()

        response = await client.get(
            f"/api/v1/projects/{project.id}/kanban",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_papers"] == 3
        assert data["project"]["name"] == "KanBan Test"

        # Check stages
        inbox_stage = next(s for s in data["stages"] if s["name"] == "inbox")
        screening_stage = next(s for s in data["stages"] if s["name"] == "screening")
        assert inbox_stage["paper_count"] == 2
        assert screening_stage["paper_count"] == 1

    @pytest.mark.asyncio
    async def test_move_paper(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test moving a paper to a different stage."""
        project = Project(
            organization_id=test_user.organization_id,
            name="Move Test",
        )
        paper = Paper(
            organization_id=test_user.organization_id,
            title="Moving Paper",
            source=PaperSource.MANUAL,
        )
        db_session.add_all([project, paper])
        await db_session.flush()

        status = PaperProjectStatus(
            paper_id=paper.id,
            project_id=project.id,
            stage="inbox",
        )
        db_session.add(status)
        await db_session.flush()

        response = await client.patch(
            f"/api/v1/projects/{project.id}/papers/{paper.id}/move",
            json={
                "stage": "evaluation",
                "comment": "Looks promising",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["stage"] == "evaluation"

    @pytest.mark.asyncio
    async def test_reject_paper(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test rejecting a paper with a reason."""
        project = Project(
            organization_id=test_user.organization_id,
            name="Reject Test",
        )
        paper = Paper(
            organization_id=test_user.organization_id,
            title="Paper to Reject",
            source=PaperSource.MANUAL,
        )
        db_session.add_all([project, paper])
        await db_session.flush()

        status = PaperProjectStatus(
            paper_id=paper.id,
            project_id=project.id,
            stage="screening",
        )
        db_session.add(status)
        await db_session.flush()

        response = await client.post(
            f"/api/v1/projects/{project.id}/papers/{paper.id}/reject",
            json={
                "reason": "out_of_scope",
                "notes": "Does not fit our research focus",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["stage"] == "rejected"
        assert data["rejection_reason"] == "out_of_scope"
        assert data["rejection_notes"] == "Does not fit our research focus"

    @pytest.mark.asyncio
    async def test_batch_add_papers(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test batch adding papers to a project."""
        project = Project(
            organization_id=test_user.organization_id,
            name="Batch Test",
        )
        db_session.add(project)
        await db_session.flush()

        # Create papers
        paper_ids = []
        for i in range(3):
            paper = Paper(
                organization_id=test_user.organization_id,
                title=f"Batch Paper {i}",
                source=PaperSource.MANUAL,
            )
            db_session.add(paper)
            await db_session.flush()
            paper_ids.append(str(paper.id))

        response = await client.post(
            f"/api/v1/projects/{project.id}/papers/batch",
            json={
                "paper_ids": paper_ids,
                "stage": "screening",
                "tags": ["batch-import"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["added"] == 3
        assert data["skipped"] == 0

    @pytest.mark.asyncio
    async def test_get_paper_history(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test getting paper stage history."""
        project = Project(
            organization_id=test_user.organization_id,
            name="History Test",
        )
        paper = Paper(
            organization_id=test_user.organization_id,
            title="History Paper",
            source=PaperSource.MANUAL,
        )
        db_session.add_all([project, paper])
        await db_session.flush()

        # Add paper via API to create history
        await client.post(
            f"/api/v1/projects/{project.id}/papers",
            json={"paper_id": str(paper.id)},
            headers=auth_headers,
        )

        # Move paper to create more history
        await client.patch(
            f"/api/v1/projects/{project.id}/papers/{paper.id}/move",
            json={"stage": "screening", "comment": "Starting review"},
            headers=auth_headers,
        )

        response = await client.get(
            f"/api/v1/projects/{project.id}/papers/{paper.id}/history",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["history"]) == 2
        # Check that both stages are in history (order may vary due to timing)
        stages_in_history = {h["to_stage"] for h in data["history"]}
        assert "inbox" in stages_in_history
        assert "screening" in stages_in_history

    @pytest.mark.asyncio
    async def test_update_paper_status(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test updating paper status metadata."""
        project = Project(
            organization_id=test_user.organization_id,
            name="Update Test",
        )
        paper = Paper(
            organization_id=test_user.organization_id,
            title="Update Paper",
            source=PaperSource.MANUAL,
        )
        db_session.add_all([project, paper])
        await db_session.flush()

        status = PaperProjectStatus(
            paper_id=paper.id,
            project_id=project.id,
            stage="inbox",
        )
        db_session.add(status)
        await db_session.flush()

        response = await client.patch(
            f"/api/v1/projects/{project.id}/papers/{paper.id}/status",
            json={
                "priority": 1,
                "notes": "High priority paper",
                "tags": ["vip", "follow-up"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == 1
        assert data["notes"] == "High priority paper"
        assert data["tags"] == ["vip", "follow-up"]

    @pytest.mark.asyncio
    async def test_remove_paper_from_project(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test removing a paper from a project."""
        project = Project(
            organization_id=test_user.organization_id,
            name="Remove Test",
        )
        paper = Paper(
            organization_id=test_user.organization_id,
            title="Remove Paper",
            source=PaperSource.MANUAL,
        )
        db_session.add_all([project, paper])
        await db_session.flush()

        status = PaperProjectStatus(
            paper_id=paper.id,
            project_id=project.id,
            stage="inbox",
        )
        db_session.add(status)
        await db_session.flush()

        response = await client.delete(
            f"/api/v1/projects/{project.id}/papers/{paper.id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify removed from project
        response = await client.get(
            f"/api/v1/projects/{project.id}/papers/{paper.id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestProjectStatistics:
    """Test project statistics endpoint."""

    @pytest.mark.asyncio
    async def test_get_project_statistics(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test getting project statistics."""
        project = Project(
            organization_id=test_user.organization_id,
            name="Stats Test",
        )
        db_session.add(project)
        await db_session.flush()

        # Add papers to different stages
        stages = ["inbox", "inbox", "screening", "rejected"]
        for i, stage in enumerate(stages):
            paper = Paper(
                organization_id=test_user.organization_id,
                title=f"Stats Paper {i}",
                source=PaperSource.MANUAL,
            )
            db_session.add(paper)
            await db_session.flush()

            status = PaperProjectStatus(
                paper_id=paper.id,
                project_id=project.id,
                stage=stage,
                priority=i % 5 + 1,
                rejection_reason=RejectionReason.OUT_OF_SCOPE if stage == "rejected" else None,
            )
            db_session.add(status)
        await db_session.flush()

        response = await client.get(
            f"/api/v1/projects/{project.id}/statistics",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_papers"] == 4
        assert data["papers_by_stage"]["inbox"] == 2
        assert data["papers_by_stage"]["screening"] == 1
        assert data["papers_by_stage"]["rejected"] == 1
        assert data["rejection_reasons"]["out_of_scope"] == 1


class TestProjectTenantIsolation:
    """Test tenant isolation for projects."""

    @pytest.mark.asyncio
    async def test_cannot_see_other_org_projects(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that users cannot see projects from other organizations."""
        # Create a real organization for the other tenant
        other_org = Organization(name="Other Org", type="university")
        db_session.add(other_org)
        await db_session.flush()
        await db_session.refresh(other_org)

        # Create project for test user's org
        my_project = Project(
            organization_id=test_user.organization_id,
            name="My Project",
        )
        db_session.add(my_project)

        # Create project for different org
        other_project = Project(
            organization_id=other_org.id,
            name="Other Org Project",
        )
        db_session.add(other_project)
        await db_session.flush()

        response = await client.get("/api/v1/projects/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "My Project"

    @pytest.mark.asyncio
    async def test_cannot_access_other_org_project(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that users cannot access projects from other organizations by ID."""
        # Create a real organization for the other tenant
        other_org = Organization(name="Other Org", type="university")
        db_session.add(other_org)
        await db_session.flush()
        await db_session.refresh(other_org)

        other_project = Project(
            organization_id=other_org.id,
            name="Other Org Project",
        )
        db_session.add(other_project)
        await db_session.flush()

        response = await client.get(
            f"/api/v1/projects/{other_project.id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestProjectModel:
    """Test project model directly."""

    @pytest.mark.asyncio
    async def test_default_stages(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that projects have default stages."""
        project = Project(
            organization_id=test_user.organization_id,
            name="Default Stages Test",
        )
        db_session.add(project)
        await db_session.flush()

        assert len(project.stages) == 7
        stage_names = [s["name"] for s in project.stages]
        assert "inbox" in stage_names
        assert "screening" in stage_names
        assert "evaluation" in stage_names
        assert "rejected" in stage_names

    @pytest.mark.asyncio
    async def test_default_scoring_weights(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that projects have default scoring weights."""
        project = Project(
            organization_id=test_user.organization_id,
            name="Weights Test",
        )
        db_session.add(project)
        await db_session.flush()

        assert project.scoring_weights["novelty"] == 0.20
        assert project.scoring_weights["ip_potential"] == 0.20
        assert project.scoring_weights["marketability"] == 0.20
        assert project.scoring_weights["feasibility"] == 0.20
        assert project.scoring_weights["commercialization"] == 0.20
