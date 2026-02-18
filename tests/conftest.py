"""Pytest configuration and fixtures for Paper Scraper tests.

Uses testcontainers-postgres for real PostgreSQL testing (with pgvector)
and fakeredis for in-memory Redis mocking.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator

import fakeredis.aioredis
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from paper_scraper.api.main import app

# ---------------------------------------------------------------------------
# fakeredis: Replace real Redis with an in-memory implementation
# ---------------------------------------------------------------------------
# Patch the TokenBlacklist (and any other RedisService subclass) to use
# fakeredis instead of connecting to a real Redis instance.
from paper_scraper.core import token_blacklist as tb_module
from paper_scraper.core.database import Base, get_db
from paper_scraper.core.security import create_access_token, get_password_hash
from paper_scraper.modules.alerts.models import Alert, AlertResult  # noqa: F401
from paper_scraper.modules.audit.models import AuditLog  # noqa: F401
from paper_scraper.modules.auth.models import Organization, User, UserRole
from paper_scraper.modules.badges.models import Badge, UserBadge  # noqa: F401
from paper_scraper.modules.compliance.models import RetentionLog, RetentionPolicy  # noqa: F401
from paper_scraper.modules.developer.models import APIKey, RepositorySource, Webhook  # noqa: F401
from paper_scraper.modules.discovery.models import DiscoveryRun  # noqa: F401
from paper_scraper.modules.groups.models import GroupMember, ResearcherGroup  # noqa: F401
from paper_scraper.modules.ingestion.models import (  # noqa: F401
    IngestCheckpoint,
    IngestRun,
    SourceRecord,
)
from paper_scraper.modules.integrations.models import (  # noqa: F401
    IntegrationConnector,
    ZoteroConnection,
    ZoteroItemLink,
    ZoteroSyncRun,
)
from paper_scraper.modules.knowledge.models import KnowledgeSource  # noqa: F401
from paper_scraper.modules.library.models import (  # noqa: F401
    LibraryCollection,
    LibraryCollectionItem,
    PaperHighlight,
    PaperTag,
    PaperTextChunk,
)
from paper_scraper.modules.model_settings.models import ModelConfiguration, ModelUsage  # noqa: F401
from paper_scraper.modules.notifications.models import Notification  # noqa: F401
from paper_scraper.modules.papers.context_models import PaperContextSnapshot  # noqa: F401
from paper_scraper.modules.papers.models import Author, Paper, PaperAuthor  # noqa: F401
from paper_scraper.modules.papers.notes import PaperNote  # noqa: F401
from paper_scraper.modules.projects.models import (  # noqa: F401
    Project,
    ProjectCluster,
    ProjectClusterPaper,
    ProjectPaper,
)
from paper_scraper.modules.reports.models import ScheduledReport  # noqa: F401
from paper_scraper.modules.saved_searches.models import SavedSearch  # noqa: F401
from paper_scraper.modules.scoring.models import (  # noqa: F401
    GlobalScoreCache,
    PaperScore,
    ScoringJob,
)
from paper_scraper.modules.search.models import SearchActivity  # noqa: F401
from paper_scraper.modules.submissions.models import (  # noqa: F401
    ResearchSubmission,
    SubmissionAttachment,
    SubmissionScore,
)
from paper_scraper.modules.transfer.models import (  # noqa: F401
    ConversationMessage,
    ConversationResource,
    MessageTemplate,
    StageChange,
    TransferConversation,
)
from paper_scraper.modules.trends.models import TrendPaper, TrendSnapshot, TrendTopic  # noqa: F401

_fake_redis: fakeredis.aioredis.FakeRedis | None = None


def _get_fake_redis() -> fakeredis.aioredis.FakeRedis:
    """Return a module-level fakeredis instance (lazy-initialized).

    Recreates the instance if it is bound to a closed or different event loop.
    """
    global _fake_redis
    if _fake_redis is None:
        _fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    return _fake_redis


def _reset_fake_redis() -> None:
    """Force a new FakeRedis instance on the next call to _get_fake_redis."""
    global _fake_redis
    _fake_redis = None


# Override the _get_redis method on the singleton so it returns fakeredis
# instead of connecting to a real Redis server.
async def _patched_get_redis() -> fakeredis.aioredis.FakeRedis:
    return _get_fake_redis()


tb_module.token_blacklist._get_redis = _patched_get_redis  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# testcontainers: PostgreSQL with pgvector
# ---------------------------------------------------------------------------
# Use pgvector/pgvector:pg16 image to match production and have the vector
# extension available.
POSTGRES_IMAGE = "pgvector/pgvector:pg16"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """Start a PostgreSQL container for the test session.

    Uses the pgvector/pgvector:pg16 image so that CREATE EXTENSION vector
    works the same as in production.
    """
    container = PostgresContainer(
        image=POSTGRES_IMAGE,
        username="test",
        password="test",
        dbname="test_paperscraper",
        driver="asyncpg",
    )
    with container:
        yield container


@pytest.fixture(scope="session")
def database_url(postgres_container: PostgresContainer) -> str:
    """Build the async database URL from the running container."""
    return postgres_container.get_connection_url()


@pytest_asyncio.fixture
async def db_engine(database_url: str):
    """Create a test database engine backed by testcontainers PostgreSQL."""
    engine = create_async_engine(
        database_url,
        echo=False,
    )

    # Enable pgvector extension and create all tables
    async with engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after the test to ensure isolation between test functions
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP test client."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_organization(db_session: AsyncSession) -> Organization:
    """Create a test organization."""
    organization = Organization(
        name="Test Organization",
        type="university",
    )
    db_session.add(organization)
    await db_session.flush()
    await db_session.refresh(organization)
    return organization


@pytest_asyncio.fixture
async def test_user(
    db_session: AsyncSession,
    test_organization: Organization,
) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        organization_id=test_organization.id,
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """Create authentication headers for test requests."""
    token = create_access_token(
        subject=str(test_user.id),
        extra_claims={
            "org_id": str(test_user.organization_id),
            "role": test_user.role.value,
        },
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def authenticated_client(
    client: AsyncClient,
    test_user: User,
) -> AsyncGenerator[AsyncClient, None]:
    """Create an authenticated test client."""
    token = create_access_token(
        subject=str(test_user.id),
        extra_claims={
            "org_id": str(test_user.organization_id),
            "role": test_user.role.value,
        },
    )
    client.headers["Authorization"] = f"Bearer {token}"
    yield client


@pytest_asyncio.fixture(autouse=True)
async def _clear_fake_redis():
    """Clear fakeredis state between tests for isolation.

    Creates a fresh FakeRedis per test to avoid event-loop binding issues
    when pytest-asyncio uses function-scoped loops.
    """
    _reset_fake_redis()
    yield
    try:
        redis = _get_fake_redis()
        await redis.flushall()
    except RuntimeError:
        # FakeRedis Queue bound to a different event loop – just discard it
        pass
    finally:
        _reset_fake_redis()
