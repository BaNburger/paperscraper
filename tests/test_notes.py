"""Tests for paper notes module."""

from datetime import datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.exceptions import ForbiddenError, NotFoundError
from paper_scraper.core.security import create_access_token, get_password_hash
from paper_scraper.modules.auth.models import Organization, User, UserRole
from paper_scraper.modules.papers.models import Paper
from paper_scraper.modules.papers.note_service import NoteService, extract_mentions
from paper_scraper.modules.papers.notes import PaperNote

# =============================================================================
# Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def note_service(db_session: AsyncSession) -> NoteService:
    """Create a note service instance for testing."""
    return NoteService(db_session)


@pytest_asyncio.fixture
async def second_organization(db_session: AsyncSession) -> Organization:
    """Create a second organization for tenant isolation tests."""
    organization = Organization(
        name="Second Organization",
        type="corporate",
    )
    db_session.add(organization)
    await db_session.flush()
    await db_session.refresh(organization)
    return organization


@pytest_asyncio.fixture
async def second_user(
    db_session: AsyncSession,
    test_organization: Organization,
) -> User:
    """Create a second user in the same organization."""
    user = User(
        email="second@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Second User",
        organization_id=test_organization.id,
        role=UserRole.MEMBER,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def second_user_client(
    client: AsyncClient,
    second_user: User,
) -> AsyncClient:
    """Create an authenticated client for the second user."""
    token = create_access_token(
        subject=str(second_user.id),
        extra_claims={
            "org_id": str(second_user.organization_id),
            "role": second_user.role.value,
        },
    )
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest_asyncio.fixture
async def test_paper(
    db_session: AsyncSession,
    test_organization: Organization,
) -> Paper:
    """Create a test paper."""
    paper = Paper(
        doi="10.1234/test.paper.001",
        title="Test Paper for Notes",
        abstract="This is a test abstract.",
        source="openalex",
        organization_id=test_organization.id,
        publication_date=datetime(2024, 1, 15),
    )
    db_session.add(paper)
    await db_session.flush()
    await db_session.refresh(paper)
    return paper


@pytest_asyncio.fixture
async def test_note(
    db_session: AsyncSession,
    test_paper: Paper,
    test_organization: Organization,
    test_user: User,
) -> PaperNote:
    """Create a test note on the paper."""
    note = PaperNote(
        organization_id=test_organization.id,
        paper_id=test_paper.id,
        user_id=test_user.id,
        content="This is a test note on the paper.",
        mentions=[],
    )
    db_session.add(note)
    await db_session.flush()
    await db_session.refresh(note)
    return note


@pytest_asyncio.fixture
async def multiple_notes(
    db_session: AsyncSession,
    test_paper: Paper,
    test_organization: Organization,
    test_user: User,
    second_user: User,
) -> list[PaperNote]:
    """Create multiple notes from different users."""
    notes = []
    for i, user in enumerate([test_user, second_user, test_user]):
        note = PaperNote(
            organization_id=test_organization.id,
            paper_id=test_paper.id,
            user_id=user.id,
            content=f"Note number {i + 1} from {user.full_name}",
            mentions=[],
        )
        db_session.add(note)
        notes.append(note)

    await db_session.flush()
    for note in notes:
        await db_session.refresh(note)

    return notes


# =============================================================================
# Unit Tests: extract_mentions
# =============================================================================


class TestExtractMentions:
    """Tests for the extract_mentions utility function."""

    def test_extract_single_mention(self):
        """Test extracting a single @mention."""
        content = "Hello @{550e8400-e29b-41d4-a716-446655440000} how are you?"
        mentions = extract_mentions(content)

        assert len(mentions) == 1
        assert str(mentions[0]) == "550e8400-e29b-41d4-a716-446655440000"

    def test_extract_multiple_mentions(self):
        """Test extracting multiple @mentions."""
        content = (
            "CC @{550e8400-e29b-41d4-a716-446655440001} and "
            "@{550e8400-e29b-41d4-a716-446655440002}"
        )
        mentions = extract_mentions(content)

        assert len(mentions) == 2

    def test_extract_duplicate_mentions(self):
        """Test that duplicate mentions are deduplicated."""
        content = (
            "@{550e8400-e29b-41d4-a716-446655440000} and again "
            "@{550e8400-e29b-41d4-a716-446655440000}"
        )
        mentions = extract_mentions(content)

        # Should only have 1 unique mention
        assert len(mentions) == 1

    def test_extract_no_mentions(self):
        """Test content with no @mentions."""
        content = "This is just regular text with no mentions."
        mentions = extract_mentions(content)

        assert len(mentions) == 0

    def test_extract_invalid_uuid(self):
        """Test that invalid UUIDs are ignored."""
        content = "Invalid @{not-a-uuid} format"
        mentions = extract_mentions(content)

        assert len(mentions) == 0

    def test_extract_case_insensitive(self):
        """Test that UUID matching is case insensitive."""
        content = "@{550E8400-E29B-41D4-A716-446655440000}"
        mentions = extract_mentions(content)

        assert len(mentions) == 1


# =============================================================================
# Service Tests
# =============================================================================


class TestNoteService:
    """Tests for NoteService class."""

    async def test_list_notes(
        self,
        note_service: NoteService,
        test_paper: Paper,
        test_organization: Organization,
        test_note: PaperNote,
    ):
        """Test listing notes for a paper."""
        response = await note_service.list_notes(
            paper_id=test_paper.id,
            organization_id=test_organization.id,
        )

        assert response.total == 1
        assert len(response.items) == 1
        assert response.items[0].id == test_note.id

    async def test_list_notes_multiple(
        self,
        note_service: NoteService,
        test_paper: Paper,
        test_organization: Organization,
        multiple_notes: list[PaperNote],
    ):
        """Test listing multiple notes."""
        response = await note_service.list_notes(
            paper_id=test_paper.id,
            organization_id=test_organization.id,
        )

        assert response.total == 3
        assert len(response.items) == 3

    async def test_list_notes_paper_not_found(
        self,
        note_service: NoteService,
        test_organization: Organization,
    ):
        """Test listing notes for non-existent paper raises error."""
        with pytest.raises(NotFoundError):
            await note_service.list_notes(
                paper_id=uuid4(),
                organization_id=test_organization.id,
            )

    async def test_create_note(
        self,
        note_service: NoteService,
        test_paper: Paper,
        test_organization: Organization,
        test_user: User,
    ):
        """Test creating a new note."""
        note = await note_service.create_note(
            paper_id=test_paper.id,
            user_id=test_user.id,
            organization_id=test_organization.id,
            content="This is a new note!",
        )

        assert note.id is not None
        assert note.paper_id == test_paper.id
        assert note.user_id == test_user.id
        assert note.content == "This is a new note!"

    async def test_create_note_with_mentions(
        self,
        note_service: NoteService,
        test_paper: Paper,
        test_organization: Organization,
        test_user: User,
        second_user: User,
    ):
        """Test creating a note with @mentions."""
        content = f"CC @{{{second_user.id}}} on this."

        note = await note_service.create_note(
            paper_id=test_paper.id,
            user_id=test_user.id,
            organization_id=test_organization.id,
            content=content,
        )

        assert len(note.mentions) == 1
        assert note.mentions[0] == str(second_user.id)

    async def test_create_note_paper_not_found(
        self,
        note_service: NoteService,
        test_organization: Organization,
        test_user: User,
    ):
        """Test creating note on non-existent paper raises error."""
        with pytest.raises(NotFoundError):
            await note_service.create_note(
                paper_id=uuid4(),
                user_id=test_user.id,
                organization_id=test_organization.id,
                content="This should fail.",
            )

    async def test_get_note(
        self,
        note_service: NoteService,
        test_paper: Paper,
        test_note: PaperNote,
        test_organization: Organization,
    ):
        """Test getting a specific note."""
        note = await note_service.get_note(
            paper_id=test_paper.id,
            note_id=test_note.id,
            organization_id=test_organization.id,
        )

        assert note.id == test_note.id
        assert note.content == test_note.content

    async def test_get_note_not_found(
        self,
        note_service: NoteService,
        test_paper: Paper,
        test_organization: Organization,
    ):
        """Test getting non-existent note raises error."""
        with pytest.raises(NotFoundError):
            await note_service.get_note(
                paper_id=test_paper.id,
                note_id=uuid4(),
                organization_id=test_organization.id,
            )

    async def test_update_note(
        self,
        note_service: NoteService,
        test_paper: Paper,
        test_note: PaperNote,
        test_organization: Organization,
        test_user: User,
    ):
        """Test updating a note by its author."""
        updated_note = await note_service.update_note(
            paper_id=test_paper.id,
            note_id=test_note.id,
            user_id=test_user.id,
            organization_id=test_organization.id,
            content="Updated content!",
        )

        assert updated_note.content == "Updated content!"

    async def test_update_note_not_owner(
        self,
        note_service: NoteService,
        test_paper: Paper,
        test_note: PaperNote,
        test_organization: Organization,
        second_user: User,
    ):
        """Test that non-owner cannot update a note."""
        with pytest.raises(ForbiddenError):
            await note_service.update_note(
                paper_id=test_paper.id,
                note_id=test_note.id,
                user_id=second_user.id,  # Different user
                organization_id=test_organization.id,
                content="Attempted unauthorized update",
            )

    async def test_delete_note(
        self,
        note_service: NoteService,
        test_paper: Paper,
        test_note: PaperNote,
        test_organization: Organization,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Test deleting a note by its author."""
        result = await note_service.delete_note(
            paper_id=test_paper.id,
            note_id=test_note.id,
            user_id=test_user.id,
            organization_id=test_organization.id,
        )

        assert result is True

        # Verify deletion
        check_result = await db_session.execute(
            select(PaperNote).where(PaperNote.id == test_note.id)
        )
        assert check_result.scalar_one_or_none() is None

    async def test_delete_note_not_owner(
        self,
        note_service: NoteService,
        test_paper: Paper,
        test_note: PaperNote,
        test_organization: Organization,
        second_user: User,
    ):
        """Test that non-owner cannot delete a note."""
        with pytest.raises(ForbiddenError):
            await note_service.delete_note(
                paper_id=test_paper.id,
                note_id=test_note.id,
                user_id=second_user.id,  # Different user
                organization_id=test_organization.id,
            )

    async def test_tenant_isolation(
        self,
        note_service: NoteService,
        test_paper: Paper,
        second_organization: Organization,
    ):
        """Test that notes operations respect tenant boundaries."""
        # Paper belongs to test_organization, not second_organization
        with pytest.raises(NotFoundError):
            await note_service.list_notes(
                paper_id=test_paper.id,
                organization_id=second_organization.id,
            )


# =============================================================================
# API Router Tests
# =============================================================================


class TestNotesRouter:
    """Tests for notes API endpoints."""

    async def test_list_notes(
        self,
        authenticated_client: AsyncClient,
        test_paper: Paper,
        test_note: PaperNote,
    ):
        """Test listing notes via API."""
        response = await authenticated_client.get(f"/api/v1/papers/{test_paper.id}/notes")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 1

    async def test_create_note(
        self,
        authenticated_client: AsyncClient,
        test_paper: Paper,
    ):
        """Test creating a note via API."""
        response = await authenticated_client.post(
            f"/api/v1/papers/{test_paper.id}/notes",
            json={"content": "API created note"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "API created note"
        assert data["paper_id"] == str(test_paper.id)

    async def test_create_note_empty_content(
        self,
        authenticated_client: AsyncClient,
        test_paper: Paper,
    ):
        """Test that empty content is rejected."""
        response = await authenticated_client.post(
            f"/api/v1/papers/{test_paper.id}/notes",
            json={"content": ""},
        )

        assert response.status_code == 422  # Validation error

    async def test_get_note(
        self,
        authenticated_client: AsyncClient,
        test_paper: Paper,
        test_note: PaperNote,
    ):
        """Test getting a specific note via API."""
        response = await authenticated_client.get(
            f"/api/v1/papers/{test_paper.id}/notes/{test_note.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_note.id)

    async def test_update_note(
        self,
        authenticated_client: AsyncClient,
        test_paper: Paper,
        test_note: PaperNote,
    ):
        """Test updating a note via API."""
        response = await authenticated_client.put(
            f"/api/v1/papers/{test_paper.id}/notes/{test_note.id}",
            json={"content": "Updated via API"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated via API"

    async def test_update_note_not_owner(
        self,
        second_user_client: AsyncClient,
        test_paper: Paper,
        test_note: PaperNote,
    ):
        """Test that non-owner cannot update note via API."""
        response = await second_user_client.put(
            f"/api/v1/papers/{test_paper.id}/notes/{test_note.id}",
            json={"content": "Unauthorized update attempt"},
        )

        assert response.status_code == 403

    async def test_delete_note(
        self,
        authenticated_client: AsyncClient,
        test_paper: Paper,
        test_note: PaperNote,
    ):
        """Test deleting a note via API."""
        response = await authenticated_client.delete(
            f"/api/v1/papers/{test_paper.id}/notes/{test_note.id}"
        )

        assert response.status_code == 204

    async def test_delete_note_not_owner(
        self,
        second_user_client: AsyncClient,
        test_paper: Paper,
        test_note: PaperNote,
    ):
        """Test that non-owner cannot delete note via API."""
        response = await second_user_client.delete(
            f"/api/v1/papers/{test_paper.id}/notes/{test_note.id}"
        )

        assert response.status_code == 403

    async def test_unauthorized_access(
        self,
        client: AsyncClient,
        test_paper: Paper,
    ):
        """Test that unauthenticated requests are rejected."""
        response = await client.get(f"/api/v1/papers/{test_paper.id}/notes")

        assert response.status_code == 401

    async def test_note_response_structure(
        self,
        authenticated_client: AsyncClient,
        test_paper: Paper,
        test_note: PaperNote,
    ):
        """Test that note response has correct structure."""
        response = await authenticated_client.get(
            f"/api/v1/papers/{test_paper.id}/notes/{test_note.id}"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all expected fields are present
        assert "id" in data
        assert "paper_id" in data
        assert "user_id" in data
        assert "content" in data
        assert "mentions" in data
        assert "created_at" in data
        assert "updated_at" in data
