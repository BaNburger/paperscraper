"""Unit tests for paper_scraper.core.vector — Qdrant VectorService.

All tests mock the AsyncQdrantClient so no real Qdrant instance is needed.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from qdrant_client import models

from paper_scraper.core.vector import COLLECTIONS, VectorService, _collection_name


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_collection(name: str) -> MagicMock:
    """Return a mock collection description with the given name."""
    col = MagicMock()
    col.name = name
    return col


def _make_service(mock_client: AsyncMock) -> VectorService:
    """Create a VectorService pre-wired with a mocked Qdrant client."""
    return VectorService(client=mock_client)


def _dummy_vector(dim: int = 1536) -> list[float]:
    """Return a zero-filled embedding of the given dimension."""
    return [0.0] * dim


# ---------------------------------------------------------------------------
# Collection Management
# ---------------------------------------------------------------------------


class TestEnsureCollections:
    """Tests for VectorService.ensure_collections."""

    async def test_ensure_collections_creates_missing(self) -> None:
        """When no collections exist, all 5 should be created."""
        mock_client = AsyncMock()

        # get_collections returns empty list
        collections_response = MagicMock()
        collections_response.collections = []
        mock_client.get_collections.return_value = collections_response

        service = _make_service(mock_client)
        await service.ensure_collections()

        assert mock_client.create_collection.await_count == len(COLLECTIONS)
        assert mock_client.create_payload_index.await_count == len(COLLECTIONS)

        # Verify each collection was created with its correct dimension
        created_names = [
            call.kwargs["collection_name"]
            for call in mock_client.create_collection.await_args_list
        ]
        for name in COLLECTIONS:
            assert _collection_name(name) in created_names

    async def test_ensure_collections_skips_existing(self) -> None:
        """Collections that already exist should not be re-created."""
        mock_client = AsyncMock()

        # Pretend "papers" and "authors" already exist
        existing = [
            _fake_collection(_collection_name("papers")),
            _fake_collection(_collection_name("authors")),
        ]
        collections_response = MagicMock()
        collections_response.collections = existing
        mock_client.get_collections.return_value = collections_response

        service = _make_service(mock_client)
        await service.ensure_collections()

        # Should only create the 3 missing collections (clusters, searches, trends)
        expected_count = len(COLLECTIONS) - 2
        assert mock_client.create_collection.await_count == expected_count

    async def test_ensure_collections_creates_payload_index(self) -> None:
        """Each new collection should get an organization_id payload index."""
        mock_client = AsyncMock()

        collections_response = MagicMock()
        collections_response.collections = []
        mock_client.get_collections.return_value = collections_response

        service = _make_service(mock_client)
        await service.ensure_collections()

        for call in mock_client.create_payload_index.await_args_list:
            assert call.kwargs["field_name"] == "organization_id"
            assert call.kwargs["field_schema"] == models.PayloadSchemaType.KEYWORD


# ---------------------------------------------------------------------------
# Upsert Operations
# ---------------------------------------------------------------------------


class TestUpsert:
    """Tests for VectorService.upsert (single point)."""

    async def test_upsert_single_point(self) -> None:
        """Upsert should call client.upsert with correctly structured point."""
        mock_client = AsyncMock()
        service = _make_service(mock_client)

        paper_id = uuid4()
        org_id = uuid4()
        vector = _dummy_vector()
        payload = {"organization_id": str(org_id), "paper_id": str(paper_id)}

        await service.upsert(
            collection="papers",
            point_id=paper_id,
            vector=vector,
            payload=payload,
        )

        mock_client.upsert.assert_awaited_once()
        call_kwargs = mock_client.upsert.await_args.kwargs
        assert call_kwargs["collection_name"] == _collection_name("papers")

        points = call_kwargs["points"]
        assert len(points) == 1
        assert points[0].id == str(paper_id)
        assert points[0].vector == vector
        assert points[0].payload == payload


class TestUpsertBatch:
    """Tests for VectorService.upsert_batch."""

    async def test_upsert_batch_single_chunk(self) -> None:
        """A batch smaller than batch_size should result in a single upsert call."""
        mock_client = AsyncMock()
        service = _make_service(mock_client)

        points = [
            {"id": uuid4(), "vector": _dummy_vector(), "payload": {"organization_id": "x"}}
            for _ in range(5)
        ]

        total = await service.upsert_batch("papers", points, batch_size=100)

        assert total == 5
        mock_client.upsert.assert_awaited_once()

    async def test_upsert_batch_splits_into_chunks(self) -> None:
        """A batch larger than batch_size should be split into multiple upsert calls."""
        mock_client = AsyncMock()
        service = _make_service(mock_client)

        points = [
            {"id": uuid4(), "vector": _dummy_vector(), "payload": {"organization_id": "x"}}
            for _ in range(250)
        ]

        total = await service.upsert_batch("papers", points, batch_size=100)

        assert total == 250
        # 250 / 100 = 3 chunks (100 + 100 + 50)
        assert mock_client.upsert.await_count == 3

    async def test_upsert_batch_empty_list(self) -> None:
        """An empty batch should return 0 and make no calls."""
        mock_client = AsyncMock()
        service = _make_service(mock_client)

        total = await service.upsert_batch("papers", [], batch_size=100)

        assert total == 0
        mock_client.upsert.assert_not_awaited()


# ---------------------------------------------------------------------------
# Search Operations
# ---------------------------------------------------------------------------


class TestSearch:
    """Tests for VectorService.search."""

    async def test_search_with_org_filter(self) -> None:
        """Search must apply organization_id as a must-filter condition."""
        mock_client = AsyncMock()
        org_id = uuid4()

        # Build mock response
        mock_point = MagicMock()
        mock_point.id = str(uuid4())
        mock_point.score = 0.95
        mock_point.payload = {"organization_id": str(org_id)}

        query_response = MagicMock()
        query_response.points = [mock_point]
        mock_client.query_points.return_value = query_response

        service = _make_service(mock_client)
        results = await service.search(
            collection="papers",
            query_vector=_dummy_vector(),
            organization_id=org_id,
            limit=10,
        )

        mock_client.query_points.assert_awaited_once()
        call_kwargs = mock_client.query_points.await_args.kwargs

        # Verify org filter is present
        query_filter = call_kwargs["query_filter"]
        assert isinstance(query_filter, models.Filter)
        assert len(query_filter.must) >= 1

        org_condition = query_filter.must[0]
        assert isinstance(org_condition, models.FieldCondition)
        assert org_condition.key == "organization_id"
        assert org_condition.match.value == str(org_id)

        # Verify result structure
        assert len(results) == 1
        assert results[0]["id"] == mock_point.id
        assert results[0]["score"] == 0.95

    async def test_search_with_extra_filters(self) -> None:
        """Extra filter conditions should be appended to the must clause."""
        mock_client = AsyncMock()
        org_id = uuid4()

        query_response = MagicMock()
        query_response.points = []
        mock_client.query_points.return_value = query_response

        extra = models.FieldCondition(
            key="source",
            match=models.MatchValue(value="openalex"),
        )

        service = _make_service(mock_client)
        await service.search(
            collection="papers",
            query_vector=_dummy_vector(),
            organization_id=org_id,
            extra_filters=[extra],
        )

        call_kwargs = mock_client.query_points.await_args.kwargs
        query_filter = call_kwargs["query_filter"]
        assert len(query_filter.must) == 2  # org filter + extra filter

    async def test_search_with_min_score(self) -> None:
        """min_score should be passed as score_threshold."""
        mock_client = AsyncMock()

        query_response = MagicMock()
        query_response.points = []
        mock_client.query_points.return_value = query_response

        service = _make_service(mock_client)
        await service.search(
            collection="papers",
            query_vector=_dummy_vector(),
            organization_id=uuid4(),
            min_score=0.7,
        )

        call_kwargs = mock_client.query_points.await_args.kwargs
        assert call_kwargs["score_threshold"] == 0.7


class TestSearchById:
    """Tests for VectorService.search_by_id."""

    async def test_search_by_id_excludes_self(self) -> None:
        """search_by_id must include a must_not filter to exclude the source point."""
        mock_client = AsyncMock()
        point_id = uuid4()
        org_id = uuid4()

        query_response = MagicMock()
        query_response.points = []
        mock_client.query_points.return_value = query_response

        service = _make_service(mock_client)
        await service.search_by_id(
            collection="papers",
            point_id=point_id,
            organization_id=org_id,
        )

        mock_client.query_points.assert_awaited_once()
        call_kwargs = mock_client.query_points.await_args.kwargs

        query_filter = call_kwargs["query_filter"]
        assert query_filter.must_not is not None
        assert len(query_filter.must_not) == 1

        exclude_condition = query_filter.must_not[0]
        assert isinstance(exclude_condition, models.HasIdCondition)
        assert str(point_id) in exclude_condition.has_id

    async def test_search_by_id_uses_point_id_as_query(self) -> None:
        """search_by_id should pass the point_id string as the query."""
        mock_client = AsyncMock()
        point_id = uuid4()

        query_response = MagicMock()
        query_response.points = []
        mock_client.query_points.return_value = query_response

        service = _make_service(mock_client)
        await service.search_by_id(
            collection="papers",
            point_id=point_id,
            organization_id=uuid4(),
        )

        call_kwargs = mock_client.query_points.await_args.kwargs
        assert call_kwargs["query"] == str(point_id)


# ---------------------------------------------------------------------------
# Delete Operations
# ---------------------------------------------------------------------------


class TestDelete:
    """Tests for VectorService.delete."""

    async def test_delete_point(self) -> None:
        """delete should call client.delete with a PointIdsList selector."""
        mock_client = AsyncMock()
        service = _make_service(mock_client)
        paper_id = uuid4()

        await service.delete("papers", paper_id)

        mock_client.delete.assert_awaited_once()
        call_kwargs = mock_client.delete.await_args.kwargs
        assert call_kwargs["collection_name"] == _collection_name("papers")

        selector = call_kwargs["points_selector"]
        assert isinstance(selector, models.PointIdsList)
        assert str(paper_id) in selector.points


class TestDeleteByOrg:
    """Tests for VectorService.delete_by_org."""

    async def test_delete_by_org(self) -> None:
        """delete_by_org should use a FilterSelector with organization_id match."""
        mock_client = AsyncMock()
        service = _make_service(mock_client)
        org_id = uuid4()

        await service.delete_by_org("papers", org_id)

        mock_client.delete.assert_awaited_once()
        call_kwargs = mock_client.delete.await_args.kwargs
        assert call_kwargs["collection_name"] == _collection_name("papers")

        selector = call_kwargs["points_selector"]
        assert isinstance(selector, models.FilterSelector)

        org_condition = selector.filter.must[0]
        assert org_condition.key == "organization_id"
        assert org_condition.match.value == str(org_id)


# ---------------------------------------------------------------------------
# Utility Methods
# ---------------------------------------------------------------------------


class TestGetPoint:
    """Tests for VectorService.get_point."""

    async def test_get_point_with_vector(self) -> None:
        """When with_vector=True, the returned dict should include the vector."""
        mock_client = AsyncMock()
        point_id = uuid4()
        expected_vector = _dummy_vector()

        mock_point = MagicMock()
        mock_point.id = str(point_id)
        mock_point.payload = {"organization_id": "some-org"}
        mock_point.vector = expected_vector

        mock_client.retrieve.return_value = [mock_point]

        service = _make_service(mock_client)
        result = await service.get_point("papers", point_id, with_vector=True)

        assert result is not None
        assert result["id"] == str(point_id)
        assert result["vector"] == expected_vector
        assert result["payload"] == {"organization_id": "some-org"}

        mock_client.retrieve.assert_awaited_once()
        call_kwargs = mock_client.retrieve.await_args.kwargs
        assert call_kwargs["with_vectors"] is True

    async def test_get_point_without_vector(self) -> None:
        """When with_vector=False (default), no vector key should be present."""
        mock_client = AsyncMock()
        point_id = uuid4()

        mock_point = MagicMock()
        mock_point.id = str(point_id)
        mock_point.payload = {"organization_id": "some-org"}
        mock_point.vector = None

        mock_client.retrieve.return_value = [mock_point]

        service = _make_service(mock_client)
        result = await service.get_point("papers", point_id, with_vector=False)

        assert result is not None
        assert "vector" not in result

    async def test_get_point_not_found_returns_none(self) -> None:
        """When retrieve returns empty list, get_point should return None."""
        mock_client = AsyncMock()
        mock_client.retrieve.return_value = []

        service = _make_service(mock_client)
        result = await service.get_point("papers", uuid4())

        assert result is None

    async def test_get_point_exception_returns_none(self) -> None:
        """When retrieve raises, get_point should catch and return None."""
        mock_client = AsyncMock()
        mock_client.retrieve.side_effect = Exception("Connection refused")

        service = _make_service(mock_client)
        result = await service.get_point("papers", uuid4())

        assert result is None


class TestHasVector:
    """Tests for VectorService.has_vector."""

    async def test_has_vector_true(self) -> None:
        """Returns True when a point with the given ID exists."""
        mock_client = AsyncMock()
        point_id = uuid4()

        mock_point = MagicMock()
        mock_point.id = str(point_id)
        mock_client.retrieve.return_value = [mock_point]

        service = _make_service(mock_client)
        result = await service.has_vector("papers", point_id)

        assert result is True
        mock_client.retrieve.assert_awaited_once()
        call_kwargs = mock_client.retrieve.await_args.kwargs
        assert call_kwargs["with_vectors"] is False
        assert call_kwargs["with_payload"] is False

    async def test_has_vector_false(self) -> None:
        """Returns False when no point with the given ID exists."""
        mock_client = AsyncMock()
        mock_client.retrieve.return_value = []

        service = _make_service(mock_client)
        result = await service.has_vector("papers", uuid4())

        assert result is False

    async def test_has_vector_exception_returns_false(self) -> None:
        """Returns False when retrieve raises an exception."""
        mock_client = AsyncMock()
        mock_client.retrieve.side_effect = Exception("timeout")

        service = _make_service(mock_client)
        result = await service.has_vector("papers", uuid4())

        assert result is False


# ---------------------------------------------------------------------------
# Collection Name Prefix
# ---------------------------------------------------------------------------


class TestCollectionNamePrefix:
    """Tests for _collection_name helper."""

    def test_collection_name_with_empty_prefix(self) -> None:
        """With default empty prefix, name should pass through unchanged."""
        with patch("paper_scraper.core.vector.settings") as mock_settings:
            mock_settings.QDRANT_COLLECTION_PREFIX = ""
            assert _collection_name("papers") == "papers"

    def test_collection_name_with_prefix(self) -> None:
        """With a prefix set, collection name should be prefixed."""
        with patch("paper_scraper.core.vector.settings") as mock_settings:
            mock_settings.QDRANT_COLLECTION_PREFIX = "test_"
            assert _collection_name("papers") == "test_papers"

    def test_collection_name_preserves_original(self) -> None:
        """Prefix should be prepended without modifying the base name."""
        with patch("paper_scraper.core.vector.settings") as mock_settings:
            mock_settings.QDRANT_COLLECTION_PREFIX = "prod_v2_"
            assert _collection_name("authors") == "prod_v2_authors"


# ---------------------------------------------------------------------------
# Count
# ---------------------------------------------------------------------------


class TestCount:
    """Tests for VectorService.count."""

    async def test_count_with_org_filter(self) -> None:
        """count with organization_id should apply filter."""
        mock_client = AsyncMock()
        org_id = uuid4()

        count_result = MagicMock()
        count_result.count = 42
        mock_client.count.return_value = count_result

        service = _make_service(mock_client)
        result = await service.count("papers", organization_id=org_id)

        assert result == 42
        call_kwargs = mock_client.count.await_args.kwargs
        assert "count_filter" in call_kwargs

    async def test_count_without_org_filter(self) -> None:
        """count without organization_id should not apply filter."""
        mock_client = AsyncMock()

        count_result = MagicMock()
        count_result.count = 100
        mock_client.count.return_value = count_result

        service = _make_service(mock_client)
        result = await service.count("papers")

        assert result == 100
        call_kwargs = mock_client.count.await_args.kwargs
        assert "count_filter" not in call_kwargs


# ---------------------------------------------------------------------------
# Delete Collections
# ---------------------------------------------------------------------------


class TestDeleteCollections:
    """Tests for VectorService.delete_collections."""

    async def test_delete_collections_calls_for_all(self) -> None:
        """delete_collections should attempt to delete all managed collections."""
        mock_client = AsyncMock()
        service = _make_service(mock_client)

        await service.delete_collections()

        assert mock_client.delete_collection.await_count == len(COLLECTIONS)

    async def test_delete_collections_ignores_errors(self) -> None:
        """delete_collections should not raise even if deletes fail."""
        mock_client = AsyncMock()
        mock_client.delete_collection.side_effect = Exception("not found")

        service = _make_service(mock_client)

        # Should not raise
        await service.delete_collections()
