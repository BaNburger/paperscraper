"""Unit tests for paper_scraper.core.sync — SyncService Typesense integration.

All tests mock SearchEngineService to verify that the SyncService correctly
delegates writes to Typesense and handles errors gracefully. Embeddings are
handled directly via pgvector (no sync needed).
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

from paper_scraper.core.sync import SyncService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_service() -> tuple[MagicMock, SyncService]:
    """Create a SyncService with a mocked SearchEngineService.

    Returns:
        (mock_search, sync_service) tuple
    """
    mock_search = MagicMock()
    sync = SyncService(search_service=mock_search)
    return mock_search, sync


# ---------------------------------------------------------------------------
# Paper Sync (Typesense only)
# ---------------------------------------------------------------------------


class TestSyncPaper:
    """Tests for SyncService.sync_paper."""

    def test_sync_paper_indexes_to_typesense(self) -> None:
        """sync_paper should index the paper document to Typesense."""
        mock_search, sync = _make_service()

        paper_id = uuid4()
        org_id = uuid4()

        sync.sync_paper(
            paper_id=paper_id,
            organization_id=org_id,
            title="Test Paper",
            abstract="Abstract text",
        )

        mock_search.index_paper.assert_called_once()
        doc = mock_search.index_paper.call_args[0][0]
        assert doc["paper_id"] == str(paper_id)
        assert doc["title"] == "Test Paper"

    def test_sync_paper_with_global_flag(self) -> None:
        """sync_paper should pass is_global to Typesense document."""
        mock_search, sync = _make_service()

        sync.sync_paper(
            paper_id=uuid4(),
            organization_id=None,
            title="Global Paper",
            is_global=True,
        )

        doc = mock_search.index_paper.call_args[0][0]
        assert doc["is_global"] is True
        assert "organization_id" not in doc

    def test_sync_paper_with_metadata(self) -> None:
        """sync_paper should pass all metadata fields to Typesense."""
        mock_search, sync = _make_service()
        created = datetime(2024, 7, 1, 12, 0, 0)

        sync.sync_paper(
            paper_id=uuid4(),
            organization_id=uuid4(),
            title="With Metadata",
            doi="10.1234/test",
            source="pubmed",
            journal="Nature",
            keywords=["ML", "AI"],
            has_embedding=True,
            created_at=created,
        )

        doc = mock_search.index_paper.call_args[0][0]
        assert doc["doi"] == "10.1234/test"
        assert doc["source"] == "pubmed"
        assert doc["journal"] == "Nature"
        assert doc["keywords"] == ["ML", "AI"]
        assert doc["has_embedding"] is True

    def test_sync_paper_typesense_failure_doesnt_raise(self) -> None:
        """If Typesense indexing fails, the exception should be caught."""
        mock_search, sync = _make_service()
        mock_search.index_paper.side_effect = Exception("Typesense down")

        # Should NOT raise
        sync.sync_paper(
            paper_id=uuid4(),
            organization_id=uuid4(),
            title="Failing Paper",
        )


# ---------------------------------------------------------------------------
# Delete Operations
# ---------------------------------------------------------------------------


class TestDeletePaper:
    """Tests for SyncService.delete_paper."""

    def test_delete_paper_from_typesense(self) -> None:
        """delete_paper should remove from Typesense."""
        mock_search, sync = _make_service()
        paper_id = uuid4()

        sync.delete_paper(paper_id)

        mock_search.delete_paper.assert_called_once_with(str(paper_id))

    def test_delete_paper_failure_doesnt_raise(self) -> None:
        """Typesense delete failure should be caught."""
        mock_search, sync = _make_service()
        mock_search.delete_paper.side_effect = Exception("Typesense error")

        # Should NOT raise
        sync.delete_paper(uuid4())


class TestDeleteOrgData:
    """Tests for SyncService.delete_org_data."""

    def test_delete_org_data_from_typesense(self) -> None:
        """delete_org_data should remove all org papers from Typesense."""
        mock_search, sync = _make_service()
        org_id = uuid4()

        sync.delete_org_data(org_id)

        mock_search.delete_papers_by_org.assert_called_once_with(org_id)

    def test_delete_org_data_failure_doesnt_raise(self) -> None:
        """Typesense failure should be caught."""
        mock_search, sync = _make_service()
        mock_search.delete_papers_by_org.side_effect = Exception("error")

        # Should NOT raise
        sync.delete_org_data(uuid4())


# ---------------------------------------------------------------------------
# Bulk Sync
# ---------------------------------------------------------------------------


class TestBulkSyncPapers:
    """Tests for SyncService.bulk_sync_papers."""

    def test_bulk_sync_indexes_all_papers(self) -> None:
        """bulk_sync_papers should batch-index all papers to Typesense."""
        mock_search, sync = _make_service()
        mock_search.index_papers_batch.return_value = [
            {"success": True},
            {"success": True},
        ]

        papers = [
            {"paper_id": uuid4(), "organization_id": uuid4(), "title": "Paper 1"},
            {"paper_id": uuid4(), "organization_id": uuid4(), "title": "Paper 2"},
        ]

        result = sync.bulk_sync_papers(papers)

        mock_search.index_papers_batch.assert_called_once()
        assert result["documents_synced"] == 2
        assert result["errors"] == 0

    def test_bulk_sync_empty_list(self) -> None:
        """An empty papers list should return zeroes with no calls."""
        mock_search, sync = _make_service()

        result = sync.bulk_sync_papers([])

        mock_search.index_papers_batch.assert_not_called()
        assert result == {"documents_synced": 0, "errors": 0}

    def test_bulk_sync_typesense_failure(self) -> None:
        """Typesense batch failure should be counted as errors."""
        mock_search, sync = _make_service()
        mock_search.index_papers_batch.side_effect = Exception("Typesense down")

        papers = [
            {"paper_id": uuid4(), "organization_id": uuid4(), "title": "Paper"},
        ]

        result = sync.bulk_sync_papers(papers)

        assert result["errors"] >= 1
