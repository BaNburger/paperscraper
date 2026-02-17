"""Tests for Library V2 collections, tags, and reader APIs."""

from __future__ import annotations

from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.config import settings
from paper_scraper.modules.auth.models import Organization, User
from paper_scraper.modules.papers.models import Paper, PaperSource


@pytest.fixture(autouse=True)
def _enable_library_flag():
    original = settings.LIBRARY_V2_ENABLED
    settings.LIBRARY_V2_ENABLED = True
    try:
        yield
    finally:
        settings.LIBRARY_V2_ENABLED = original


class TestLibraryCollections:
    """Collection and membership behavior."""

    @pytest.mark.asyncio
    async def test_collection_crud_and_membership(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        db_session: AsyncSession,
        test_user: User,
    ):
        paper = Paper(
            organization_id=test_user.organization_id,
            title="Collection Target Paper",
            source=PaperSource.MANUAL,
        )
        db_session.add(paper)
        await db_session.flush()

        create_root = await client.post(
            "/api/v1/library/collections",
            headers=auth_headers,
            json={"name": "Root Collection", "description": "Top level"},
        )
        assert create_root.status_code == 201
        root = create_root.json()

        create_child = await client.post(
            "/api/v1/library/collections",
            headers=auth_headers,
            json={"name": "Child Collection", "parent_id": root["id"]},
        )
        assert create_child.status_code == 201
        child = create_child.json()
        assert child["parent_id"] == root["id"]

        list_response = await client.get("/api/v1/library/collections", headers=auth_headers)
        assert list_response.status_code == 200
        data = list_response.json()
        assert data["total"] == 2

        update_response = await client.patch(
            f"/api/v1/library/collections/{child['id']}",
            headers=auth_headers,
            json={"name": "Child Collection Updated"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Child Collection Updated"

        add_paper_response = await client.post(
            f"/api/v1/library/collections/{child['id']}/papers/{paper.id}",
            headers=auth_headers,
        )
        assert add_paper_response.status_code == 200
        assert add_paper_response.json()["added"] is True

        remove_paper_response = await client.delete(
            f"/api/v1/library/collections/{child['id']}/papers/{paper.id}",
            headers=auth_headers,
        )
        assert remove_paper_response.status_code == 200
        assert remove_paper_response.json()["added"] is False

        delete_response = await client.delete(
            f"/api/v1/library/collections/{child['id']}",
            headers=auth_headers,
        )
        assert delete_response.status_code == 204

    @pytest.mark.asyncio
    async def test_collection_cycle_prevention(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        create_root = await client.post(
            "/api/v1/library/collections",
            headers=auth_headers,
            json={"name": "Root"},
        )
        root_id = create_root.json()["id"]

        create_child = await client.post(
            "/api/v1/library/collections",
            headers=auth_headers,
            json={"name": "Child", "parent_id": root_id},
        )
        child_id = create_child.json()["id"]

        response = await client.patch(
            f"/api/v1/library/collections/{root_id}",
            headers=auth_headers,
            json={"parent_id": child_id},
        )
        assert response.status_code in {400, 422}


class TestLibraryReaderAndTags:
    """Reader hydration and tagging."""

    @pytest.mark.asyncio
    async def test_reader_hydrate_and_fetch(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        db_session: AsyncSession,
        test_user: User,
    ):
        full_text = " ".join([f"Sentence {i}." for i in range(1, 800)])
        paper = Paper(
            organization_id=test_user.organization_id,
            title="Reader Paper",
            source=PaperSource.MANUAL,
            full_text=full_text,
            publication_date=datetime(2025, 1, 1),
        )
        db_session.add(paper)
        await db_session.flush()

        hydrate = await client.post(
            f"/api/v1/library/papers/{paper.id}/hydrate-fulltext",
            headers=auth_headers,
        )
        assert hydrate.status_code == 200
        hydrate_data = hydrate.json()
        assert hydrate_data["hydrated"] is True
        assert hydrate_data["chunks_created"] > 0

        reader = await client.get(
            f"/api/v1/library/papers/{paper.id}/reader",
            headers=auth_headers,
        )
        assert reader.status_code == 200
        reader_data = reader.json()
        assert reader_data["status"]["available"] is True
        assert reader_data["status"]["chunk_count"] > 0
        assert len(reader_data["chunks"]) == reader_data["status"]["chunk_count"]

    @pytest.mark.asyncio
    async def test_tags_crud_and_tenant_isolation(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        db_session: AsyncSession,
        test_user: User,
    ):
        paper = Paper(
            organization_id=test_user.organization_id,
            title="Taggable Paper",
            source=PaperSource.MANUAL,
        )
        db_session.add(paper)

        other_org = Organization(name="Other Org", type="university")
        db_session.add(other_org)
        await db_session.flush()

        other_paper = Paper(
            organization_id=other_org.id,
            title="Other Paper",
            source=PaperSource.MANUAL,
        )
        db_session.add(other_paper)
        await db_session.flush()

        add_tag = await client.post(
            f"/api/v1/library/papers/{paper.id}/tags",
            headers=auth_headers,
            json={"tag": "Priority"},
        )
        assert add_tag.status_code == 201
        assert add_tag.json()["tag"] == "priority"

        tag_list = await client.get("/api/v1/library/tags", headers=auth_headers)
        assert tag_list.status_code == 200
        tags = tag_list.json()["items"]
        tag_names = {item["tag"] for item in tags}
        assert "priority" in tag_names

        # Ensure current user cannot tag another tenant's paper.
        forbidden = await client.post(
            f"/api/v1/library/papers/{other_paper.id}/tags",
            headers=auth_headers,
            json={"tag": "external"},
        )
        assert forbidden.status_code == 404

        remove = await client.delete(
            f"/api/v1/library/papers/{paper.id}/tags/priority",
            headers=auth_headers,
        )
        assert remove.status_code == 200
        assert remove.json()["removed"] is True

    @pytest.mark.asyncio
    async def test_library_routes_require_authentication(self, client: AsyncClient):
        """Ensure new library routes enforce authentication."""
        response = await client.get('/api/v1/library/collections')
        assert response.status_code == 401

        response = await client.get('/api/v1/library/tags')
        assert response.status_code == 401
