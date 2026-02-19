"""Tests for Zotero integration sync endpoints."""

from __future__ import annotations

from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.config import settings
from paper_scraper.modules.auth.models import User
from paper_scraper.modules.integrations.connectors.zotero import ZoteroConnector
from paper_scraper.modules.integrations.models import ZoteroItemLink
from paper_scraper.modules.library.models import LibraryCollection, LibraryCollectionItem, PaperTag
from paper_scraper.modules.papers.models import Paper, PaperSource


@pytest.fixture(autouse=True)
def _enable_zotero_flags():
    original_sync = settings.ZOTERO_SYNC_ENABLED
    original_inbound = settings.LIBRARY_INBOUND_SYNC_ENABLED
    settings.ZOTERO_SYNC_ENABLED = True
    settings.LIBRARY_INBOUND_SYNC_ENABLED = True
    try:
        yield
    finally:
        settings.ZOTERO_SYNC_ENABLED = original_sync
        settings.LIBRARY_INBOUND_SYNC_ENABLED = original_inbound


class TestZoteroSync:
    """Outbound and inbound Zotero synchronization behavior."""

    @pytest.mark.asyncio
    async def test_connect_and_outbound_sync_idempotent(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        db_session: AsyncSession,
        test_user: User,
        monkeypatch: pytest.MonkeyPatch,
    ):
        async def _verify_ok(self, creds):
            return None

        async def _upsert(self, creds, item_payload, zotero_item_key=None):
            if zotero_item_key:
                return {"item_key": zotero_item_key}
            return {"item_key": "ITEM-123"}

        monkeypatch.setattr(ZoteroConnector, "verify_connection", _verify_ok)
        monkeypatch.setattr(ZoteroConnector, "upsert_item", _upsert)

        paper = Paper(
            organization_id=test_user.organization_id,
            title="Outbound Sync Paper",
            source=PaperSource.MANUAL,
            publication_date=datetime(2024, 1, 1),
        )
        db_session.add(paper)
        await db_session.flush()

        connect = await client.post(
            "/api/v1/integrations/zotero/connect",
            headers=auth_headers,
            json={
                "user_id": "zotero-user",
                "api_key": "test-api-key",
                "library_type": "users",
            },
        )
        assert connect.status_code == 200
        assert connect.json()["connected"] is True

        first_sync = await client.post(
            "/api/v1/integrations/zotero/sync/outbound",
            headers=auth_headers,
            json={"paper_ids": [str(paper.id)]},
        )
        assert first_sync.status_code == 200
        assert first_sync.json()["status"] in {"succeeded", "running"}

        second_sync = await client.post(
            "/api/v1/integrations/zotero/sync/outbound",
            headers=auth_headers,
            json={"paper_ids": [str(paper.id)]},
        )
        assert second_sync.status_code == 200

        links_result = await db_session.execute(
            select(ZoteroItemLink).where(
                ZoteroItemLink.organization_id == test_user.organization_id,
                ZoteroItemLink.paper_id == paper.id,
            )
        )
        links = list(links_result.scalars().all())
        assert len(links) == 1
        assert links[0].zotero_item_key == "ITEM-123"
        assert links[0].is_active is True

    @pytest.mark.xfail(reason="Zotero inbound sync does not merge DOI field yet")
    @pytest.mark.asyncio
    async def test_inbound_sync_non_destructive_merge_and_soft_deactivate(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        db_session: AsyncSession,
        test_user: User,
        monkeypatch: pytest.MonkeyPatch,
    ):
        async def _verify_ok(self, creds):
            return None

        list_items_payload: list[dict] = [
            {
                "key": "INBOUND-ITEM-1",
                "data": {
                    "itemType": "journalArticle",
                    "title": "Inbound Merge Paper",
                    "DOI": "10.1234/inbound.merge",
                    "abstractNote": "Remote abstract should not overwrite local value",
                    "publicationTitle": "Zotero Journal",
                    "date": "2024-03-12",
                    "tags": [{"tag": "priority"}, {"tag": "automation"}],
                    "collections": ["COLL-A"],
                },
            }
        ]

        async def _list_items(self, creds, since=None, limit=100):
            return list_items_payload

        monkeypatch.setattr(ZoteroConnector, "verify_connection", _verify_ok)
        monkeypatch.setattr(ZoteroConnector, "list_items", _list_items)

        local_paper = Paper(
            organization_id=test_user.organization_id,
            title="Inbound Merge Paper",
            source=PaperSource.MANUAL,
            abstract="Local abstract should stay",
        )
        db_session.add(local_paper)
        await db_session.flush()

        connect = await client.post(
            "/api/v1/integrations/zotero/connect",
            headers=auth_headers,
            json={
                "user_id": "zotero-user",
                "api_key": "test-api-key",
                "library_type": "users",
            },
        )
        assert connect.status_code == 200

        inbound = await client.post(
            "/api/v1/integrations/zotero/sync/inbound",
            headers=auth_headers,
        )
        assert inbound.status_code == 200
        assert inbound.json()["status"] in {"succeeded", "running"}

        await db_session.refresh(local_paper)
        assert local_paper.abstract == "Local abstract should stay"
        assert local_paper.doi == "10.1234/inbound.merge"
        assert local_paper.journal == "Zotero Journal"

        tag_result = await db_session.execute(
            select(PaperTag).where(
                PaperTag.organization_id == test_user.organization_id,
                PaperTag.paper_id == local_paper.id,
                PaperTag.tag == "priority",
            )
        )
        assert tag_result.scalar_one_or_none() is not None

        collection_result = await db_session.execute(
            select(LibraryCollection).where(
                LibraryCollection.organization_id == test_user.organization_id,
                LibraryCollection.name == "Zotero COLL-A",
            )
        )
        collection = collection_result.scalar_one_or_none()
        assert collection is not None

        membership_result = await db_session.execute(
            select(LibraryCollectionItem).where(
                LibraryCollectionItem.organization_id == test_user.organization_id,
                LibraryCollectionItem.collection_id == collection.id,
                LibraryCollectionItem.paper_id == local_paper.id,
            )
        )
        assert membership_result.scalar_one_or_none() is not None

        link_result = await db_session.execute(
            select(ZoteroItemLink).where(
                ZoteroItemLink.organization_id == test_user.organization_id,
                ZoteroItemLink.paper_id == local_paper.id,
                ZoteroItemLink.zotero_item_key == "INBOUND-ITEM-1",
            )
        )
        link = link_result.scalar_one_or_none()
        assert link is not None
        assert link.is_active is True

        # Simulate deletion on Zotero side: no items returned.
        list_items_payload.clear()
        inbound_after_delete = await client.post(
            "/api/v1/integrations/zotero/sync/inbound",
            headers=auth_headers,
        )
        assert inbound_after_delete.status_code == 200

        await db_session.refresh(link)
        assert link.is_active is False

    @pytest.mark.asyncio
    async def test_zotero_routes_require_authentication(self, client: AsyncClient):
        """Ensure Zotero integration routes are protected."""
        status = await client.get("/api/v1/integrations/zotero/status")
        assert status.status_code == 401

        outbound = await client.post("/api/v1/integrations/zotero/sync/outbound", json={})
        assert outbound.status_code == 401
