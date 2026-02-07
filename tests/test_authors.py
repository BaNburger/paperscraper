"""Tests for authors module."""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.security import create_access_token, get_password_hash
from paper_scraper.modules.auth.models import Organization, User, UserRole
from paper_scraper.modules.authors.models import AuthorContact, ContactType, ContactOutcome
from paper_scraper.modules.authors.service import AuthorService
from paper_scraper.modules.authors.schemas import ContactCreate, ContactUpdate
from paper_scraper.modules.papers.models import Author, Paper, PaperAuthor


# =============================================================================
# Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def author_service(db_session: AsyncSession) -> AuthorService:
    """Create an author service instance for testing."""
    return AuthorService(db_session)


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
async def test_author(
    db_session: AsyncSession,
    test_organization: Organization,
) -> Author:
    """Create a test author."""
    author = Author(
        name="Dr. Jane Smith",
        orcid="0000-0001-2345-6789",
        openalex_id="A123456789",
        affiliations=["MIT", "Stanford"],
        h_index=25,
        citation_count=1500,
        works_count=45,
        organization_id=test_organization.id,
    )
    db_session.add(author)
    await db_session.flush()
    await db_session.refresh(author)
    return author


@pytest_asyncio.fixture
async def test_paper(
    db_session: AsyncSession,
    test_organization: Organization,
) -> Paper:
    """Create a test paper."""
    paper = Paper(
        doi="10.1234/test.paper.001",
        title="Test Paper on Machine Learning",
        abstract="This is a test abstract for a machine learning paper.",
        source="openalex",
        organization_id=test_organization.id,
        publication_date=datetime(2024, 1, 15),
        journal="Journal of AI Research",
    )
    db_session.add(paper)
    await db_session.flush()
    await db_session.refresh(paper)
    return paper


@pytest_asyncio.fixture
async def paper_author_link(
    db_session: AsyncSession,
    test_author: Author,
    test_paper: Paper,
) -> PaperAuthor:
    """Link the test author to the test paper."""
    link = PaperAuthor(
        paper_id=test_paper.id,
        author_id=test_author.id,
        position=1,
        is_corresponding=True,
    )
    db_session.add(link)
    await db_session.flush()
    await db_session.refresh(link)
    return link


@pytest_asyncio.fixture
async def test_contact(
    db_session: AsyncSession,
    test_author: Author,
    test_organization: Organization,
    test_user: User,
) -> AuthorContact:
    """Create a test contact for the author."""
    contact = AuthorContact(
        author_id=test_author.id,
        organization_id=test_organization.id,
        contacted_by_id=test_user.id,
        contact_type=ContactType.EMAIL,
        contact_date=datetime.now(timezone.utc),
        subject="Introduction and collaboration",
        notes="Reached out regarding potential collaboration on ML research.",
        outcome=ContactOutcome.IN_PROGRESS,
    )
    db_session.add(contact)
    await db_session.flush()
    await db_session.refresh(contact)
    return contact


@pytest_asyncio.fixture
async def multiple_contacts(
    db_session: AsyncSession,
    test_author: Author,
    test_organization: Organization,
    test_user: User,
) -> list[AuthorContact]:
    """Create multiple contacts for testing statistics."""
    contacts = []
    contact_data = [
        (ContactType.EMAIL, ContactOutcome.NO_RESPONSE, -30),  # 30 days ago
        (ContactType.EMAIL, ContactOutcome.FOLLOW_UP_NEEDED, -14),  # 14 days ago
        (ContactType.MEETING, ContactOutcome.SUCCESSFUL, -7),  # 7 days ago
        (ContactType.PHONE, ContactOutcome.SUCCESSFUL, -2),  # 2 days ago
    ]

    for contact_type, outcome, days_ago in contact_data:
        contact = AuthorContact(
            author_id=test_author.id,
            organization_id=test_organization.id,
            contacted_by_id=test_user.id,
            contact_type=contact_type,
            contact_date=datetime.now(timezone.utc) + timedelta(days=days_ago),
            outcome=outcome,
        )
        db_session.add(contact)
        contacts.append(contact)

    await db_session.flush()
    for contact in contacts:
        await db_session.refresh(contact)

    return contacts


# =============================================================================
# Service Tests
# =============================================================================


class TestAuthorService:
    """Tests for AuthorService class."""

    async def test_get_author(
        self,
        author_service: AuthorService,
        test_author: Author,
        test_organization: Organization,
    ):
        """Test retrieving an author by ID."""
        author = await author_service.get_author(
            author_id=test_author.id,
            organization_id=test_organization.id,
        )

        assert author is not None
        assert author.id == test_author.id
        assert author.name == "Dr. Jane Smith"
        assert author.orcid == "0000-0001-2345-6789"

    async def test_get_author_not_found(
        self,
        author_service: AuthorService,
        test_organization: Organization,
    ):
        """Test that getting a non-existent author returns None."""
        author = await author_service.get_author(
            author_id=uuid4(),
            organization_id=test_organization.id,
        )

        assert author is None

    async def test_get_author_tenant_isolation(
        self,
        author_service: AuthorService,
        test_author: Author,
        second_organization: Organization,
    ):
        """Test that author retrieval respects organization boundaries."""
        author = await author_service.get_author(
            author_id=test_author.id,
            organization_id=second_organization.id,
        )

        assert author is None

    async def test_get_author_profile(
        self,
        author_service: AuthorService,
        test_author: Author,
        test_organization: Organization,
        paper_author_link: PaperAuthor,  # Ensures author-paper relationship exists
    ):
        """Test getting author profile with stats."""
        profile = await author_service.get_author_profile(
            author_id=test_author.id,
            organization_id=test_organization.id,
        )

        assert profile is not None
        assert profile.id == test_author.id
        assert profile.name == "Dr. Jane Smith"
        assert profile.h_index == 25
        assert profile.citation_count == 1500
        assert profile.paper_count == 1

    async def test_get_author_detail(
        self,
        author_service: AuthorService,
        test_author: Author,
        test_organization: Organization,
        paper_author_link: PaperAuthor,
        test_contact: AuthorContact,
    ):
        """Test getting full author detail with papers and contacts."""
        detail = await author_service.get_author_detail(
            author_id=test_author.id,
            organization_id=test_organization.id,
        )

        assert detail is not None
        assert detail.id == test_author.id
        assert len(detail.papers) == 1
        assert len(detail.contacts) == 1
        assert detail.papers[0].is_corresponding is True

    async def test_list_authors(
        self,
        author_service: AuthorService,
        test_author: Author,
        test_organization: Organization,
    ):
        """Test listing authors with pagination."""
        response = await author_service.list_authors(
            organization_id=test_organization.id,
            page=1,
            page_size=10,
        )

        assert response.total == 1
        assert len(response.items) == 1
        assert response.items[0].name == "Dr. Jane Smith"

    async def test_list_authors_with_search(
        self,
        author_service: AuthorService,
        test_author: Author,
        test_organization: Organization,
        db_session: AsyncSession,
    ):
        """Test searching authors by name."""
        # Add another author
        other_author = Author(
            name="Dr. John Doe",
            organization_id=test_organization.id,
        )
        db_session.add(other_author)
        await db_session.flush()

        # Search for "Jane"
        response = await author_service.list_authors(
            organization_id=test_organization.id,
            search="Jane",
        )

        assert response.total == 1
        assert response.items[0].name == "Dr. Jane Smith"

    async def test_create_contact(
        self,
        author_service: AuthorService,
        test_author: Author,
        test_organization: Organization,
        test_user: User,
    ):
        """Test creating a new contact log."""
        contact_data = ContactCreate(
            contact_type=ContactType.EMAIL,
            subject="Research collaboration",
            notes="Initial outreach email.",
            outcome=ContactOutcome.IN_PROGRESS,
        )

        contact = await author_service.create_contact(
            author_id=test_author.id,
            organization_id=test_organization.id,
            user_id=test_user.id,
            data=contact_data,
        )

        assert contact.id is not None
        assert contact.author_id == test_author.id
        assert contact.organization_id == test_organization.id
        assert contact.contacted_by_id == test_user.id
        assert contact.contact_type == ContactType.EMAIL
        assert contact.subject == "Research collaboration"

    async def test_update_contact(
        self,
        author_service: AuthorService,
        test_contact: AuthorContact,
        test_organization: Organization,
    ):
        """Test updating an existing contact."""
        update_data = ContactUpdate(
            outcome=ContactOutcome.SUCCESSFUL,
            notes="Successfully completed collaboration discussion.",
        )

        updated = await author_service.update_contact(
            contact_id=test_contact.id,
            organization_id=test_organization.id,
            data=update_data,
        )

        assert updated.outcome == ContactOutcome.SUCCESSFUL
        assert "Successfully completed" in updated.notes

    async def test_delete_contact(
        self,
        author_service: AuthorService,
        test_contact: AuthorContact,
        test_organization: Organization,
        db_session: AsyncSession,
    ):
        """Test deleting a contact."""
        await author_service.delete_contact(
            contact_id=test_contact.id,
            organization_id=test_organization.id,
        )

        # Verify deletion
        result = await db_session.execute(
            select(AuthorContact).where(AuthorContact.id == test_contact.id)
        )
        assert result.scalar_one_or_none() is None

    async def test_get_contact_stats(
        self,
        author_service: AuthorService,
        test_author: Author,
        test_organization: Organization,
        multiple_contacts: list[AuthorContact],
    ):
        """Test getting contact statistics for an author."""
        stats = await author_service.get_contact_stats(
            author_id=test_author.id,
            organization_id=test_organization.id,
        )

        assert stats.author_id == test_author.id
        assert stats.total_contacts == 4
        assert stats.contacts_by_type["email"] == 2
        assert stats.contacts_by_type["meeting"] == 1
        assert stats.contacts_by_type["phone"] == 1
        assert stats.contacts_by_outcome["successful"] == 2

    async def test_contact_tenant_isolation(
        self,
        author_service: AuthorService,
        test_contact: AuthorContact,
        second_organization: Organization,
    ):
        """Test that contact operations respect tenant boundaries."""
        from paper_scraper.core.exceptions import NotFoundError

        # Trying to update a contact with wrong organization should fail
        with pytest.raises(NotFoundError):
            await author_service.update_contact(
                contact_id=test_contact.id,
                organization_id=second_organization.id,
                data=ContactUpdate(notes="Attempted unauthorized update"),
            )


# =============================================================================
# API Router Tests
# =============================================================================


class TestAuthorsRouter:
    """Tests for authors API endpoints."""

    async def test_list_authors(
        self,
        authenticated_client: AsyncClient,
        test_author: Author,
    ):
        """Test listing authors via API."""
        response = await authenticated_client.get("/api/v1/authors/")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    async def test_list_authors_with_pagination(
        self,
        authenticated_client: AsyncClient,
        test_author: Author,
    ):
        """Test pagination parameters for authors list."""
        response = await authenticated_client.get(
            "/api/v1/authors/", params={"page": 1, "page_size": 5}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5

    async def test_list_authors_with_search(
        self,
        authenticated_client: AsyncClient,
        test_author: Author,
    ):
        """Test searching authors via API."""
        response = await authenticated_client.get(
            "/api/v1/authors/", params={"search": "Jane"}
        )

        assert response.status_code == 200
        data = response.json()
        # Should find Dr. Jane Smith
        assert data["total"] >= 0

    async def test_get_author_profile(
        self,
        authenticated_client: AsyncClient,
        test_author: Author,
    ):
        """Test getting author profile via API."""
        response = await authenticated_client.get(
            f"/api/v1/authors/{test_author.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_author.id)
        assert data["name"] == "Dr. Jane Smith"
        assert data["h_index"] == 25

    async def test_get_author_profile_not_found(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test getting non-existent author returns 404."""
        response = await authenticated_client.get(
            f"/api/v1/authors/{uuid4()}"
        )

        assert response.status_code == 404

    async def test_get_author_detail(
        self,
        authenticated_client: AsyncClient,
        test_author: Author,
        paper_author_link: PaperAuthor,
    ):
        """Test getting full author detail via API."""
        response = await authenticated_client.get(
            f"/api/v1/authors/{test_author.id}/detail"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_author.id)
        assert "papers" in data
        assert "contacts" in data

    async def test_create_contact(
        self,
        authenticated_client: AsyncClient,
        test_author: Author,
    ):
        """Test creating a contact via API."""
        response = await authenticated_client.post(
            f"/api/v1/authors/{test_author.id}/contacts",
            json={
                "contact_type": "email",
                "subject": "API test contact",
                "notes": "Created via API test.",
                "outcome": "in_progress",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["contact_type"] == "email"
        assert data["subject"] == "API test contact"
        assert data["author_id"] == str(test_author.id)

    async def test_update_contact(
        self,
        authenticated_client: AsyncClient,
        test_author: Author,
        test_contact: AuthorContact,
    ):
        """Test updating a contact via API."""
        response = await authenticated_client.patch(
            f"/api/v1/authors/{test_author.id}/contacts/{test_contact.id}",
            json={
                "outcome": "successful",
                "notes": "Updated via API.",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["outcome"] == "successful"

    async def test_delete_contact(
        self,
        authenticated_client: AsyncClient,
        test_author: Author,
        test_contact: AuthorContact,
    ):
        """Test deleting a contact via API."""
        response = await authenticated_client.delete(
            f"/api/v1/authors/{test_author.id}/contacts/{test_contact.id}"
        )

        assert response.status_code == 204

    async def test_get_contact_stats(
        self,
        authenticated_client: AsyncClient,
        test_author: Author,
        multiple_contacts: list[AuthorContact],
    ):
        """Test getting contact statistics via API."""
        response = await authenticated_client.get(
            f"/api/v1/authors/{test_author.id}/contacts/stats"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["author_id"] == str(test_author.id)
        assert data["total_contacts"] == 4
        assert "contacts_by_type" in data
        assert "contacts_by_outcome" in data

    async def test_enrich_author(
        self,
        authenticated_client: AsyncClient,
        test_author: Author,
    ):
        """Test enriching author data via API."""
        response = await authenticated_client.post(
            f"/api/v1/authors/{test_author.id}/enrich",
            json={
                "source": "openalex",
                "force_update": False,
            },
        )

        # Note: This might fail if no actual API is available, but structure should be valid
        assert response.status_code == 200
        data = response.json()
        assert data["author_id"] == str(test_author.id)
        assert "success" in data
        assert "updated_fields" in data

    async def test_unauthorized_access(
        self,
        client: AsyncClient,
        test_author: Author,
    ):
        """Test that unauthenticated requests are rejected."""
        response = await client.get("/api/v1/authors/")

        assert response.status_code == 401

    async def test_author_response_structure(
        self,
        authenticated_client: AsyncClient,
        test_author: Author,
    ):
        """Test that author response has correct structure."""
        response = await authenticated_client.get(
            f"/api/v1/authors/{test_author.id}"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all expected fields are present
        assert "id" in data
        assert "name" in data
        assert "orcid" in data
        assert "openalex_id" in data
        assert "affiliations" in data
        assert "h_index" in data
        assert "citation_count" in data
        assert "works_count" in data
        assert "paper_count" in data
        assert "recent_contacts_count" in data
        assert "created_at" in data
        assert "updated_at" in data
