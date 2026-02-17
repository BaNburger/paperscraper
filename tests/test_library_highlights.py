"""Tests for Library V2 highlights API."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.config import settings
from paper_scraper.modules.auth.models import User
from paper_scraper.modules.papers.models import Paper, PaperSource


@pytest.fixture(autouse=True)
def _enable_library_flag():
    original = settings.LIBRARY_V2_ENABLED
    settings.LIBRARY_V2_ENABLED = True
    try:
        yield
    finally:
        settings.LIBRARY_V2_ENABLED = original


class TestLibraryHighlights:
    """Highlight generation and CRUD."""

    @pytest.mark.asyncio
    async def test_generate_and_version_highlights(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        db_session: AsyncSession,
        test_user: User,
    ):
        # Build enough text to create several chunks and satisfy min target count.
        full_text = " ".join([f"Key finding sentence {i}." for i in range(1, 1500)])
        paper = Paper(
            organization_id=test_user.organization_id,
            title="Highlight Generation Paper",
            source=PaperSource.MANUAL,
            full_text=full_text,
        )
        db_session.add(paper)
        await db_session.flush()

        hydrate = await client.post(
            f"/api/v1/library/papers/{paper.id}/hydrate-fulltext",
            headers=auth_headers,
        )
        assert hydrate.status_code == 200
        assert hydrate.json()["hydrated"] is True

        first_run = await client.post(
            f"/api/v1/library/papers/{paper.id}/highlights/generate",
            headers=auth_headers,
            json={"target_count": 6},
        )
        assert first_run.status_code == 200
        first_items = first_run.json()["items"]
        assert len(first_items) >= 5
        first_generation_id = first_items[0]["generation_id"]

        second_run = await client.post(
            f"/api/v1/library/papers/{paper.id}/highlights/generate",
            headers=auth_headers,
            json={"target_count": 6},
        )
        assert second_run.status_code == 200
        second_items = second_run.json()["items"]
        second_generation_id = second_items[0]["generation_id"]
        assert second_generation_id != first_generation_id

        active_list = await client.get(
            f"/api/v1/library/papers/{paper.id}/highlights",
            headers=auth_headers,
        )
        assert active_list.status_code == 200
        assert all(item["is_active"] is True for item in active_list.json()["items"])

        all_list = await client.get(
            f"/api/v1/library/papers/{paper.id}/highlights",
            headers=auth_headers,
            params={"include_inactive": True},
        )
        assert all_list.status_code == 200
        all_items = all_list.json()["items"]
        assert any(item["generation_id"] == first_generation_id and item["is_active"] is False for item in all_items)

    @pytest.mark.asyncio
    async def test_manual_highlight_crud(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        db_session: AsyncSession,
        test_user: User,
    ):
        paper = Paper(
            organization_id=test_user.organization_id,
            title="Manual Highlight Paper",
            source=PaperSource.MANUAL,
            full_text="A concise full text body for manual highlight tests.",
        )
        db_session.add(paper)
        await db_session.flush()

        create_response = await client.post(
            f"/api/v1/library/papers/{paper.id}/highlights",
            headers=auth_headers,
            json={
                "quote": "A concise full text body",
                "insight_summary": "Manual insight",
                "confidence": 0.9,
            },
        )
        assert create_response.status_code == 201
        created = create_response.json()
        assert created["source"] == "manual"

        update_response = await client.patch(
            f"/api/v1/library/papers/{paper.id}/highlights/{created['id']}",
            headers=auth_headers,
            json={"insight_summary": "Updated insight summary", "confidence": 0.7},
        )
        assert update_response.status_code == 200
        assert update_response.json()["insight_summary"] == "Updated insight summary"
        assert update_response.json()["confidence"] == 0.7

        delete_response = await client.delete(
            f"/api/v1/library/papers/{paper.id}/highlights/{created['id']}",
            headers=auth_headers,
        )
        assert delete_response.status_code == 204

        list_response = await client.get(
            f"/api/v1/library/papers/{paper.id}/highlights",
            headers=auth_headers,
            params={"include_inactive": True},
        )
        assert list_response.status_code == 200
        assert not any(item["id"] == created["id"] for item in list_response.json()["items"])
