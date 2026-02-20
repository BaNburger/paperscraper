"""Qdrant vector search client for paper and author embeddings.

Replaces pgvector for all vector similarity operations. Provides tenant-isolated
filtered search, batch upsert, and collection management.

Collections:
    - papers: 1536d embeddings for paper semantic search
    - authors: 768d embeddings for author similarity
    - clusters: 1536d centroids for project clusters
    - searches: 1536d embeddings for saved searches
    - trends: 1536d embeddings for trend topics
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from qdrant_client import AsyncQdrantClient, models

from paper_scraper.core.config import settings

logger = logging.getLogger(__name__)

# Collection definitions: name -> vector dimension
COLLECTIONS: dict[str, int] = {
    "papers": 1536,
    "authors": 768,
    "clusters": 1536,
    "searches": 1536,
    "trends": 1536,
}

# Singleton client instance
_client: AsyncQdrantClient | None = None


async def get_qdrant_client() -> AsyncQdrantClient:
    """Get or create the async Qdrant client singleton."""
    global _client
    if _client is None:
        _client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
            timeout=30,
        )
    return _client


async def close_qdrant_client() -> None:
    """Close the Qdrant client connection."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None


def _collection_name(name: str) -> str:
    """Get the full collection name with optional prefix."""
    return f"{settings.QDRANT_COLLECTION_PREFIX}{name}"


class VectorService:
    """High-level vector search operations backed by Qdrant.

    All methods are tenant-isolated via organization_id payload filtering.
    """

    def __init__(self, client: AsyncQdrantClient | None = None) -> None:
        self._client = client

    async def _get_client(self) -> AsyncQdrantClient:
        if self._client is not None:
            return self._client
        return await get_qdrant_client()

    # =========================================================================
    # Collection Management
    # =========================================================================

    async def ensure_collections(self) -> None:
        """Create all vector collections if they don't exist."""
        client = await self._get_client()
        existing = {c.name for c in (await client.get_collections()).collections}

        for name, dimension in COLLECTIONS.items():
            full_name = _collection_name(name)
            if full_name in existing:
                continue

            await client.create_collection(
                collection_name=full_name,
                vectors_config=models.VectorParams(
                    size=dimension,
                    distance=models.Distance.COSINE,
                ),
                # Scalar quantization for ~4x memory savings at scale
                quantization_config=models.ScalarQuantization(
                    scalar=models.ScalarQuantizationConfig(
                        type=models.ScalarType.INT8,
                        quantile=0.99,
                        always_ram=True,
                    ),
                ),
            )

            # Create payload indexes for filtered search
            await client.create_payload_index(
                collection_name=full_name,
                field_name="organization_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

            logger.info("Created Qdrant collection: %s (dim=%d)", full_name, dimension)

    async def delete_collections(self) -> None:
        """Delete all managed collections. Used in testing."""
        client = await self._get_client()
        for name in COLLECTIONS:
            full_name = _collection_name(name)
            try:
                await client.delete_collection(full_name)
            except Exception:
                pass

    # =========================================================================
    # Upsert Operations
    # =========================================================================

    async def upsert(
        self,
        collection: str,
        point_id: UUID,
        vector: list[float],
        payload: dict[str, Any],
    ) -> None:
        """Upsert a single vector point.

        Args:
            collection: Collection name (e.g., "papers", "authors")
            point_id: Unique point ID (typically the entity's UUID)
            vector: Embedding vector
            payload: Metadata payload (must include organization_id)
        """
        client = await self._get_client()
        await client.upsert(
            collection_name=_collection_name(collection),
            points=[
                models.PointStruct(
                    id=str(point_id),
                    vector=vector,
                    payload=payload,
                )
            ],
        )

    async def upsert_batch(
        self,
        collection: str,
        points: list[dict[str, Any]],
        batch_size: int = 100,
    ) -> int:
        """Batch upsert vector points.

        Args:
            collection: Collection name
            points: List of dicts with keys: id (UUID), vector (list[float]), payload (dict)
            batch_size: Points per batch

        Returns:
            Number of points upserted
        """
        client = await self._get_client()
        full_name = _collection_name(collection)
        total = 0

        for start in range(0, len(points), batch_size):
            chunk = points[start : start + batch_size]
            qdrant_points = [
                models.PointStruct(
                    id=str(p["id"]),
                    vector=p["vector"],
                    payload=p["payload"],
                )
                for p in chunk
            ]
            await client.upsert(
                collection_name=full_name,
                points=qdrant_points,
            )
            total += len(chunk)

        return total

    # =========================================================================
    # Search Operations
    # =========================================================================

    async def search(
        self,
        collection: str,
        query_vector: list[float],
        organization_id: UUID,
        limit: int = 20,
        min_score: float | None = None,
        extra_filters: list[models.Condition] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors within a tenant.

        Args:
            collection: Collection name
            query_vector: Query embedding
            organization_id: Tenant isolation filter
            limit: Max results
            min_score: Minimum similarity score (0-1)
            extra_filters: Additional Qdrant filter conditions

        Returns:
            List of dicts with keys: id, score, payload
        """
        client = await self._get_client()

        must_conditions: list[models.Condition] = [
            models.FieldCondition(
                key="organization_id",
                match=models.MatchValue(value=str(organization_id)),
            ),
        ]
        if extra_filters:
            must_conditions.extend(extra_filters)

        results = await client.query_points(
            collection_name=_collection_name(collection),
            query=query_vector,
            query_filter=models.Filter(must=must_conditions),
            limit=limit,
            score_threshold=min_score,
            with_payload=True,
        )

        return [
            {
                "id": point.id,
                "score": point.score,
                "payload": point.payload or {},
            }
            for point in results.points
        ]

    async def search_by_id(
        self,
        collection: str,
        point_id: UUID,
        organization_id: UUID,
        limit: int = 10,
        min_score: float | None = None,
    ) -> list[dict[str, Any]]:
        """Find similar vectors to an existing point.

        Args:
            collection: Collection name
            point_id: ID of the reference point
            organization_id: Tenant isolation filter
            limit: Max results
            min_score: Minimum similarity score

        Returns:
            List of similar points (excluding the reference point)
        """
        client = await self._get_client()

        must_conditions: list[models.Condition] = [
            models.FieldCondition(
                key="organization_id",
                match=models.MatchValue(value=str(organization_id)),
            ),
        ]

        # Exclude the reference point itself
        must_not: list[models.Condition] = [
            models.HasIdCondition(has_id=[str(point_id)]),
        ]

        results = await client.query_points(
            collection_name=_collection_name(collection),
            query=str(point_id),
            using=None,
            query_filter=models.Filter(must=must_conditions, must_not=must_not),
            limit=limit,
            score_threshold=min_score,
            with_payload=True,
        )

        return [
            {
                "id": point.id,
                "score": point.score,
                "payload": point.payload or {},
            }
            for point in results.points
        ]

    # =========================================================================
    # Delete Operations
    # =========================================================================

    async def delete(self, collection: str, point_id: UUID) -> None:
        """Delete a single point by ID."""
        client = await self._get_client()
        await client.delete(
            collection_name=_collection_name(collection),
            points_selector=models.PointIdsList(
                points=[str(point_id)],
            ),
        )

    async def delete_by_org(self, collection: str, organization_id: UUID) -> None:
        """Delete all points for an organization (tenant cleanup)."""
        client = await self._get_client()
        await client.delete(
            collection_name=_collection_name(collection),
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="organization_id",
                            match=models.MatchValue(value=str(organization_id)),
                        ),
                    ]
                )
            ),
        )

    # =========================================================================
    # Utility
    # =========================================================================

    async def count(
        self,
        collection: str,
        organization_id: UUID | None = None,
    ) -> int:
        """Count points in a collection, optionally filtered by org."""
        client = await self._get_client()
        full_name = _collection_name(collection)

        if organization_id:
            result = await client.count(
                collection_name=full_name,
                count_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="organization_id",
                            match=models.MatchValue(value=str(organization_id)),
                        ),
                    ]
                ),
            )
        else:
            result = await client.count(collection_name=full_name)

        return result.count

    async def get_point(
        self,
        collection: str,
        point_id: UUID,
        with_vector: bool = False,
    ) -> dict[str, Any] | None:
        """Retrieve a single point by ID.

        Args:
            collection: Collection name
            point_id: Point UUID
            with_vector: Whether to include the vector in the result

        Returns:
            Dict with id, payload, and optionally vector. None if not found.
        """
        client = await self._get_client()
        try:
            results = await client.retrieve(
                collection_name=_collection_name(collection),
                ids=[str(point_id)],
                with_vectors=with_vector,
                with_payload=True,
            )
            if results:
                point = results[0]
                result: dict[str, Any] = {
                    "id": point.id,
                    "payload": point.payload or {},
                }
                if with_vector and point.vector is not None:
                    result["vector"] = point.vector
                return result
        except Exception:
            pass
        return None

    async def has_vector(
        self,
        collection: str,
        point_id: UUID,
    ) -> bool:
        """Check if a point exists in a collection."""
        client = await self._get_client()
        try:
            results = await client.retrieve(
                collection_name=_collection_name(collection),
                ids=[str(point_id)],
                with_vectors=False,
                with_payload=False,
            )
            return len(results) > 0
        except Exception:
            return False
