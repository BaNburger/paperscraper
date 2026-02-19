"""Tests for async ingestion endpoints, worker path, and ingestion run RBAC."""

from __future__ import annotations

from contextlib import asynccontextmanager
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.security import create_access_token, get_password_hash
from paper_scraper.jobs.ingestion import ingest_source_task
from paper_scraper.modules.auth.models import Organization, User, UserRole
from paper_scraper.modules.ingestion.interfaces import ConnectorBatch
from paper_scraper.modules.ingestion.models import IngestRun, IngestRunStatus
from paper_scraper.modules.ingestion.service import IngestionService


class _FakeJob:
    def __init__(self, job_id: str):
        self.job_id = job_id


class _StaticConnector:
    async def fetch(
        self,
        cursor: dict | None,
        filters: dict | None,
        limit: int,
    ) -> ConnectorBatch:
        return ConnectorBatch(
            records=[
                {
                    "source": "openalex",
                    "source_id": "W-123",
                    "title": "Queued run execution test",
                    "abstract": "Test abstract",
                    "publication_date": "2024-01-01",
                    "keywords": ["ai"],
                    "authors": [{"name": "Ada Lovelace"}],
                    "raw_metadata": {"id": "W-123"},
                }
            ],
            cursor_before={"cursor": "*"},
            cursor_after={"cursor": "next"},
            has_more=False,
        )


def _auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(
        subject=str(user.id),
        extra_claims={"org_id": str(user.organization_id), "role": user.role.value},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def member_user(
    db_session: AsyncSession,
    test_organization: Organization,
) -> User:
    user = User(
        email="member-ingestion@example.com",
        hashed_password=get_password_hash("memberpassword123"),
        full_name="Member Ingestion",
        organization_id=test_organization.id,
        role=UserRole.MEMBER,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def other_org_member(db_session: AsyncSession) -> User:
    org = Organization(name="Other Org", type="university")
    db_session.add(org)
    await db_session.flush()
    await db_session.refresh(org)

    user = User(
        email="other-org-member@example.com",
        hashed_password=get_password_hash("memberpassword123"),
        full_name="Other Org Member",
        organization_id=org.id,
        role=UserRole.MEMBER,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "payload", "source"),
    [
        (
            "/api/v1/ingestion/sources/openalex/runs",
            {"query": "ml", "max_results": 5, "filters": {}},
            "openalex",
        ),
        (
            "/api/v1/ingestion/sources/pubmed/runs",
            {"query": "oncology", "max_results": 5},
            "pubmed",
        ),
        (
            "/api/v1/ingestion/sources/arxiv/runs",
            {"query": "transformer", "max_results": 5, "category": "cs.AI"},
            "arxiv",
        ),
        (
            "/api/v1/ingestion/sources/semantic-scholar/runs",
            {"query": "graph neural network", "max_results": 5},
            "semantic_scholar",
        ),
    ],
)
async def test_async_ingest_endpoints_return_job_and_run_ids(
    path: str,
    payload: dict,
    source: str,
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_enqueue_job(
        job_name: str, *args, job_id: str | None = None, **kwargs
    ) -> _FakeJob:
        assert job_name == "ingest_source_task"
        assert job_id is not None
        return _FakeJob(job_id)

    monkeypatch.setattr("paper_scraper.jobs.worker.enqueue_job", fake_enqueue_job)

    response = await client.post(path, json=payload, headers=auth_headers)
    assert response.status_code == 202
    data = response.json()

    assert data["job_id"]
    assert data["ingest_run_id"]
    assert data["source"] == source
    assert data["status"] == "queued"

    run_id = UUID(data["ingest_run_id"])
    run = await db_session.get(IngestRun, run_id)
    assert run is not None
    assert run.source == source
    assert run.status == IngestRunStatus.QUEUED


@pytest.mark.asyncio
async def test_async_ingest_enqueue_failure_marks_run_failed(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
    test_user: User,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def failing_enqueue_job(*args, **kwargs):
        raise RuntimeError("redis unavailable")

    monkeypatch.setattr("paper_scraper.jobs.worker.enqueue_job", failing_enqueue_job)

    response = await client.post(
        "/api/v1/ingestion/sources/openalex/runs",
        json={"query": "ml", "max_results": 5, "filters": {}},
        headers=auth_headers,
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to enqueue ingestion job"

    result = await db_session.execute(
        select(IngestRun)
        .where(
            IngestRun.organization_id == test_user.organization_id,
            IngestRun.source == "openalex",
        )
        .order_by(IngestRun.created_at.desc())
        .limit(1)
    )
    run = result.scalar_one_or_none()
    assert run is not None
    assert run.status == IngestRunStatus.FAILED
    assert run.error_message is not None
    assert "redis unavailable" in run.error_message


@pytest.mark.asyncio
async def test_ingestion_runs_rbac_member_can_read_org_runs(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    member_user: User,
) -> None:
    ingestion_service = IngestionService(db_session)
    run = await ingestion_service.create_run(
        source="openalex",
        organization_id=test_user.organization_id,
        initiated_by_id=test_user.id,
        status=IngestRunStatus.QUEUED,
    )
    await db_session.flush()

    headers = _auth_headers(member_user)

    list_response = await client.get("/api/v1/ingestion/runs", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] >= 1

    detail_response = await client.get(f"/api/v1/ingestion/runs/{run.id}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == str(run.id)


@pytest.mark.asyncio
async def test_ingestion_runs_cross_org_access_is_denied(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    other_org_member: User,
) -> None:
    ingestion_service = IngestionService(db_session)
    run = await ingestion_service.create_run(
        source="openalex",
        organization_id=test_user.organization_id,
        initiated_by_id=test_user.id,
        status=IngestRunStatus.QUEUED,
    )
    await db_session.flush()

    headers = _auth_headers(other_org_member)
    response = await client.get(f"/api/v1/ingestion/runs/{run.id}", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ingest_source_task_executes_existing_queued_run(
    db_session: AsyncSession,
    test_user: User,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ingestion_service = IngestionService(db_session)
    run = await ingestion_service.create_run(
        source="openalex",
        organization_id=test_user.organization_id,
        initiated_by_id=test_user.id,
        status=IngestRunStatus.QUEUED,
    )
    await db_session.flush()

    @asynccontextmanager
    async def fake_db_session():
        yield db_session

    monkeypatch.setattr("paper_scraper.jobs.ingestion.get_db_session", fake_db_session)
    monkeypatch.setattr(
        "paper_scraper.modules.ingestion.pipeline.get_source_connector",
        lambda source: _StaticConnector(),
    )

    result = await ingest_source_task(
        {},
        {
            "ingest_run_id": str(run.id),
            "source": "openalex",
            "organization_id": str(test_user.organization_id),
            "initiated_by_id": str(test_user.id),
            "query": "llm",
            "max_results": 5,
            "filters": {"filters": {}},
        },
    )

    assert result["run_id"] == str(run.id)
    assert result["status"] in {"completed", "completed_with_errors"}

    refreshed = await ingestion_service.get_run(
        run_id=run.id,
        organization_id=test_user.organization_id,
    )
    assert refreshed.status in {IngestRunStatus.COMPLETED, IngestRunStatus.COMPLETED_WITH_ERRORS}
