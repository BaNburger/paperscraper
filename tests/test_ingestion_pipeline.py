"""Tests for ingestion pipeline orchestration."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.auth.models import User
from paper_scraper.modules.ingestion.interfaces import ConnectorBatch
from paper_scraper.modules.ingestion.models import (
    IngestCheckpoint,
    IngestRun,
    IngestRunStatus,
    SourceRecord,
)
from paper_scraper.modules.ingestion.pipeline import IngestionPipeline
from paper_scraper.modules.ingestion.service import IngestionService
from paper_scraper.modules.papers.models import Paper


class _StaticConnector:
    """Simple connector test double returning pre-canned batches."""

    def __init__(self, batches: list[ConnectorBatch]) -> None:
        self._batches = batches
        self._calls = 0

    async def fetch(
        self,
        cursor: dict | None,
        filters: dict | None,
        limit: int,
    ) -> ConnectorBatch:
        index = min(self._calls, len(self._batches) - 1)
        self._calls += 1
        return self._batches[index]


def _openalex_record(
    source_id: str,
    title: str,
    doi: str | None = None,
    publication_date: str = "2024-01-01",
) -> dict:
    return {
        "source": "openalex",
        "source_id": source_id,
        "doi": doi,
        "title": title,
        "abstract": f"Abstract for {title}",
        "publication_date": publication_date,
        "journal": "Test Journal",
        "keywords": ["ai", "ml"],
        "authors": [
            {
                "name": "Ada Lovelace",
                "orcid": "0000-0000-0000-0001",
                "openalex_id": "A123",
                "affiliations": ["Oxford"],
            }
        ],
        "raw_metadata": {"source_id": source_id},
    }


def _source_record(
    source: str,
    source_id: str,
    title: str,
    doi: str | None = None,
    publication_date: str = "2024-01-01",
) -> dict:
    return {
        "source": source,
        "source_id": source_id,
        "doi": doi,
        "title": title,
        "abstract": f"Abstract for {title}",
        "publication_date": publication_date,
        "journal": "Test Journal",
        "keywords": ["ai", "ml"],
        "authors": [{"name": "Ada Lovelace", "affiliations": ["Oxford"]}],
        "raw_metadata": {"source_id": source_id},
    }


async def _count_rows(db_session: AsyncSession, model: type) -> int:
    result = await db_session.execute(select(func.count()).select_from(model))
    return int(result.scalar() or 0)


@pytest.mark.asyncio
async def test_pipeline_run_creates_run_checkpoint_and_papers(
    db_session: AsyncSession,
    test_user: User,
) -> None:
    pipeline = IngestionPipeline(db_session)
    connector = _StaticConnector(
        [
            ConnectorBatch(
                records=[
                    _openalex_record("W-1", "Paper One", "10.1000/one"),
                    _openalex_record("W-2", "Paper Two", "10.1000/two"),
                ],
                cursor_before={"cursor": "*"},
                cursor_after={"cursor": "next-1"},
                has_more=True,
            )
        ]
    )

    run = await pipeline.run(
        source="openalex",
        organization_id=test_user.organization_id,
        initiated_by_id=test_user.id,
        filters={"query": "llm", "filters": {}},
        limit=50,
        connector=connector,
    )

    assert run.status.value == "completed"
    assert run.stats_json["fetched_records"] == 2
    assert run.stats_json["papers_created"] == 2
    assert run.stats_json["source_records_inserted"] == 2
    assert await _count_rows(db_session, Paper) == 2
    assert await _count_rows(db_session, SourceRecord) == 2
    assert await _count_rows(db_session, IngestRun) == 1

    checkpoint = await db_session.get(
        IngestCheckpoint,
        {
            "source": "openalex",
            "scope_key": pipeline._build_scope_key(  # noqa: SLF001
                test_user.organization_id,
                {"query": "llm", "filters": {}},
            ),
        },
    )
    assert checkpoint is not None
    assert checkpoint.cursor_json == {"cursor": "next-1"}


@pytest.mark.asyncio
async def test_pipeline_is_idempotent_on_replay(
    db_session: AsyncSession,
    test_user: User,
) -> None:
    pipeline = IngestionPipeline(db_session)
    replay_batch = ConnectorBatch(
        records=[
            _openalex_record("W-1", "Paper One", "10.1000/one"),
            _openalex_record("W-2", "Paper Two", "10.1000/two"),
        ],
        cursor_before={"cursor": "*"},
        cursor_after={"cursor": "next-1"},
        has_more=True,
    )
    connector = _StaticConnector([replay_batch, replay_batch])

    first_run = await pipeline.run(
        source="openalex",
        organization_id=test_user.organization_id,
        initiated_by_id=test_user.id,
        filters={"query": "llm", "filters": {}},
        limit=50,
        connector=connector,
    )
    second_run = await pipeline.run(
        source="openalex",
        organization_id=test_user.organization_id,
        initiated_by_id=test_user.id,
        filters={"query": "llm", "filters": {}},
        limit=50,
        connector=connector,
    )

    assert first_run.stats_json["papers_created"] == 2
    assert second_run.stats_json["papers_created"] == 0
    assert second_run.stats_json["source_records_inserted"] == 0
    assert second_run.stats_json["source_records_duplicates"] == 2
    assert await _count_rows(db_session, Paper) == 2
    assert await _count_rows(db_session, SourceRecord) == 2
    assert await _count_rows(db_session, IngestRun) == 2


@pytest.mark.asyncio
async def test_pipeline_title_year_fallback_prevents_duplicate(
    db_session: AsyncSession,
    test_user: User,
) -> None:
    pipeline = IngestionPipeline(db_session)

    first_batch = ConnectorBatch(
        records=[
            _openalex_record(
                "W-1",
                "A Unified Transferability Model",
                doi=None,
                publication_date="2024-05-10",
            )
        ],
        cursor_before={"cursor": "*"},
        cursor_after={"cursor": "next-1"},
        has_more=True,
    )
    second_batch = ConnectorBatch(
        records=[
            {
                **_openalex_record(
                    "W-2",
                    "A Unified Transferability Model",
                    doi=None,
                    publication_date="2024-05-10",
                ),
                "abstract": "Updated source payload",
            }
        ],
        cursor_before={"cursor": "next-1"},
        cursor_after={"cursor": "next-2"},
        has_more=False,
    )
    connector = _StaticConnector([first_batch, second_batch])

    await pipeline.run(
        source="openalex",
        organization_id=test_user.organization_id,
        initiated_by_id=test_user.id,
        filters={"query": "transfer", "filters": {}},
        limit=10,
        connector=connector,
    )
    second_run = await pipeline.run(
        source="openalex",
        organization_id=test_user.organization_id,
        initiated_by_id=test_user.id,
        filters={"query": "transfer", "filters": {}},
        limit=10,
        connector=connector,
    )

    assert await _count_rows(db_session, Paper) == 1
    assert await _count_rows(db_session, SourceRecord) == 2
    assert second_run.stats_json["papers_created"] == 0
    assert second_run.stats_json["papers_matched"] == 1
    dedupe_report = second_run.stats_json["dedupe_report"]
    assert dedupe_report.get("title_year") == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("source", ["openalex", "pubmed", "arxiv", "semantic_scholar"])
async def test_pipeline_executes_existing_queued_run_for_supported_sources(
    source: str,
    db_session: AsyncSession,
    test_user: User,
) -> None:
    pipeline = IngestionPipeline(db_session)
    ingestion_service = IngestionService(db_session)

    queued_run = await ingestion_service.create_run(
        source=source,
        organization_id=test_user.organization_id,
        initiated_by_id=test_user.id,
        status=IngestRunStatus.QUEUED,
    )

    connector = _StaticConnector(
        [
            ConnectorBatch(
                records=[_source_record(source, f"{source}-1", f"{source} paper 1")],
                cursor_before={"cursor": "*"},
                cursor_after={"cursor": "next"},
                has_more=False,
            )
        ]
    )

    run = await pipeline.run(
        source=source,
        organization_id=test_user.organization_id,
        initiated_by_id=test_user.id,
        filters={"query": "transfer"},
        limit=50,
        connector=connector,
        existing_run_id=queued_run.id,
    )

    assert run.id == queued_run.id
    assert run.status == IngestRunStatus.COMPLETED
    assert run.stats_json["fetched_records"] == 1
    assert run.stats_json["papers_created"] == 1


@pytest.mark.asyncio
async def test_pipeline_marks_existing_run_failed_for_unsupported_source(
    db_session: AsyncSession,
    test_user: User,
) -> None:
    pipeline = IngestionPipeline(db_session)
    ingestion_service = IngestionService(db_session)

    queued_run = await ingestion_service.create_run(
        source="unsupported_source",
        organization_id=test_user.organization_id,
        initiated_by_id=test_user.id,
        status=IngestRunStatus.QUEUED,
    )

    with pytest.raises(ValueError, match="Unsupported source connector"):
        await pipeline.run(
            source="unsupported_source",
            organization_id=test_user.organization_id,
            filters={"query": "test"},
            existing_run_id=queued_run.id,
        )

    refreshed = await ingestion_service.get_run(
        run_id=queued_run.id,
        organization_id=test_user.organization_id,
    )
    assert refreshed.status == IngestRunStatus.FAILED
    assert refreshed.error_message
