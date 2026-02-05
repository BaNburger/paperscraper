"""Pytest configuration and fixtures for Paper Scraper tests."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from paper_scraper.api.main import app
from paper_scraper.core.database import Base, get_db
from paper_scraper.core.security import create_access_token
from paper_scraper.modules.auth.models import Organization, User, UserRole
from paper_scraper.modules.papers.models import Author, Paper, PaperAuthor  # noqa: F401
from paper_scraper.modules.projects.models import (  # noqa: F401
    PaperProjectStatus,
    PaperStageHistory,
    Project,
)
from paper_scraper.modules.scoring.models import PaperScore, ScoringJob  # noqa: F401
from paper_scraper.modules.groups.models import ResearcherGroup, GroupMember  # noqa: F401
from paper_scraper.modules.transfer.models import (  # noqa: F401
    TransferConversation, ConversationMessage, ConversationResource,
    StageChange, MessageTemplate,
)
from paper_scraper.modules.submissions.models import (  # noqa: F401
    ResearchSubmission, SubmissionAttachment, SubmissionScore,
)
from paper_scraper.modules.badges.models import Badge, UserBadge  # noqa: F401
from paper_scraper.modules.knowledge.models import KnowledgeSource  # noqa: F401
from paper_scraper.core.security import get_password_hash

# Register SQLite type compiler for PostgreSQL JSONB so tests can run
# against in-memory SQLite instead of requiring a PostgreSQL instance.
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler

if not hasattr(SQLiteTypeCompiler, "visit_JSONB"):
    SQLiteTypeCompiler.visit_JSONB = SQLiteTypeCompiler.visit_JSON


# Test database URL - uses in-memory SQLite for fast tests
# Note: Some PostgreSQL-specific features won't work in tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

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
