"""Unit tests for paper_scraper.core.search_engine — Typesense SearchEngineService.

All tests mock the typesense.Client so no real Typesense instance is needed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from paper_scraper.core.search_engine import (
    PAPERS_SCHEMA,
    SearchEngineService,
    _collection_name,
    _datetime_to_epoch,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_service(mock_client: MagicMock | None = None) -> SearchEngineService:
    """Create a SearchEngineService with a mocked Typesense client."""
    client = mock_client or MagicMock()
    return SearchEngineService(client=client)


# ---------------------------------------------------------------------------
# Collection Management
# ---------------------------------------------------------------------------


class TestEnsureCollections:
    """Tests for SearchEngineService.ensure_collections."""

    async def test_ensure_collections_creates_schema_when_missing(self) -> None:
        """When the collection does not exist, it should be created with PAPERS_SCHEMA."""
        import typesense.exceptions

        mock_client = MagicMock()
        # Simulate ObjectNotFound on retrieve
        mock_collection = MagicMock()
        mock_collection.retrieve.side_effect = typesense.exceptions.ObjectNotFound(
            "Not found"
        )
        mock_client.collections.__getitem__.return_value = mock_collection

        service = _make_service(mock_client)
        await service.ensure_collections()

        mock_client.collections.create.assert_called_once()
        create_arg = mock_client.collections.create.call_args[0][0]
        assert create_arg["name"] == _collection_name("papers")
        assert "fields" in create_arg

    async def test_ensure_collections_skips_existing(self) -> None:
        """When the collection already exists, create should not be called."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.retrieve.return_value = {"name": _collection_name("papers")}
        mock_client.collections.__getitem__.return_value = mock_collection

        service = _make_service(mock_client)
        await service.ensure_collections()

        mock_client.collections.create.assert_not_called()


class TestDeleteCollections:
    """Tests for SearchEngineService.delete_collections."""

    async def test_delete_collections(self) -> None:
        """delete_collections should attempt to delete the papers collection."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.collections.__getitem__.return_value = mock_collection

        service = _make_service(mock_client)
        await service.delete_collections()

        mock_collection.delete.assert_called_once()

    async def test_delete_collections_ignores_errors(self) -> None:
        """delete_collections should not raise if delete fails."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.delete.side_effect = Exception("not found")
        mock_client.collections.__getitem__.return_value = mock_collection

        service = _make_service(mock_client)
        # Should not raise
        await service.delete_collections()


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------


class TestIndexPaper:
    """Tests for SearchEngineService.index_paper."""

    def test_index_paper(self) -> None:
        """index_paper should upsert the document to the correct collection."""
        mock_client = MagicMock()
        mock_docs = MagicMock()
        mock_client.collections.__getitem__.return_value.documents = mock_docs

        service = _make_service(mock_client)

        paper_id = uuid4()
        org_id = uuid4()
        doc = {
            "id": str(paper_id),
            "paper_id": str(paper_id),
            "organization_id": str(org_id),
            "title": "Test Paper",
            "created_at": 1700000000,
        }

        service.index_paper(doc)

        mock_docs.upsert.assert_called_once_with(doc)

    def test_index_paper_uses_correct_collection_name(self) -> None:
        """index_paper should use the prefixed collection name."""
        mock_client = MagicMock()
        service = _make_service(mock_client)

        doc = {"id": "test", "title": "Test", "created_at": 0}
        service.index_paper(doc)

        mock_client.collections.__getitem__.assert_called_with(
            _collection_name("papers")
        )


class TestIndexPapersBatch:
    """Tests for SearchEngineService.index_papers_batch."""

    def test_index_papers_batch(self) -> None:
        """Batch import should call import_ with papers and action param."""
        mock_client = MagicMock()
        mock_docs = MagicMock()
        mock_docs.import_.return_value = [{"success": True}, {"success": True}]
        mock_client.collections.__getitem__.return_value.documents = mock_docs

        service = _make_service(mock_client)

        papers = [
            {"id": str(uuid4()), "title": "Paper 1", "created_at": 0},
            {"id": str(uuid4()), "title": "Paper 2", "created_at": 0},
        ]

        results = service.index_papers_batch(papers)

        mock_docs.import_.assert_called_once_with(papers, {"action": "upsert"})
        assert len(results) == 2

    def test_index_papers_batch_custom_action(self) -> None:
        """index_papers_batch should respect the action parameter."""
        mock_client = MagicMock()
        mock_docs = MagicMock()
        mock_docs.import_.return_value = []
        mock_client.collections.__getitem__.return_value.documents = mock_docs

        service = _make_service(mock_client)
        service.index_papers_batch([], action="create")

        # Empty list returns early, no import call
        mock_docs.import_.assert_not_called()

    def test_index_papers_batch_empty_returns_empty(self) -> None:
        """An empty list should return [] without calling import_."""
        mock_client = MagicMock()
        mock_docs = MagicMock()
        mock_client.collections.__getitem__.return_value.documents = mock_docs

        service = _make_service(mock_client)
        results = service.index_papers_batch([])

        assert results == []
        mock_docs.import_.assert_not_called()


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


class TestDeletePaper:
    """Tests for SearchEngineService.delete_paper."""

    def test_delete_paper(self) -> None:
        """delete_paper should call documents[paper_id].delete()."""
        mock_client = MagicMock()
        mock_doc = MagicMock()
        mock_client.collections.__getitem__.return_value.documents.__getitem__.return_value = mock_doc

        service = _make_service(mock_client)
        paper_id = str(uuid4())
        service.delete_paper(paper_id)

        mock_client.collections.__getitem__.return_value.documents.__getitem__.assert_called_with(
            paper_id
        )
        mock_doc.delete.assert_called_once()

    def test_delete_paper_not_found_is_silent(self) -> None:
        """delete_paper should not raise if document is not found."""
        import typesense.exceptions

        mock_client = MagicMock()
        mock_doc = MagicMock()
        mock_doc.delete.side_effect = typesense.exceptions.ObjectNotFound("Not found")
        mock_client.collections.__getitem__.return_value.documents.__getitem__.return_value = mock_doc

        service = _make_service(mock_client)
        # Should not raise
        service.delete_paper(str(uuid4()))


class TestDeletePapersByOrg:
    """Tests for SearchEngineService.delete_papers_by_org."""

    def test_delete_papers_by_org(self) -> None:
        """delete_papers_by_org should apply filter_by with organization_id."""
        mock_client = MagicMock()
        mock_docs = MagicMock()
        mock_docs.delete.return_value = {"num_deleted": 15}
        mock_client.collections.__getitem__.return_value.documents = mock_docs

        service = _make_service(mock_client)
        org_id = uuid4()
        result = service.delete_papers_by_org(org_id)

        assert result == 15
        mock_docs.delete.assert_called_once()
        filter_arg = mock_docs.delete.call_args[0][0]
        assert f"organization_id:={org_id}" in filter_arg["filter_by"]


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


class TestSearchPapers:
    """Tests for SearchEngineService.search_papers."""

    def test_search_papers_basic(self) -> None:
        """search_papers should call documents.search with correct params."""
        mock_client = MagicMock()
        mock_docs = MagicMock()
        mock_docs.search.return_value = {"found": 1, "hits": [{"document": {}}]}
        mock_client.collections.__getitem__.return_value.documents = mock_docs

        service = _make_service(mock_client)
        org_id = uuid4()

        result = service.search_papers(
            query="machine learning",
            organization_id=org_id,
            page=1,
            page_size=20,
        )

        mock_docs.search.assert_called_once()
        search_params = mock_docs.search.call_args[0][0]

        assert search_params["q"] == "machine learning"
        assert search_params["query_by"] == "title,abstract,keywords"
        assert f"organization_id:={org_id}" in search_params["filter_by"]
        assert search_params["per_page"] == 20
        assert search_params["page"] == 1

    def test_search_papers_with_additional_filter(self) -> None:
        """Additional filter_by should be combined with org filter via &&."""
        mock_client = MagicMock()
        mock_docs = MagicMock()
        mock_docs.search.return_value = {"found": 0, "hits": []}
        mock_client.collections.__getitem__.return_value.documents = mock_docs

        service = _make_service(mock_client)
        org_id = uuid4()

        service.search_papers(
            query="crispr",
            organization_id=org_id,
            filter_by="source:=openalex",
        )

        search_params = mock_docs.search.call_args[0][0]
        filter_str = search_params["filter_by"]
        assert f"organization_id:={org_id}" in filter_str
        assert "source:=openalex" in filter_str
        assert "&&" in filter_str

    def test_search_papers_with_sort_and_facet(self) -> None:
        """sort_by and facet_by should be included in search params."""
        mock_client = MagicMock()
        mock_docs = MagicMock()
        mock_docs.search.return_value = {"found": 0, "hits": []}
        mock_client.collections.__getitem__.return_value.documents = mock_docs

        service = _make_service(mock_client)

        service.search_papers(
            query="*",
            organization_id=uuid4(),
            sort_by="created_at:desc",
            facet_by="source,paper_type",
        )

        search_params = mock_docs.search.call_args[0][0]
        assert search_params["sort_by"] == "created_at:desc"
        assert search_params["facet_by"] == "source,paper_type"

    def test_search_papers_typo_tolerance_enabled(self) -> None:
        """num_typos should be set to 2 for typo tolerance."""
        mock_client = MagicMock()
        mock_docs = MagicMock()
        mock_docs.search.return_value = {"found": 0, "hits": []}
        mock_client.collections.__getitem__.return_value.documents = mock_docs

        service = _make_service(mock_client)
        service.search_papers(query="test", organization_id=uuid4())

        search_params = mock_docs.search.call_args[0][0]
        assert search_params["num_typos"] == 2


# ---------------------------------------------------------------------------
# paper_to_document
# ---------------------------------------------------------------------------


class TestPaperToDocument:
    """Tests for SearchEngineService.paper_to_document static method."""

    def test_paper_to_document_required_fields(self) -> None:
        """paper_to_document should always include id, paper_id, organization_id, title, created_at."""
        paper_id = uuid4()
        org_id = uuid4()

        doc = SearchEngineService.paper_to_document(
            paper_id=paper_id,
            organization_id=org_id,
            title="Test Paper",
        )

        assert doc["id"] == str(paper_id)
        assert doc["paper_id"] == str(paper_id)
        assert doc["organization_id"] == str(org_id)
        assert doc["title"] == "Test Paper"
        assert doc["created_at"] == 0  # None datetime -> 0

    def test_paper_to_document_all_optional_fields(self) -> None:
        """All optional fields should be included when provided."""
        paper_id = uuid4()
        org_id = uuid4()
        pub_date = datetime(2024, 6, 15)
        created = datetime(2024, 7, 1)

        doc = SearchEngineService.paper_to_document(
            paper_id=paper_id,
            organization_id=org_id,
            title="Full Paper",
            abstract="This is the abstract.",
            doi="10.1234/test",
            source="openalex",
            journal="Nature",
            paper_type="article",
            keywords=["ai", "ml"],
            overall_score=8.5,
            citations_count=42,
            has_embedding=True,
            publication_date=pub_date,
            created_at=created,
        )

        assert doc["abstract"] == "This is the abstract."
        assert doc["doi"] == "10.1234/test"
        assert doc["source"] == "openalex"
        assert doc["journal"] == "Nature"
        assert doc["paper_type"] == "article"
        assert doc["keywords"] == ["ai", "ml"]
        assert doc["overall_score"] == 8.5
        assert doc["citations_count"] == 42
        assert doc["has_embedding"] is True
        assert doc["publication_date"] == int(pub_date.timestamp())
        assert doc["created_at"] == int(created.timestamp())

    def test_paper_to_document_omits_none_optionals(self) -> None:
        """Optional fields that are None should not appear in the document."""
        doc = SearchEngineService.paper_to_document(
            paper_id=uuid4(),
            organization_id=uuid4(),
            title="Minimal",
        )

        assert "abstract" not in doc
        assert "doi" not in doc
        assert "source" not in doc
        assert "journal" not in doc
        assert "paper_type" not in doc
        assert "keywords" not in doc
        assert "overall_score" not in doc
        assert "citations_count" not in doc
        assert "has_embedding" not in doc
        assert "publication_date" not in doc

    def test_paper_to_document_empty_keywords_excluded(self) -> None:
        """Empty keywords list should not be included (falsy check)."""
        doc = SearchEngineService.paper_to_document(
            paper_id=uuid4(),
            organization_id=uuid4(),
            title="No Keywords",
            keywords=[],
        )

        assert "keywords" not in doc

    def test_paper_to_document_has_embedding_false_excluded(self) -> None:
        """has_embedding=False (default) should not be included."""
        doc = SearchEngineService.paper_to_document(
            paper_id=uuid4(),
            organization_id=uuid4(),
            title="No Embedding",
            has_embedding=False,
        )

        assert "has_embedding" not in doc


# ---------------------------------------------------------------------------
# _datetime_to_epoch helper
# ---------------------------------------------------------------------------


class TestDatetimeToEpoch:
    """Tests for the _datetime_to_epoch helper function."""

    def test_none_returns_none(self) -> None:
        assert _datetime_to_epoch(None) is None

    def test_datetime_converts_to_epoch(self) -> None:
        dt = datetime(2024, 1, 1, 0, 0, 0)
        result = _datetime_to_epoch(dt)
        assert isinstance(result, int)
        assert result == int(dt.timestamp())

    def test_epoch_is_integer(self) -> None:
        """Result should be an integer, not a float."""
        dt = datetime(2024, 6, 15, 12, 30, 45)
        result = _datetime_to_epoch(dt)
        assert isinstance(result, int)


# ---------------------------------------------------------------------------
# _collection_name helper
# ---------------------------------------------------------------------------


class TestCollectionName:
    """Tests for the _collection_name helper."""

    def test_with_empty_prefix(self) -> None:
        with patch("paper_scraper.core.search_engine.settings") as mock_settings:
            mock_settings.TYPESENSE_COLLECTION_PREFIX = ""
            assert _collection_name("papers") == "papers"

    def test_with_prefix(self) -> None:
        with patch("paper_scraper.core.search_engine.settings") as mock_settings:
            mock_settings.TYPESENSE_COLLECTION_PREFIX = "test_"
            assert _collection_name("papers") == "test_papers"


# ---------------------------------------------------------------------------
# Multi-search
# ---------------------------------------------------------------------------


class TestMultiSearch:
    """Tests for SearchEngineService.multi_search."""

    def test_multi_search(self) -> None:
        """multi_search should call multi_search.perform with search params."""
        mock_client = MagicMock()
        mock_multi = MagicMock()
        mock_multi.perform.return_value = {"results": []}
        mock_client.multi_search = mock_multi

        service = _make_service(mock_client)
        searches = [
            {"q": "test1", "collection": "papers"},
            {"q": "test2", "collection": "papers"},
        ]

        result = service.multi_search(searches)

        mock_multi.perform.assert_called_once()
        call_args = mock_multi.perform.call_args[0]
        assert call_args[0] == {"searches": searches}
