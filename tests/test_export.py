"""Tests for export module."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.auth.models import Organization, User
from paper_scraper.modules.papers.models import Author, Paper, PaperAuthor, PaperSource
from paper_scraper.modules.scoring.models import PaperScore


class TestExportEndpoints:
    """Test export API endpoints."""

    @pytest.mark.asyncio
    async def test_export_csv_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test CSV export when no papers exist."""
        response = await client.get("/api/v1/export/csv", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "papers_export_" in response.headers["content-disposition"]
        assert response.headers["x-paper-count"] == "0"

    @pytest.mark.asyncio
    async def test_export_csv_with_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test CSV export with papers."""
        # Create paper
        paper = Paper(
            organization_id=test_user.organization_id,
            title="Test Paper for Export",
            abstract="Test abstract",
            doi="10.1234/test.export",
            source=PaperSource.MANUAL,
            keywords=["AI", "ML"],
        )
        db_session.add(paper)
        await db_session.flush()

        response = await client.get("/api/v1/export/csv", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["x-paper-count"] == "1"

        # Check content
        content = response.text
        assert "Test Paper for Export" in content
        assert "10.1234/test.export" in content
        assert "Test abstract" in content

    @pytest.mark.asyncio
    async def test_export_csv_with_scores(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test CSV export includes scoring data."""
        # Create paper
        paper = Paper(
            organization_id=test_user.organization_id,
            title="Scored Paper",
            source=PaperSource.MANUAL,
        )
        db_session.add(paper)
        await db_session.flush()

        # Create score
        score = PaperScore(
            paper_id=paper.id,
            organization_id=test_user.organization_id,
            novelty=8.0,
            ip_potential=7.5,
            marketability=6.0,
            feasibility=8.5,
            commercialization=7.0,
            overall_score=7.4,
            overall_confidence=0.85,
            model_version="test",
        )
        db_session.add(score)
        await db_session.flush()

        response = await client.get(
            "/api/v1/export/csv",
            params={"include_scores": True},
            headers=auth_headers,
        )
        assert response.status_code == 200

        content = response.text
        assert "7.40" in content  # Overall score
        assert "8.00" in content  # Novelty

    @pytest.mark.asyncio
    async def test_export_bibtex_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test BibTeX export when no papers exist."""
        response = await client.get("/api/v1/export/bibtex", headers=auth_headers)
        assert response.status_code == 200
        assert "bibtex" in response.headers["content-type"]
        assert response.headers["x-paper-count"] == "0"

    @pytest.mark.asyncio
    async def test_export_bibtex_with_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test BibTeX export with papers and authors."""
        # Create author
        author = Author(
            name="John Smith",
            orcid="0000-0001-2345-6789",
            organization_id=test_user.organization_id,
        )
        db_session.add(author)
        await db_session.flush()

        # Create paper
        from datetime import datetime
        paper = Paper(
            organization_id=test_user.organization_id,
            title="BibTeX Test Paper",
            abstract="Testing BibTeX export",
            doi="10.1234/bibtex.test",
            source=PaperSource.MANUAL,
            journal="Nature",
            publication_date=datetime(2024, 6, 15),
            volume="100",
            issue="5",
            pages="10-20",
        )
        db_session.add(paper)
        await db_session.flush()

        # Link author to paper
        paper_author = PaperAuthor(
            paper_id=paper.id,
            author_id=author.id,
            position=0,
            is_corresponding=True,
        )
        db_session.add(paper_author)
        await db_session.flush()

        response = await client.get("/api/v1/export/bibtex", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["x-paper-count"] == "1"

        content = response.text
        assert "@article{" in content
        assert "title = {BibTeX Test Paper}" in content
        assert "author = {John Smith}" in content
        assert "journal = {Nature}" in content
        assert "doi = {10.1234/bibtex.test}" in content
        assert "year = {2024}" in content
        assert "volume = {100}" in content

    @pytest.mark.asyncio
    async def test_export_pdf_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test PDF export when no papers exist."""
        response = await client.get("/api/v1/export/pdf", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["x-paper-count"] == "0"

    @pytest.mark.asyncio
    async def test_export_pdf_with_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test PDF export with papers."""
        paper = Paper(
            organization_id=test_user.organization_id,
            title="PDF Export Test Paper",
            abstract="Testing PDF export functionality",
            source=PaperSource.MANUAL,
        )
        db_session.add(paper)
        await db_session.flush()

        response = await client.get("/api/v1/export/pdf", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["x-paper-count"] == "1"

        content = response.text
        assert "PDF Export Test Paper" in content
        assert "Testing PDF export functionality" in content

    @pytest.mark.asyncio
    async def test_batch_export_csv(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test batch export with specific paper IDs."""
        # Create papers
        paper1 = Paper(
            organization_id=test_user.organization_id,
            title="Paper 1",
            source=PaperSource.MANUAL,
        )
        paper2 = Paper(
            organization_id=test_user.organization_id,
            title="Paper 2",
            source=PaperSource.MANUAL,
        )
        paper3 = Paper(
            organization_id=test_user.organization_id,
            title="Paper 3",
            source=PaperSource.MANUAL,
        )
        db_session.add_all([paper1, paper2, paper3])
        await db_session.flush()

        # Export only paper1 and paper2
        response = await client.post(
            "/api/v1/export/batch",
            params={"format": "csv"},
            json=[str(paper1.id), str(paper2.id)],
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.headers["x-paper-count"] == "2"

        content = response.text
        assert "Paper 1" in content
        assert "Paper 2" in content
        assert "Paper 3" not in content

    @pytest.mark.asyncio
    async def test_export_tenant_isolation(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that export only includes papers from user's organization."""
        # Create a real organization for the other tenant
        other_org = Organization(name="Other Org", type="university")
        db_session.add(other_org)
        await db_session.flush()
        await db_session.refresh(other_org)

        # Create paper for test user's org
        paper = Paper(
            organization_id=test_user.organization_id,
            title="My Org Paper",
            source=PaperSource.MANUAL,
        )
        db_session.add(paper)

        # Create paper for different org
        other_org_paper = Paper(
            organization_id=other_org.id,
            title="Other Org Paper",
            source=PaperSource.MANUAL,
        )
        db_session.add(other_org_paper)
        await db_session.flush()

        response = await client.get("/api/v1/export/csv", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["x-paper-count"] == "1"

        content = response.text
        assert "My Org Paper" in content
        assert "Other Org Paper" not in content

    @pytest.mark.asyncio
    async def test_unauthenticated_access(
        self,
        client: AsyncClient,
    ):
        """Test that unauthenticated users cannot export."""
        response = await client.get("/api/v1/export/csv")
        assert response.status_code == 401

        response = await client.get("/api/v1/export/bibtex")
        assert response.status_code == 401

        response = await client.get("/api/v1/export/pdf")
        assert response.status_code == 401


class TestExportService:
    """Test export service directly."""

    @pytest.mark.asyncio
    async def test_bibtex_escaping(self):
        """Test BibTeX special character escaping."""
        from paper_scraper.modules.export.service import ExportService

        # Create a mock session (we only test the escaping method)
        service = ExportService(None)  # type: ignore

        # Test escaping special characters
        text = "Machine Learning & AI: A 100% Complete Guide"
        escaped = service._escape_bibtex(text)

        assert r"\&" in escaped
        assert r"\%" in escaped

    @pytest.mark.asyncio
    async def test_bibtex_citation_key_generation(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test BibTeX citation key generation from author and year."""
        from datetime import datetime
        from paper_scraper.modules.export.service import ExportService

        # Create author
        author = Author(name="Einstein Albert", organization_id=test_user.organization_id)
        db_session.add(author)
        await db_session.flush()

        # Create paper
        paper = Paper(
            organization_id=test_user.organization_id,
            title="Theory of Relativity",
            source=PaperSource.MANUAL,
            publication_date=datetime(1905, 6, 30),
        )
        db_session.add(paper)
        await db_session.flush()

        # Link author
        paper_author = PaperAuthor(
            paper_id=paper.id,
            author_id=author.id,
            position=0,
            is_corresponding=True,
        )
        db_session.add(paper_author)
        await db_session.flush()

        # Generate BibTeX
        service = ExportService(db_session)
        bibtex, count = await service.export_bibtex(test_user.organization_id)

        assert count == 1
        assert "@article{albert1905," in bibtex  # Last name + year
