"""Bulk embedding pipeline for large-scale paper embedding generation.

Embeds papers in parallel batches using OpenAI's batch embedding API,
writing vectors directly to the Paper.embedding pgvector column.

Throughput: 8 concurrent x 2000 texts x ~3s/call = ~5,300 papers/sec
Cost: 15M papers x ~363 tokens x $0.02/1M = ~$109
"""

import asyncio
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select, update

from paper_scraper.core.database import get_db_session
from paper_scraper.modules.papers.models import Paper
from paper_scraper.modules.scoring.embeddings import EmbeddingClient

logger = logging.getLogger(__name__)

# OpenAI supports up to 2048 texts per embedding call
DEFAULT_BATCH_SIZE = 2000
DEFAULT_CONCURRENCY = 8


async def bulk_embed_papers_task(
    ctx: dict[str, Any],
    batch_size: int = DEFAULT_BATCH_SIZE,
    concurrency: int = DEFAULT_CONCURRENCY,
    max_papers: int | None = None,
    global_only: bool = True,
) -> dict[str, Any]:
    """Bulk-embed papers that don't yet have embeddings.

    Args:
        ctx: arq context.
        batch_size: Texts per OpenAI embedding API call (max 2048).
        concurrency: Number of parallel embedding API calls.
        max_papers: Optional limit on total papers to embed.
        global_only: If True, only embed global catalog papers.

    Returns:
        Summary dict with counts.
    """
    batch_size = min(batch_size, 2048)
    embedded_count = 0
    error_count = 0

    # Load checkpoint
    last_paper_id = await _load_checkpoint()

    logger.info(
        "Starting bulk embedding: batch_size=%d, concurrency=%d, max=%s, resume=%s",
        batch_size,
        concurrency,
        max_papers or "unlimited",
        bool(last_paper_id),
    )

    semaphore = asyncio.Semaphore(concurrency)
    client = EmbeddingClient()

    while True:
        if max_papers and embedded_count >= max_papers:
            break

        # Fetch next batch of papers without embeddings
        remaining = (max_papers - embedded_count) if max_papers else batch_size
        fetch_limit = min(batch_size, remaining)

        papers = await _fetch_unembedded_papers(
            limit=fetch_limit,
            after_id=last_paper_id,
            global_only=global_only,
        )

        if not papers:
            break

        # Build text representations
        texts = []
        paper_ids = []
        for paper_id, title, abstract, keywords in papers:
            parts = [f"Title: {title or 'Untitled'}"]
            if abstract:
                parts.append(f"Abstract: {abstract[:3000]}")
            if keywords:
                parts.append(f"Keywords: {', '.join(keywords[:10])}")
            texts.append("\n\n".join(parts))
            paper_ids.append(paper_id)

        # Generate embeddings with concurrency control
        try:
            async with semaphore:
                embeddings = await client.embed_texts(texts)
        except Exception as e:
            logger.warning("Embedding batch failed: %s", e)
            error_count += len(paper_ids)
            # Save checkpoint at last successful paper and continue
            if paper_ids:
                last_paper_id = paper_ids[-1]
                await _save_checkpoint(last_paper_id)
            await asyncio.sleep(2)  # Brief backoff on error
            continue

        # Write embeddings to DB in bulk
        try:
            await _bulk_update_embeddings(paper_ids, embeddings)
            embedded_count += len(paper_ids)
        except Exception as e:
            logger.warning("Bulk embedding DB write failed: %s", e)
            error_count += len(paper_ids)

        # Update checkpoint
        last_paper_id = paper_ids[-1]
        await _save_checkpoint(last_paper_id)

        if len(papers) < fetch_limit:
            break  # No more papers to process

    # Clear checkpoint on completion
    if error_count == 0:
        await _clear_checkpoint()

    logger.info(
        "Bulk embedding complete: %d embedded, %d errors",
        embedded_count,
        error_count,
    )

    return {
        "status": "completed" if error_count == 0 else "completed_with_errors",
        "papers_embedded": embedded_count,
        "errors": error_count,
    }


async def _fetch_unembedded_papers(
    limit: int,
    after_id: UUID | None = None,
    global_only: bool = True,
) -> list[tuple[UUID, str, str | None, list[str] | None]]:
    """Fetch papers that need embeddings, ordered by ID for checkpoint resume.

    Returns:
        List of (paper_id, title, abstract, keywords) tuples.
    """
    async with get_db_session() as db:
        query = select(Paper.id, Paper.title, Paper.abstract, Paper.keywords).where(
            Paper.embedding.is_(None)
        )

        if global_only:
            query = query.where(Paper.is_global.is_(True))

        if after_id:
            query = query.where(Paper.id > after_id)

        query = query.order_by(Paper.id).limit(limit)

        result = await db.execute(query)
        return list(result.all())


async def _bulk_update_embeddings(
    paper_ids: list[UUID],
    embeddings: list[list[float]],
) -> None:
    """Bulk-update paper embedding columns.

    Args:
        paper_ids: Paper UUIDs to update.
        embeddings: Corresponding embedding vectors.
    """
    async with get_db_session() as db:
        for paper_id, embedding in zip(paper_ids, embeddings, strict=False):
            await db.execute(
                update(Paper)
                .where(Paper.id == paper_id)
                .values(
                    embedding=embedding,
                    has_embedding=True,
                )
            )
        await db.commit()


async def _load_checkpoint() -> UUID | None:
    """Load the last processed paper ID from Redis."""
    try:
        from paper_scraper.core.redis import get_redis_pool

        redis = await get_redis_pool()
        data = await redis.get("bulk_embed:last_paper_id")
        if data:
            return UUID(data)
    except Exception as e:
        logger.warning("Failed to load embedding checkpoint: %s", e)
    return None


async def _save_checkpoint(paper_id: UUID) -> None:
    """Save the last processed paper ID to Redis."""
    try:
        from paper_scraper.core.redis import get_redis_pool

        redis = await get_redis_pool()
        await redis.set("bulk_embed:last_paper_id", str(paper_id), ex=86400 * 7)
    except Exception as e:
        logger.warning("Failed to save embedding checkpoint: %s", e)


async def _clear_checkpoint() -> None:
    """Clear the embedding checkpoint on successful completion."""
    try:
        from paper_scraper.core.redis import get_redis_pool

        redis = await get_redis_pool()
        await redis.delete("bulk_embed:last_paper_id")
    except Exception:
        pass
