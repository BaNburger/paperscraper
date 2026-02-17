"""Service layer for papers module."""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from paper_scraper.core.exceptions import DuplicateError, NotFoundError
from paper_scraper.core.sql_utils import escape_like
from paper_scraper.modules.papers.clients.crossref import CrossrefClient
from paper_scraper.modules.papers.clients.openalex import OpenAlexClient
from paper_scraper.modules.papers.models import Author, Paper, PaperAuthor, PaperSource
from paper_scraper.modules.papers.schemas import PaperListResponse
from paper_scraper.modules.scoring.pitch_generator import (
    PitchGenerator,
    SimplifiedAbstractGenerator,
)

logger = logging.getLogger(__name__)


class PaperService:
    """Service for paper management and ingestion."""

    def __init__(self, db: AsyncSession):
        """Initialize paper service.

        Args:
            db: Async database session.
        """
        self.db = db

    # =========================================================================
    # Paper CRUD
    # =========================================================================

    async def get_paper(
        self, paper_id: UUID, organization_id: UUID
    ) -> Paper | None:
        """Get paper by ID with tenant isolation.

        Args:
            paper_id: Paper UUID.
            organization_id: Organization UUID for tenant isolation.

        Returns:
            Paper with authors loaded, or None if not found.
        """
        result = await self.db.execute(
            select(Paper)
            .options(selectinload(Paper.authors).selectinload(PaperAuthor.author))
            .where(
                Paper.id == paper_id,
                Paper.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_papers(
        self,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> PaperListResponse:
        """List papers with pagination and optional search.

        Args:
            organization_id: Organization UUID for tenant isolation.
            page: Page number (1-indexed).
            page_size: Number of items per page.
            search: Optional search query for title/abstract.

        Returns:
            Paginated list response.
        """
        query = select(Paper).where(Paper.organization_id == organization_id)

        if search:
            # Escape LIKE special characters to prevent pattern injection
            search_filter = f"%{escape_like(search)}%"
            query = query.where(
                Paper.title.ilike(search_filter, escape="\\")
                | Paper.abstract.ilike(search_filter, escape="\\")
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(Paper.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        papers = list(result.scalars().all())

        return PaperListResponse(
            items=papers,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size if total > 0 else 0,
        )

    async def get_paper_by_doi(
        self, doi: str, organization_id: UUID
    ) -> Paper | None:
        """Get paper by DOI within organization.

        Args:
            doi: Digital Object Identifier.
            organization_id: Organization UUID for tenant isolation.

        Returns:
            Paper or None if not found.
        """
        result = await self.db.execute(
            select(Paper).where(
                Paper.doi == doi,
                Paper.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete_paper(
        self, paper_id: UUID, organization_id: UUID
    ) -> bool:
        """Delete paper by ID.

        Args:
            paper_id: Paper UUID.
            organization_id: Organization UUID for tenant isolation.

        Returns:
            True if deleted, False if not found.
        """
        paper = await self.get_paper(paper_id, organization_id)
        if not paper:
            return False
        await self.db.delete(paper)
        await self.db.flush()
        return True

    # =========================================================================
    # Ingestion
    # =========================================================================

    async def ingest_by_doi(
        self, doi: str, organization_id: UUID, created_by_id: UUID | None = None
    ) -> Paper:
        """Ingest paper by DOI.

        Strategy: OpenAlex first (richer metadata), Crossref fallback.

        Args:
            doi: Digital Object Identifier.
            organization_id: Organization UUID.

        Returns:
            Created Paper object.

        Raises:
            DuplicateError: If paper with DOI already exists.
            NotFoundError: If paper not found in any source.
        """
        # Clean DOI
        doi = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")

        # Check if already exists
        existing = await self.get_paper_by_doi(doi, organization_id)
        if existing:
            raise DuplicateError("Paper", "doi", doi)

        paper_data = None

        # Try OpenAlex first (better metadata)
        async with OpenAlexClient() as client:
            paper_data = await client.get_by_doi(doi)

        # Fallback to Crossref
        if not paper_data:
            async with CrossrefClient() as client:
                paper_data = await client.get_by_id(doi)

        if not paper_data:
            raise NotFoundError("Paper", doi, {"field": "doi"})

        paper = await self._create_paper_from_data(
            paper_data, organization_id, created_by_id=created_by_id
        )
        await self.db.flush()
        return paper

    async def ingest_from_pdf(
        self,
        file_content: bytes,
        filename: str,
        organization_id: UUID,
        created_by_id: UUID | None = None,
    ) -> Paper:
        """Ingest paper from uploaded PDF.

        Args:
            file_content: PDF file bytes.
            filename: Original filename.
            organization_id: Organization UUID.

        Returns:
            Created Paper object.
        """
        # Lazy import to avoid loading PyMuPDF until needed
        from paper_scraper.modules.papers.pdf_service import PDFService

        pdf_service = PDFService()
        extracted = await pdf_service.upload_and_extract(
            file_content=file_content,
            filename=filename,
            organization_id=organization_id,
        )

        # Create paper data in normalized format
        paper_data = {
            "source": "pdf",
            "source_id": extracted["pdf_path"],
            "title": extracted["title"],
            "abstract": extracted["abstract"],
            "authors": extracted["authors"],
            "keywords": extracted.get("keywords", []),
            "full_text": extracted.get("full_text"),
            "raw_metadata": {"filename": filename, "pdf_path": extracted["pdf_path"]},
        }

        paper = await self._create_paper_from_data(
            paper_data, organization_id, created_by_id=created_by_id
        )

        # Store pdf_path on the paper
        paper.pdf_path = extracted["pdf_path"]
        if extracted.get("full_text"):
            paper.full_text = extracted["full_text"]

        await self.db.flush()
        return paper

    async def _create_paper_from_data(
        self,
        data: dict,
        organization_id: UUID,
        created_by_id: UUID | None = None,
    ) -> Paper:
        """Create paper and authors from normalized API data.

        Args:
            data: Normalized paper data from API client.
            organization_id: Organization UUID.
            created_by_id: User UUID who initiated the import.

        Returns:
            Created Paper object.
        """
        # Parse publication date
        pub_date = None
        if data.get("publication_date"):
            try:
                pub_date = datetime.fromisoformat(data["publication_date"])
            except ValueError:
                logger.warning("Invalid publication_date format: %s", data["publication_date"])

        # Create paper
        paper = Paper(
            organization_id=organization_id,
            created_by_id=created_by_id,
            doi=data.get("doi"),
            source=PaperSource(data["source"]),
            source_id=data.get("source_id"),
            title=data["title"],
            abstract=data.get("abstract"),
            publication_date=pub_date,
            journal=data.get("journal"),
            volume=data.get("volume"),
            issue=data.get("issue"),
            pages=data.get("pages"),
            keywords=data.get("keywords", []),
            references_count=data.get("references_count"),
            citations_count=data.get("citations_count"),
            raw_metadata=data.get("raw_metadata", {}),
        )
        self.db.add(paper)
        await self.db.flush()

        # Create/link authors
        for idx, author_data in enumerate(data.get("authors", [])):
            author = await self._get_or_create_author(author_data, organization_id)
            paper_author = PaperAuthor(
                paper_id=paper.id,
                author_id=author.id,
                position=idx,
                is_corresponding=author_data.get("is_corresponding", False),
            )
            self.db.add(paper_author)

        await self.db.flush()
        return paper

    async def _get_or_create_author(
        self, data: dict, organization_id: UUID
    ) -> Author:
        """Get existing author or create new one within organization.

        Lookup order: ORCID > OpenAlex ID > Create new.
        Authors are scoped to organizations for multi-tenancy.

        Args:
            data: Author data from API response.
            organization_id: Organization UUID for tenant isolation.

        Returns:
            Author object (existing or new).
        """
        # Try to find by ORCID within organization
        if data.get("orcid"):
            result = await self.db.execute(
                select(Author).where(
                    Author.organization_id == organization_id,
                    Author.orcid == data["orcid"],
                )
            )
            author = result.scalar_one_or_none()
            if author:
                return author

        # Try to find by OpenAlex ID within organization
        if data.get("openalex_id"):
            result = await self.db.execute(
                select(Author).where(
                    Author.organization_id == organization_id,
                    Author.openalex_id == data["openalex_id"],
                )
            )
            author = result.scalar_one_or_none()
            if author:
                return author

        # Create new author in organization
        author = Author(
            organization_id=organization_id,
            name=data["name"],
            orcid=data.get("orcid"),
            openalex_id=data.get("openalex_id"),
            affiliations=data.get("affiliations", []),
        )
        self.db.add(author)
        await self.db.flush()
        return author

    # =========================================================================
    # AI-Generated Content
    # =========================================================================

    async def generate_pitch(
        self, paper_id: UUID, organization_id: UUID
    ) -> Paper:
        """Generate one-line pitch for a paper.

        Args:
            paper_id: Paper UUID.
            organization_id: Organization UUID for tenant isolation.

        Returns:
            Updated Paper object with one_line_pitch.

        Raises:
            NotFoundError: If paper not found.
        """
        paper = await self.get_paper(paper_id, organization_id)
        if not paper:
            raise NotFoundError("Paper", paper_id)

        # Generate pitch using LLM
        pitch_generator = PitchGenerator()
        pitch = await pitch_generator.generate(
            title=paper.title,
            abstract=paper.abstract,
            keywords=paper.keywords,
        )

        # Update paper with pitch
        paper.one_line_pitch = pitch
        await self.db.flush()

        return paper

    async def generate_simplified_abstract(
        self, paper_id: UUID, organization_id: UUID
    ) -> Paper:
        """Generate simplified abstract for a paper.

        Args:
            paper_id: Paper UUID.
            organization_id: Organization UUID for tenant isolation.

        Returns:
            Updated Paper object with simplified_abstract.

        Raises:
            NotFoundError: If paper not found.
        """
        paper = await self.get_paper(paper_id, organization_id)
        if not paper:
            raise NotFoundError("Paper", paper_id)

        if not paper.abstract:
            raise ValueError("Paper has no abstract to simplify")

        # Generate simplified abstract using LLM
        generator = SimplifiedAbstractGenerator()
        simplified = await generator.generate(
            title=paper.title,
            abstract=paper.abstract,
        )

        # Update paper with simplified abstract
        paper.simplified_abstract = simplified
        await self.db.flush()

        return paper
