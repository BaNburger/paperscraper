"""Tests for papers module."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.auth.models import User
from paper_scraper.modules.papers.models import Paper, PaperSource


class TestPaperEndpoints:
    """Test paper API endpoints."""

    @pytest.mark.asyncio
    async def test_list_papers_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test listing papers when none exist."""
        response = await client.get("/api/v1/papers/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["pages"] == 0

    @pytest.mark.asyncio
    async def test_list_papers_with_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test listing papers with data."""
        # Create test paper
        paper = Paper(
            organization_id=test_user.organization_id,
            title="Test Paper Title",
            abstract="Test abstract content",
            source=PaperSource.MANUAL,
        )
        db_session.add(paper)
        await db_session.flush()

        response = await client.get("/api/v1/papers/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Test Paper Title"
        assert data["items"][0]["abstract"] == "Test abstract content"
        assert data["items"][0]["source"] == "manual"

    @pytest.mark.asyncio
    async def test_list_papers_with_search(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test listing papers with search filter."""
        # Create test papers
        paper1 = Paper(
            organization_id=test_user.organization_id,
            title="Machine Learning Paper",
            abstract="This paper discusses ML techniques",
            source=PaperSource.MANUAL,
        )
        paper2 = Paper(
            organization_id=test_user.organization_id,
            title="Quantum Computing Paper",
            abstract="This paper discusses quantum algorithms",
            source=PaperSource.MANUAL,
        )
        db_session.add_all([paper1, paper2])
        await db_session.flush()

        # Search for "Machine"
        response = await client.get(
            "/api/v1/papers/",
            params={"search": "Machine"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Machine Learning Paper"

    @pytest.mark.asyncio
    async def test_list_papers_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test pagination of papers list."""
        # Create multiple papers
        for i in range(5):
            paper = Paper(
                organization_id=test_user.organization_id,
                title=f"Paper {i}",
                source=PaperSource.MANUAL,
            )
            db_session.add(paper)
        await db_session.flush()

        # Request page 1 with page_size 2
        response = await client.get(
            "/api/v1/papers/",
            params={"page": 1, "page_size": 2},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["pages"] == 3

    @pytest.mark.asyncio
    async def test_get_paper_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test getting non-existent paper."""
        response = await client.get(
            f"/api/v1/papers/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_paper_detail(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test getting paper details."""
        paper = Paper(
            organization_id=test_user.organization_id,
            title="Detailed Paper",
            abstract="Detailed abstract",
            doi="10.1234/test.123",
            source=PaperSource.OPENALEX,
            source_id="W12345",
            journal="Nature",
            volume="100",
            issue="1",
            pages="1-10",
            keywords=["AI", "ML"],
            citations_count=42,
        )
        db_session.add(paper)
        await db_session.flush()

        response = await client.get(
            f"/api/v1/papers/{paper.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Detailed Paper"
        assert data["doi"] == "10.1234/test.123"
        assert data["source"] == "openalex"
        assert data["journal"] == "Nature"
        assert data["citations_count"] == 42
        assert data["keywords"] == ["AI", "ML"]

    @pytest.mark.asyncio
    async def test_delete_paper(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test deleting a paper."""
        paper = Paper(
            organization_id=test_user.organization_id,
            title="Paper to Delete",
            source=PaperSource.MANUAL,
        )
        db_session.add(paper)
        await db_session.flush()
        paper_id = paper.id

        response = await client.delete(
            f"/api/v1/papers/{paper_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Expire all objects in session to force re-fetch from database
        db_session.expire_all()

        # Verify paper is deleted by checking it's no longer in the list
        response = await client.get("/api/v1/papers/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        paper_ids = [p["id"] for p in data["items"]]
        assert str(paper_id) not in paper_ids

    @pytest.mark.asyncio
    async def test_delete_paper_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test deleting non-existent paper."""
        response = await client.delete(
            f"/api/v1/papers/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_tenant_isolation(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that users can only see papers from their organization."""
        # Create paper for test user's org
        paper = Paper(
            organization_id=test_user.organization_id,
            title="My Org Paper",
            source=PaperSource.MANUAL,
        )
        db_session.add(paper)

        # Create paper for different org
        other_org_paper = Paper(
            organization_id=uuid.uuid4(),  # Different org
            title="Other Org Paper",
            source=PaperSource.MANUAL,
        )
        db_session.add(other_org_paper)
        await db_session.flush()

        response = await client.get("/api/v1/papers/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "My Org Paper"

    @pytest.mark.asyncio
    async def test_unauthenticated_access(
        self,
        client: AsyncClient,
    ):
        """Test that unauthenticated users cannot access papers."""
        response = await client.get("/api/v1/papers/")
        assert response.status_code == 401


class TestOpenAlexClient:
    """Test OpenAlex API client."""

    @pytest.mark.asyncio
    async def test_normalize(self):
        """Test OpenAlex data normalization."""
        from paper_scraper.modules.papers.clients.openalex import OpenAlexClient

        client = OpenAlexClient()
        raw = {
            "id": "W123456789",
            "title": "Machine Learning for Science",
            "doi": "https://doi.org/10.1234/test.123",
            "abstract": "This paper explores machine learning applications...",
            "publication_date": "2024-01-15",
            "authorships": [
                {
                    "author": {
                        "display_name": "Jane Doe",
                        "orcid": "0000-0001-2345-6789",
                        "id": "A12345",
                    },
                    "institutions": [{"display_name": "MIT"}],
                    "is_corresponding": True,
                },
                {
                    "author": {
                        "display_name": "John Smith",
                        "orcid": None,
                        "id": "A67890",
                    },
                    "institutions": [{"display_name": "Stanford"}],
                    "is_corresponding": False,
                },
            ],
            "primary_location": {"source": {"display_name": "Nature"}},
            "biblio": {
                "volume": "42",
                "issue": "3",
                "first_page": "100",
                "last_page": "110",
            },
            "keywords": [
                {"display_name": "Machine Learning"},
                {"display_name": "Science"},
            ],
            "referenced_works_count": 50,
            "cited_by_count": 42,
        }

        normalized = client.normalize(raw)

        assert normalized["source"] == "openalex"
        assert normalized["source_id"] == "W123456789"
        assert normalized["title"] == "Machine Learning for Science"
        assert normalized["doi"] == "10.1234/test.123"
        assert normalized["abstract"] == "This paper explores machine learning applications..."
        assert normalized["publication_date"] == "2024-01-15"
        assert normalized["journal"] == "Nature"
        assert normalized["volume"] == "42"
        assert normalized["issue"] == "3"
        assert normalized["pages"] == "100-110"
        assert normalized["keywords"] == ["Machine Learning", "Science"]
        assert normalized["references_count"] == 50
        assert normalized["citations_count"] == 42

        # Check authors
        assert len(normalized["authors"]) == 2
        assert normalized["authors"][0]["name"] == "Jane Doe"
        assert normalized["authors"][0]["orcid"] == "0000-0001-2345-6789"
        assert normalized["authors"][0]["openalex_id"] == "A12345"
        assert normalized["authors"][0]["affiliations"] == ["MIT"]
        assert normalized["authors"][0]["is_corresponding"] is True
        assert normalized["authors"][1]["name"] == "John Smith"
        assert normalized["authors"][1]["is_corresponding"] is False

    @pytest.mark.asyncio
    async def test_normalize_minimal_data(self):
        """Test OpenAlex normalization with minimal data."""
        from paper_scraper.modules.papers.clients.openalex import OpenAlexClient

        client = OpenAlexClient()
        raw = {
            "id": "W999",
            "title": None,  # Missing title
            "doi": None,
            "authorships": [],
        }

        normalized = client.normalize(raw)

        assert normalized["title"] == "Untitled"
        assert normalized["doi"] is None
        assert normalized["authors"] == []
        assert normalized["journal"] is None


class TestCrossrefClient:
    """Test Crossref API client."""

    @pytest.mark.asyncio
    async def test_normalize(self):
        """Test Crossref data normalization."""
        from paper_scraper.modules.papers.clients.crossref import CrossrefClient

        client = CrossrefClient()
        raw = {
            "DOI": "10.1234/test.456",
            "title": ["Deep Learning Applications"],
            "abstract": "We present novel deep learning techniques...",
            "author": [
                {
                    "given": "John",
                    "family": "Smith",
                    "ORCID": "https://orcid.org/0000-0002-1234-5678",
                    "affiliation": [{"name": "Stanford University"}],
                },
                {
                    "given": "Jane",
                    "family": "Doe",
                    "affiliation": [],
                },
            ],
            "container-title": ["Science"],
            "published-print": {"date-parts": [[2024, 3, 1]]},
            "volume": "380",
            "issue": "5",
            "page": "50-65",
            "subject": ["Computer Science", "AI"],
            "references-count": 30,
            "is-referenced-by-count": 15,
        }

        normalized = client.normalize(raw)

        assert normalized["source"] == "crossref"
        assert normalized["source_id"] == "10.1234/test.456"
        assert normalized["title"] == "Deep Learning Applications"
        assert normalized["doi"] == "10.1234/test.456"
        assert normalized["abstract"] == "We present novel deep learning techniques..."
        assert normalized["publication_date"] == "2024-03-01"
        assert normalized["journal"] == "Science"
        assert normalized["volume"] == "380"
        assert normalized["issue"] == "5"
        assert normalized["pages"] == "50-65"
        assert normalized["keywords"] == ["Computer Science", "AI"]
        assert normalized["references_count"] == 30
        assert normalized["citations_count"] == 15

        # Check authors
        assert len(normalized["authors"]) == 2
        assert normalized["authors"][0]["name"] == "John Smith"
        assert normalized["authors"][0]["orcid"] == "https://orcid.org/0000-0002-1234-5678"
        assert normalized["authors"][0]["affiliations"] == ["Stanford University"]
        assert normalized["authors"][1]["name"] == "Jane Doe"
        assert normalized["authors"][1]["affiliations"] == []

    @pytest.mark.asyncio
    async def test_normalize_list_fields(self):
        """Test Crossref normalization handles list fields correctly."""
        from paper_scraper.modules.papers.clients.crossref import CrossrefClient

        client = CrossrefClient()
        raw = {
            "DOI": "10.1234/test.789",
            "title": [],  # Empty list
            "container-title": [],
            "author": [],
            "published-online": {"date-parts": [[2024, 6]]},  # Only year and month
        }

        normalized = client.normalize(raw)

        assert normalized["title"] == "Untitled"
        assert normalized["journal"] is None
        assert normalized["authors"] == []
        assert normalized["publication_date"] == "2024-06-01"

    @pytest.mark.asyncio
    async def test_extract_date_fallback(self):
        """Test Crossref date extraction with fallback fields."""
        from paper_scraper.modules.papers.clients.crossref import CrossrefClient

        client = CrossrefClient()

        # Test with created date as fallback
        raw = {
            "DOI": "10.1234/test",
            "title": ["Test"],
            "created": {"date-parts": [[2023, 12, 25]]},
        }

        normalized = client.normalize(raw)
        assert normalized["publication_date"] == "2023-12-25"

        # Test with no date
        raw_no_date = {
            "DOI": "10.1234/test2",
            "title": ["Test 2"],
        }

        normalized_no_date = client.normalize(raw_no_date)
        assert normalized_no_date["publication_date"] is None
