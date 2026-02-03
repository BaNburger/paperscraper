"""Service layer for papers module."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from paper_scraper.core.exceptions import DuplicateError, NotFoundError
from paper_scraper.modules.papers.clients.arxiv import ArxivClient
from paper_scraper.modules.papers.clients.crossref import CrossrefClient
from paper_scraper.modules.papers.clients.openalex import OpenAlexClient
from paper_scraper.modules.papers.clients.pubmed import PubMedClient
from paper_scraper.modules.papers.models import Author, Paper, PaperAuthor, PaperSource
from paper_scraper.modules.papers.schemas import IngestResult, PaperListResponse
from paper_scraper.modules.scoring.pitch_generator import PitchGenerator, SimplifiedAbstractGenerator


def _escape_like(text: str) -> str:
    """Escape special characters for SQL LIKE patterns.

    Args:
        text: The search text to escape.

    Returns:
        Text with LIKE special characters (%, _) escaped.
    """
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


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
            search_filter = f"%{_escape_like(search)}%"
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

    async def ingest_by_doi(self, doi: str, organization_id: UUID) -> Paper:
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
            raise NotFoundError("Paper", "doi", doi)

        paper = await self._create_paper_from_data(paper_data, organization_id)
        await self.db.commit()
        return paper

    async def ingest_from_openalex(
        self,
        query: str,
        organization_id: UUID,
        max_results: int = 100,
        filters: dict | None = None,
    ) -> IngestResult:
        """Batch ingest papers from OpenAlex search.

        Args:
            query: OpenAlex search query.
            organization_id: Organization UUID.
            max_results: Maximum papers to import.
            filters: Optional OpenAlex filters.

        Returns:
            IngestResult with counts of created/skipped papers.
        """
        created = 0
        skipped = 0
        errors: list[str] = []

        async with OpenAlexClient() as client:
            papers_data = await client.search(query, max_results, filters)

        for paper_data in papers_data:
            try:
                doi = paper_data.get("doi")
                if doi:
                    existing = await self.get_paper_by_doi(doi, organization_id)
                    if existing:
                        skipped += 1
                        continue

                await self._create_paper_from_data(paper_data, organization_id)
                created += 1
            except Exception as e:
                title = paper_data.get("title", "unknown")[:50]
                errors.append(f"Error importing '{title}': {str(e)}")

        await self.db.commit()

        return IngestResult(
            papers_created=created,
            papers_updated=0,
            papers_skipped=skipped,
            errors=errors,
        )

    async def ingest_from_pubmed(
        self,
        query: str,
        organization_id: UUID,
        max_results: int = 100,
    ) -> IngestResult:
        """Batch ingest papers from PubMed search.

        Args:
            query: PubMed search query.
            organization_id: Organization UUID.
            max_results: Maximum papers to import.

        Returns:
            IngestResult with counts of created/skipped papers.
        """
        async with PubMedClient() as client:
            papers_data = await client.search(query, max_results)

        return await self._ingest_papers_batch(
            papers_data, organization_id, PaperSource.PUBMED
        )

    async def ingest_from_arxiv(
        self,
        query: str,
        organization_id: UUID,
        max_results: int = 100,
        category: str | None = None,
    ) -> IngestResult:
        """Batch ingest papers from arXiv search.

        Args:
            query: arXiv search query.
            organization_id: Organization UUID.
            max_results: Maximum papers to import.
            category: Optional arXiv category filter.

        Returns:
            IngestResult with counts of created/skipped papers.
        """
        async with ArxivClient() as client:
            papers_data = await client.search(query, max_results, category)

        return await self._ingest_papers_batch(
            papers_data, organization_id, PaperSource.ARXIV
        )

    async def _ingest_papers_batch(
        self,
        papers_data: list[dict],
        organization_id: UUID,
        source: PaperSource,
    ) -> IngestResult:
        """Ingest a batch of papers with duplicate checking.

        Args:
            papers_data: List of normalized paper data dictionaries.
            organization_id: Organization UUID.
            source: Paper source for duplicate checking by source_id.

        Returns:
            IngestResult with counts of created/skipped papers.
        """
        created = 0
        skipped = 0
        errors: list[str] = []

        for paper_data in papers_data:
            try:
                if await self._paper_exists(paper_data, organization_id, source):
                    skipped += 1
                    continue

                await self._create_paper_from_data(paper_data, organization_id)
                created += 1
            except Exception as e:
                title = paper_data.get("title", "unknown")[:50]
                errors.append(f"Error importing '{title}': {e}")

        await self.db.commit()

        return IngestResult(
            papers_created=created,
            papers_updated=0,
            papers_skipped=skipped,
            errors=errors,
        )

    async def _paper_exists(
        self,
        paper_data: dict,
        organization_id: UUID,
        source: PaperSource,
    ) -> bool:
        """Check if paper already exists by DOI or source_id.

        Args:
            paper_data: Paper data dictionary.
            organization_id: Organization UUID.
            source: Paper source for source_id lookup.

        Returns:
            True if paper already exists.
        """
        doi = paper_data.get("doi")
        if doi:
            existing = await self.get_paper_by_doi(doi, organization_id)
            if existing:
                return True

        source_id = paper_data.get("source_id")
        if source_id:
            existing = await self._get_paper_by_source(source, source_id, organization_id)
            if existing:
                return True

        return False

    async def ingest_from_pdf(
        self,
        file_content: bytes,
        filename: str,
        organization_id: UUID,
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

        paper = await self._create_paper_from_data(paper_data, organization_id)

        # Store pdf_path on the paper
        paper.pdf_path = extracted["pdf_path"]
        if extracted.get("full_text"):
            paper.full_text = extracted["full_text"]

        await self.db.commit()
        return paper

    async def _get_paper_by_source(
        self, source: PaperSource, source_id: str, organization_id: UUID
    ) -> Paper | None:
        """Get paper by source and source_id within organization.

        Args:
            source: Paper source (PUBMED, ARXIV, etc.).
            source_id: Source-specific identifier.
            organization_id: Organization UUID for tenant isolation.

        Returns:
            Paper or None if not found.
        """
        result = await self.db.execute(
            select(Paper).where(
                Paper.source == source,
                Paper.source_id == source_id,
                Paper.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def _create_paper_from_data(
        self, data: dict, organization_id: UUID
    ) -> Paper:
        """Create paper and authors from normalized API data.

        Args:
            data: Normalized paper data from API client.
            organization_id: Organization UUID.

        Returns:
            Created Paper object.
        """
        # Parse publication date
        pub_date = None
        if data.get("publication_date"):
            try:
                pub_date = datetime.fromisoformat(data["publication_date"])
            except ValueError:
                pass

        # Create paper
        paper = Paper(
            organization_id=organization_id,
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
            raise NotFoundError("Paper", "id", str(paper_id))

        # Generate pitch using LLM
        pitch_generator = PitchGenerator()
        pitch = await pitch_generator.generate(
            title=paper.title,
            abstract=paper.abstract,
            keywords=paper.keywords,
        )

        # Update paper with pitch
        paper.one_line_pitch = pitch
        await self.db.commit()
        await self.db.refresh(paper)

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
            raise NotFoundError("Paper", "id", str(paper_id))

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
        await self.db.commit()
        await self.db.refresh(paper)

        return paper
