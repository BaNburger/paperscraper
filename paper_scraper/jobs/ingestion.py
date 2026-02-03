"""Background tasks for paper ingestion."""

from typing import Any
from uuid import UUID

from paper_scraper.core.database import get_db_session
from paper_scraper.modules.papers.service import PaperService


async def ingest_openalex_task(
    ctx: dict[str, Any],
    organization_id: str,
    query: str,
    max_results: int = 100,
    filters: dict | None = None,
) -> dict[str, Any]:
    """Ingest papers from OpenAlex.

    Args:
        ctx: arq context.
        organization_id: UUID string of organization.
        query: OpenAlex search query.
        max_results: Maximum papers to import.
        filters: Optional OpenAlex filters.

    Returns:
        Ingestion result dict.
    """
    async with get_db_session() as db:
        service = PaperService(db)
        result = await service.ingest_from_openalex(
            query=query,
            organization_id=UUID(organization_id),
            max_results=max_results,
            filters=filters,
        )
        return result.model_dump()
