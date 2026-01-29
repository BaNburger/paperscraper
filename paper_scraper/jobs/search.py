"""Background tasks for search operations."""

from typing import Any
from uuid import UUID

from paper_scraper.core.database import get_db_session
from paper_scraper.modules.search.service import SearchService


async def backfill_embeddings_task(
    ctx: dict[str, Any],
    organization_id: str,
    batch_size: int = 100,
    max_papers: int | None = None,
) -> dict[str, Any]:
    """
    arq task: Backfill embeddings for papers that don't have them.

    This task generates embeddings for all papers in an organization
    that don't currently have vector embeddings.

    Args:
        ctx: arq context
        organization_id: UUID string of organization
        batch_size: Papers to process per batch (for commits)
        max_papers: Maximum papers to process (None = all)

    Returns:
        Result dict with backfill statistics
    """
    org_uuid = UUID(organization_id)

    async with get_db_session() as db:
        service = SearchService(db)
        result = await service.backfill_embeddings(
            organization_id=org_uuid,
            batch_size=batch_size,
            max_papers=max_papers,
        )

    return {
        "status": "completed",
        "papers_processed": result.papers_processed,
        "papers_succeeded": result.papers_succeeded,
        "papers_failed": result.papers_failed,
        "errors": result.errors,
    }
