"""Unit tests for paper_scraper.core.sync — SyncService dual-write orchestration.

All tests mock VectorService and SearchEngineService to verify that
the SyncService correctly delegates writes and handles errors gracefully.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from paper_scraper.core.sync import SyncService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dummy_vector(dim: int = 1536) -> list[float]:
    """Return a zero-filled embedding of the given dimension."""
    return [0.0] * dim


def _make_services() -> tuple[AsyncMock, MagicMock, SyncService]:
    """Create a SyncService with mocked dependencies.

    Returns:
        (mock_vector, mock_search, sync_service) tuple
    """
    mock_vector = AsyncMock()
    mock_search = MagicMock()
    sync = SyncService(vector_service=mock_vector, search_service=mock_search)
    return mock_vector, mock_search, sync


# ---------------------------------------------------------------------------
# Paper Sync
# ---------------------------------------------------------------------------


class TestSyncPaper:
    """Tests for SyncService.sync_paper."""

    async def test_sync_paper_writes_to_qdrant_and_typesense(self) -> None:
        """When embedding is provided, both Qdrant and Typesense should be written."""
        mock_vector, mock_search, sync = _make_services()

        paper_id = uuid4()
        org_id = uuid4()
        embedding = _dummy_vector()

        await sync.sync_paper(
            paper_id=paper_id,
            organization_id=org_id,
            title="Test Paper",
            abstract="Abstract text",
            embedding=embedding,
        )

        # Qdrant: upsert called with papers collection
        mock_vector.upsert.assert_awaited_once()
        upsert_kwargs = mock_vector.upsert.await_args.kwargs
        assert upsert_kwargs["collection"] == "papers"
        assert upsert_kwargs["point_id"] == paper_id
        assert upsert_kwargs["vector"] == embedding
        assert upsert_kwargs["payload"]["organization_id"] == str(org_id)

        # Typesense: index_paper called
        mock_search.index_paper.assert_called_once()
        doc = mock_search.index_paper.call_args[0][0]
        assert doc["paper_id"] == str(paper_id)
        assert doc["organization_id"] == str(org_id)
        assert doc["title"] == "Test Paper"
        assert doc["has_embedding"] is True

    async def test_sync_paper_skips_qdrant_without_embedding(self) -> None:
        """When no embedding is provided, only Typesense should be written."""
        mock_vector, mock_search, sync = _make_services()

        paper_id = uuid4()
        org_id = uuid4()

        await sync.sync_paper(
            paper_id=paper_id,
            organization_id=org_id,
            title="No Embedding Paper",
            embedding=None,
        )

        # Qdrant: NOT called
        mock_vector.upsert.assert_not_awaited()

        # Typesense: still called
        mock_search.index_paper.assert_called_once()
        doc = mock_search.index_paper.call_args[0][0]
        # has_embedding=False is falsy, so paper_to_document omits it from the doc
        assert "has_embedding" not in doc

    async def test_sync_paper_qdrant_failure_doesnt_block(self) -> None:
        """If Qdrant upsert fails, the exception should be caught and logged.

        Typesense indexing should still proceed.
        """
        mock_vector, mock_search, sync = _make_services()
        mock_vector.upsert.side_effect = Exception("Qdrant connection refused")

        paper_id = uuid4()
        org_id = uuid4()

        # Should NOT raise
        await sync.sync_paper(
            paper_id=paper_id,
            organization_id=org_id,
            title="Failing Paper",
            embedding=_dummy_vector(),
        )

        # Qdrant was attempted
        mock_vector.upsert.assert_awaited_once()
        # Typesense still called despite Qdrant failure
        mock_search.index_paper.assert_called_once()

    async def test_sync_paper_typesense_failure_doesnt_raise(self) -> None:
        """If Typesense indexing fails, the exception should be caught and logged."""
        mock_vector, mock_search, sync = _make_services()
        mock_search.index_paper.side_effect = Exception("Typesense down")

        # Should NOT raise
        await sync.sync_paper(
            paper_id=uuid4(),
            organization_id=uuid4(),
            title="TS Failure",
            embedding=None,
        )

    async def test_sync_paper_passes_metadata_to_qdrant_payload(self) -> None:
        """Qdrant payload should include doi, source, and created_at when provided."""
        mock_vector, mock_search, sync = _make_services()

        created = datetime(2024, 7, 1, 12, 0, 0)
        await sync.sync_paper(
            paper_id=uuid4(),
            organization_id=uuid4(),
            title="With Metadata",
            doi="10.1234/test",
            source="pubmed",
            created_at=created,
            embedding=_dummy_vector(),
        )

        payload = mock_vector.upsert.await_args.kwargs["payload"]
        assert payload["doi"] == "10.1234/test"
        assert payload["source"] == "pubmed"
        assert payload["created_at"] == int(created.timestamp())


# ---------------------------------------------------------------------------
# Author Sync
# ---------------------------------------------------------------------------


class TestSyncAuthor:
    """Tests for SyncService.sync_author."""

    async def test_sync_author(self) -> None:
        """sync_author should upsert to the authors collection in Qdrant."""
        mock_vector, _mock_search, sync = _make_services()

        author_id = uuid4()
        org_id = uuid4()
        embedding = _dummy_vector(768)

        await sync.sync_author(
            author_id=author_id,
            organization_id=org_id,
            embedding=embedding,
            name="Dr. Test Author",
            orcid="0000-0001-2345-6789",
        )

        mock_vector.upsert.assert_awaited_once()
        kwargs = mock_vector.upsert.await_args.kwargs
        assert kwargs["collection"] == "authors"
        assert kwargs["point_id"] == author_id
        assert kwargs["vector"] == embedding
        assert kwargs["payload"]["name"] == "Dr. Test Author"
        assert kwargs["payload"]["orcid"] == "0000-0001-2345-6789"
        assert kwargs["payload"]["organization_id"] == str(org_id)

    async def test_sync_author_failure_doesnt_raise(self) -> None:
        """Author sync failure should be caught and logged."""
        mock_vector, _mock_search, sync = _make_services()
        mock_vector.upsert.side_effect = Exception("network error")

        # Should NOT raise
        await sync.sync_author(
            author_id=uuid4(),
            organization_id=uuid4(),
            embedding=_dummy_vector(768),
        )

    async def test_sync_author_optional_fields(self) -> None:
        """When name and orcid are not provided, payload should omit them."""
        mock_vector, _mock_search, sync = _make_services()

        await sync.sync_author(
            author_id=uuid4(),
            organization_id=uuid4(),
            embedding=_dummy_vector(768),
        )

        payload = mock_vector.upsert.await_args.kwargs["payload"]
        assert "name" not in payload
        assert "orcid" not in payload


# ---------------------------------------------------------------------------
# Cluster Sync
# ---------------------------------------------------------------------------


class TestSyncCluster:
    """Tests for SyncService.sync_cluster."""

    async def test_sync_cluster(self) -> None:
        """sync_cluster should upsert to the clusters collection."""
        mock_vector, _mock_search, sync = _make_services()

        cluster_id = uuid4()
        org_id = uuid4()
        project_id = uuid4()
        centroid = _dummy_vector()

        await sync.sync_cluster(
            cluster_id=cluster_id,
            organization_id=org_id,
            project_id=project_id,
            centroid=centroid,
        )

        mock_vector.upsert.assert_awaited_once()
        kwargs = mock_vector.upsert.await_args.kwargs
        assert kwargs["collection"] == "clusters"
        assert kwargs["point_id"] == cluster_id
        assert kwargs["vector"] == centroid
        assert kwargs["payload"]["organization_id"] == str(org_id)
        assert kwargs["payload"]["project_id"] == str(project_id)
        assert kwargs["payload"]["cluster_id"] == str(cluster_id)

    async def test_sync_cluster_failure_doesnt_raise(self) -> None:
        """Cluster sync failure should be caught and logged."""
        mock_vector, _mock_search, sync = _make_services()
        mock_vector.upsert.side_effect = Exception("timeout")

        await sync.sync_cluster(
            cluster_id=uuid4(),
            organization_id=uuid4(),
            project_id=uuid4(),
            centroid=_dummy_vector(),
        )


# ---------------------------------------------------------------------------
# Trend Sync
# ---------------------------------------------------------------------------


class TestSyncTrend:
    """Tests for SyncService.sync_trend."""

    async def test_sync_trend(self) -> None:
        """sync_trend should upsert to the trends collection."""
        mock_vector, _mock_search, sync = _make_services()

        trend_id = uuid4()
        org_id = uuid4()
        embedding = _dummy_vector()

        await sync.sync_trend(
            trend_id=trend_id,
            organization_id=org_id,
            embedding=embedding,
            name="AI in Healthcare",
        )

        mock_vector.upsert.assert_awaited_once()
        kwargs = mock_vector.upsert.await_args.kwargs
        assert kwargs["collection"] == "trends"
        assert kwargs["point_id"] == trend_id
        assert kwargs["vector"] == embedding
        assert kwargs["payload"]["organization_id"] == str(org_id)
        assert kwargs["payload"]["trend_id"] == str(trend_id)
        assert kwargs["payload"]["name"] == "AI in Healthcare"

    async def test_sync_trend_without_name(self) -> None:
        """Trend payload should omit name when not provided."""
        mock_vector, _mock_search, sync = _make_services()

        await sync.sync_trend(
            trend_id=uuid4(),
            organization_id=uuid4(),
            embedding=_dummy_vector(),
        )

        payload = mock_vector.upsert.await_args.kwargs["payload"]
        assert "name" not in payload

    async def test_sync_trend_failure_doesnt_raise(self) -> None:
        """Trend sync failure should be caught and logged."""
        mock_vector, _mock_search, sync = _make_services()
        mock_vector.upsert.side_effect = Exception("error")

        await sync.sync_trend(
            trend_id=uuid4(),
            organization_id=uuid4(),
            embedding=_dummy_vector(),
        )


# ---------------------------------------------------------------------------
# Saved Search Sync
# ---------------------------------------------------------------------------


class TestSyncSavedSearch:
    """Tests for SyncService.sync_saved_search."""

    async def test_sync_saved_search(self) -> None:
        """sync_saved_search should upsert to the searches collection."""
        mock_vector, _mock_search, sync = _make_services()

        search_id = uuid4()
        org_id = uuid4()
        embedding = _dummy_vector()

        await sync.sync_saved_search(
            search_id=search_id,
            organization_id=org_id,
            embedding=embedding,
        )

        mock_vector.upsert.assert_awaited_once()
        kwargs = mock_vector.upsert.await_args.kwargs
        assert kwargs["collection"] == "searches"
        assert kwargs["point_id"] == search_id
        assert kwargs["vector"] == embedding
        assert kwargs["payload"]["organization_id"] == str(org_id)
        assert kwargs["payload"]["search_id"] == str(search_id)

    async def test_sync_saved_search_failure_doesnt_raise(self) -> None:
        """Saved search sync failure should be caught and logged."""
        mock_vector, _mock_search, sync = _make_services()
        mock_vector.upsert.side_effect = Exception("connection refused")

        await sync.sync_saved_search(
            search_id=uuid4(),
            organization_id=uuid4(),
            embedding=_dummy_vector(),
        )


# ---------------------------------------------------------------------------
# Delete Operations
# ---------------------------------------------------------------------------


class TestDeletePaper:
    """Tests for SyncService.delete_paper."""

    async def test_delete_paper_from_both(self) -> None:
        """delete_paper should remove from both Qdrant and Typesense."""
        mock_vector, mock_search, sync = _make_services()
        paper_id = uuid4()

        await sync.delete_paper(paper_id)

        # Qdrant delete
        mock_vector.delete.assert_awaited_once_with("papers", paper_id)
        # Typesense delete
        mock_search.delete_paper.assert_called_once_with(str(paper_id))

    async def test_delete_paper_qdrant_failure_still_deletes_typesense(self) -> None:
        """If Qdrant delete fails, Typesense delete should still proceed."""
        mock_vector, mock_search, sync = _make_services()
        mock_vector.delete.side_effect = Exception("Qdrant error")

        paper_id = uuid4()
        await sync.delete_paper(paper_id)

        mock_search.delete_paper.assert_called_once_with(str(paper_id))

    async def test_delete_paper_typesense_failure_doesnt_raise(self) -> None:
        """If Typesense delete fails, the error should be caught."""
        mock_vector, mock_search, sync = _make_services()
        mock_search.delete_paper.side_effect = Exception("Typesense error")

        # Should NOT raise
        await sync.delete_paper(uuid4())


class TestDeleteAuthor:
    """Tests for SyncService.delete_author."""

    async def test_delete_author(self) -> None:
        """delete_author should remove from Qdrant authors collection."""
        mock_vector, _mock_search, sync = _make_services()
        author_id = uuid4()

        await sync.delete_author(author_id)

        mock_vector.delete.assert_awaited_once_with("authors", author_id)

    async def test_delete_author_failure_doesnt_raise(self) -> None:
        """Author delete failure should be caught."""
        mock_vector, _mock_search, sync = _make_services()
        mock_vector.delete.side_effect = Exception("error")

        await sync.delete_author(uuid4())


class TestDeleteOrgData:
    """Tests for SyncService.delete_org_data."""

    async def test_delete_org_data(self) -> None:
        """delete_org_data should clean up all 5 Qdrant collections + Typesense."""
        mock_vector, mock_search, sync = _make_services()
        org_id = uuid4()

        await sync.delete_org_data(org_id)

        # Qdrant: delete_by_org for all 5 collections
        assert mock_vector.delete_by_org.await_count == 5
        deleted_collections = [call.args[0] for call in mock_vector.delete_by_org.await_args_list]
        assert "papers" in deleted_collections
        assert "authors" in deleted_collections
        assert "clusters" in deleted_collections
        assert "searches" in deleted_collections
        assert "trends" in deleted_collections

        for call in mock_vector.delete_by_org.await_args_list:
            assert call.args[1] == org_id

        # Typesense: delete_papers_by_org
        mock_search.delete_papers_by_org.assert_called_once_with(org_id)

    async def test_delete_org_data_partial_failure(self) -> None:
        """If some collections fail to delete, the rest should still be attempted."""
        mock_vector, mock_search, sync = _make_services()

        call_count = 0

        async def _fail_on_second(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("failed on second collection")

        mock_vector.delete_by_org.side_effect = _fail_on_second

        org_id = uuid4()
        # Should NOT raise
        await sync.delete_org_data(org_id)

        # All 5 collections should still be attempted
        assert mock_vector.delete_by_org.await_count == 5
        # Typesense should still be called
        mock_search.delete_papers_by_org.assert_called_once()


# ---------------------------------------------------------------------------
# Bulk Sync
# ---------------------------------------------------------------------------


class TestBulkSyncPapers:
    """Tests for SyncService.bulk_sync_papers."""

    async def test_bulk_sync_papers(self) -> None:
        """bulk_sync_papers should batch-write to both Qdrant and Typesense."""
        mock_vector, mock_search, sync = _make_services()

        mock_vector.upsert_batch.return_value = 2
        mock_search.index_papers_batch.return_value = [
            {"success": True},
            {"success": True},
            {"success": True},
        ]

        org_id = uuid4()
        papers = [
            {
                "paper_id": uuid4(),
                "organization_id": org_id,
                "title": "Paper 1",
                "embedding": _dummy_vector(),
            },
            {
                "paper_id": uuid4(),
                "organization_id": org_id,
                "title": "Paper 2",
                "embedding": _dummy_vector(),
            },
            {
                "paper_id": uuid4(),
                "organization_id": org_id,
                "title": "Paper 3 (no embedding)",
            },
        ]

        result = await sync.bulk_sync_papers(papers)

        # Qdrant: only papers with embeddings (2)
        mock_vector.upsert_batch.assert_awaited_once()
        batch_args = mock_vector.upsert_batch.await_args
        assert batch_args.args[0] == "papers"
        assert len(batch_args.args[1]) == 2  # 2 papers with embeddings

        # Typesense: all 3 papers
        mock_search.index_papers_batch.assert_called_once()
        assert len(mock_search.index_papers_batch.call_args[0][0]) == 3

        assert result["vectors_synced"] == 2
        assert result["documents_synced"] == 3
        assert result["errors"] == 0

    async def test_bulk_sync_papers_no_embeddings(self) -> None:
        """When no papers have embeddings, Qdrant batch should be skipped."""
        mock_vector, mock_search, sync = _make_services()

        mock_search.index_papers_batch.return_value = [{"success": True}]

        papers = [
            {
                "paper_id": uuid4(),
                "organization_id": uuid4(),
                "title": "No Embedding",
            },
        ]

        result = await sync.bulk_sync_papers(papers)

        mock_vector.upsert_batch.assert_not_awaited()
        mock_search.index_papers_batch.assert_called_once()
        assert result["vectors_synced"] == 0
        assert result["documents_synced"] == 1

    async def test_bulk_sync_papers_qdrant_failure(self) -> None:
        """Qdrant batch failure should be counted as errors, Typesense still proceeds."""
        mock_vector, mock_search, sync = _make_services()

        mock_vector.upsert_batch.side_effect = Exception("Qdrant down")
        mock_search.index_papers_batch.return_value = [{"success": True}]

        papers = [
            {
                "paper_id": uuid4(),
                "organization_id": uuid4(),
                "title": "Paper",
                "embedding": _dummy_vector(),
            },
        ]

        result = await sync.bulk_sync_papers(papers)

        assert result["vectors_synced"] == 0
        assert result["errors"] >= 1
        # Typesense still called
        mock_search.index_papers_batch.assert_called_once()

    async def test_bulk_sync_papers_typesense_failure(self) -> None:
        """Typesense batch failure should be counted as errors."""
        mock_vector, mock_search, sync = _make_services()

        mock_vector.upsert_batch.return_value = 1
        mock_search.index_papers_batch.side_effect = Exception("Typesense down")

        papers = [
            {
                "paper_id": uuid4(),
                "organization_id": uuid4(),
                "title": "Paper",
                "embedding": _dummy_vector(),
            },
        ]

        result = await sync.bulk_sync_papers(papers)

        assert result["vectors_synced"] == 1
        assert result["errors"] >= 1

    async def test_bulk_sync_papers_empty_list(self) -> None:
        """An empty papers list should return zeroes with no calls."""
        mock_vector, mock_search, sync = _make_services()

        result = await sync.bulk_sync_papers([])

        mock_vector.upsert_batch.assert_not_awaited()
        mock_search.index_papers_batch.assert_not_called()
        assert result == {"vectors_synced": 0, "documents_synced": 0, "errors": 0}

    async def test_bulk_sync_papers_respects_batch_size(self) -> None:
        """batch_size parameter should be forwarded to upsert_batch."""
        mock_vector, mock_search, sync = _make_services()

        mock_vector.upsert_batch.return_value = 1
        mock_search.index_papers_batch.return_value = [{"success": True}]

        papers = [
            {
                "paper_id": uuid4(),
                "organization_id": uuid4(),
                "title": "Paper",
                "embedding": _dummy_vector(),
            },
        ]

        await sync.bulk_sync_papers(papers, batch_size=50)

        kwargs = mock_vector.upsert_batch.await_args.kwargs
        assert kwargs["batch_size"] == 50
