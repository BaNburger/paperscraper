"""Export service for CSV, PDF, and BibTeX generation."""

import csv
import io
import json
import re
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from paper_scraper.core.csv_utils import sanitize_csv_field
from paper_scraper.modules.papers.models import Paper, PaperAuthor
from paper_scraper.modules.scoring.models import PaperScore


def _get_sorted_author_names(paper: Paper) -> list[str]:
    """Get author names sorted by position."""
    sorted_authors = sorted(paper.authors, key=lambda x: x.position)
    return [author.author.name for author in sorted_authors]


class ExportService:
    """Service for exporting papers in various formats."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize export service."""
        self.db = db

    async def _get_papers(
        self,
        organization_id: UUID,
        paper_ids: list[UUID] | None = None,
        include_authors: bool = True,
    ) -> list[Paper]:
        """Fetch papers for export."""
        query = select(Paper).where(Paper.organization_id == organization_id)

        if paper_ids:
            query = query.where(Paper.id.in_(paper_ids))

        if include_authors:
            query = query.options(selectinload(Paper.authors).selectinload(PaperAuthor.author))

        query = query.order_by(Paper.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _get_scores(
        self, organization_id: UUID, paper_ids: list[UUID]
    ) -> dict[UUID, PaperScore]:
        """Get latest scores for papers."""
        if not paper_ids:
            return {}

        # Get latest score per paper using a subquery
        result = await self.db.execute(
            select(PaperScore)
            .where(
                PaperScore.organization_id == organization_id,
                PaperScore.paper_id.in_(paper_ids),
            )
            .order_by(PaperScore.created_at.desc())
        )

        scores: dict[UUID, PaperScore] = {}
        for score in result.scalars().all():
            if score.paper_id not in scores:
                scores[score.paper_id] = score

        return scores

    async def export_csv(
        self,
        organization_id: UUID,
        paper_ids: list[UUID] | None = None,
        include_scores: bool = True,
        include_authors: bool = True,
    ) -> tuple[str, int]:
        """Export papers to CSV format.

        Returns:
            Tuple of (csv_content, paper_count)
        """
        papers = await self._get_papers(organization_id, paper_ids, include_authors)

        if not papers:
            return "", 0

        scores = {}
        if include_scores:
            scores = await self._get_scores(
                organization_id, [p.id for p in papers]
            )

        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        headers = [
            "ID",
            "DOI",
            "Title",
            "Abstract",
            "Source",
            "Journal",
            "Publication Date",
            "Keywords",
        ]
        if include_authors:
            headers.append("Authors")
        if include_scores:
            headers.extend([
                "Overall Score",
                "Novelty",
                "IP Potential",
                "Marketability",
                "Feasibility",
                "Commercialization",
            ])
        headers.extend(["Created At", "Has PDF", "Has Embedding"])

        writer.writerow(headers)

        # Data rows — sanitize user-controlled text to prevent CSV injection
        for paper in papers:
            row = [
                str(paper.id),
                sanitize_csv_field(paper.doi or ""),
                sanitize_csv_field(paper.title),
                sanitize_csv_field(paper.abstract or ""),
                paper.source.value,
                sanitize_csv_field(paper.journal or ""),
                paper.publication_date.isoformat() if paper.publication_date else "",
                sanitize_csv_field("; ".join(paper.keywords) if paper.keywords else ""),
            ]

            if include_authors:
                row.append(sanitize_csv_field("; ".join(_get_sorted_author_names(paper))))

            if include_scores:
                score = scores.get(paper.id)
                if score:
                    row.extend([
                        f"{score.overall_score:.2f}",
                        f"{score.novelty:.2f}",
                        f"{score.ip_potential:.2f}",
                        f"{score.marketability:.2f}",
                        f"{score.feasibility:.2f}",
                        f"{score.commercialization:.2f}",
                    ])
                else:
                    row.extend([""] * 6)

            row.extend([
                paper.created_at.isoformat(),
                "Yes" if paper.has_pdf else "No",
                "Yes" if paper.has_embedding else "No",
            ])

            writer.writerow(row)

        return output.getvalue(), len(papers)

    async def export_bibtex(
        self,
        organization_id: UUID,
        paper_ids: list[UUID] | None = None,
        include_abstract: bool = True,
    ) -> tuple[str, int]:
        """Export papers to BibTeX format.

        Returns:
            Tuple of (bibtex_content, paper_count)
        """
        papers = await self._get_papers(organization_id, paper_ids, include_authors=True)

        if not papers:
            return "", 0

        entries = []
        for paper in papers:
            entry = self._generate_bibtex_entry(paper, include_abstract)
            entries.append(entry)

        return "\n\n".join(entries), len(papers)

    async def export_ris(
        self,
        organization_id: UUID,
        paper_ids: list[UUID] | None = None,
        include_abstract: bool = True,
    ) -> tuple[str, int]:
        """Export papers to RIS format."""
        papers = await self._get_papers(organization_id, paper_ids, include_authors=True)
        if not papers:
            return "", 0

        lines: list[str] = []
        for paper in papers:
            lines.append("TY  - JOUR")
            lines.append(f"ID  - {paper.id}")
            lines.append(f"TI  - {paper.title}")
            for author in _get_sorted_author_names(paper):
                lines.append(f"AU  - {author}")
            if paper.journal:
                lines.append(f"JO  - {paper.journal}")
            if paper.publication_date:
                date_str = paper.publication_date.strftime("%Y/%m/%d")
                lines.append(f"PY  - {date_str}")
                lines.append(f"DA  - {date_str}")
            if paper.volume:
                lines.append(f"VL  - {paper.volume}")
            if paper.issue:
                lines.append(f"IS  - {paper.issue}")
            if paper.pages:
                lines.append(f"SP  - {paper.pages}")
            if paper.doi:
                lines.append(f"DO  - {paper.doi}")
            if include_abstract and paper.abstract:
                lines.append(f"AB  - {paper.abstract}")
            for keyword in paper.keywords or []:
                lines.append(f"KW  - {keyword}")
            lines.append("ER  - ")
            lines.append("")

        # RIS tools generally accept LF, no need to force CRLF.
        return "\n".join(lines), len(papers)

    async def export_csljson(
        self,
        organization_id: UUID,
        paper_ids: list[UUID] | None = None,
        include_abstract: bool = True,
    ) -> tuple[str, int]:
        """Export papers as CSL JSON array."""
        papers = await self._get_papers(organization_id, paper_ids, include_authors=True)
        if not papers:
            return "[]", 0

        entries: list[dict] = []
        for paper in papers:
            authors = []
            for author_name in _get_sorted_author_names(paper):
                parts = author_name.split()
                if len(parts) > 1:
                    authors.append({"family": parts[-1], "given": " ".join(parts[:-1])})
                else:
                    authors.append({"family": author_name})

            issued = None
            if paper.publication_date:
                date_parts = [paper.publication_date.year]
                if paper.publication_date.month:
                    date_parts.append(paper.publication_date.month)
                if paper.publication_date.day:
                    date_parts.append(paper.publication_date.day)
                issued = {"date-parts": [date_parts]}

            item = {
                "id": str(paper.id),
                "type": "article-journal",
                "title": paper.title,
                "author": authors,
            }
            if paper.doi:
                item["DOI"] = paper.doi
            if paper.journal:
                item["container-title"] = paper.journal
            if issued:
                item["issued"] = issued
            if paper.volume:
                item["volume"] = paper.volume
            if paper.issue:
                item["issue"] = paper.issue
            if paper.pages:
                item["page"] = paper.pages
            if include_abstract and paper.abstract:
                item["abstract"] = paper.abstract
            if paper.keywords:
                item["keyword"] = ", ".join(paper.keywords)

            entries.append(item)

        return json.dumps(entries, ensure_ascii=False, indent=2), len(entries)

    def _generate_bibtex_entry(self, paper: Paper, include_abstract: bool) -> str:
        """Generate a single BibTeX entry."""
        author_names = _get_sorted_author_names(paper) if paper.authors else []

        # Generate citation key from first author's last name and year
        first_author_key = ""
        if author_names:
            last_name = author_names[0].split()[-1]
            first_author_key = re.sub(r"[^a-zA-Z]", "", last_name).lower()

        year = str(paper.publication_date.year) if paper.publication_date else ""
        citation_key = f"{first_author_key}{year}" if first_author_key else str(paper.id)[:8]

        # Build entry
        lines = [f"@article{{{citation_key},"]

        # Title
        lines.append(f"  title = {{{self._escape_bibtex(paper.title)}}},")

        # Authors
        if author_names:
            lines.append(f"  author = {{{' and '.join(author_names)}}},")

        # Year and date
        if paper.publication_date:
            lines.append(f"  year = {{{paper.publication_date.year}}},")
            lines.append(f"  month = {{{paper.publication_date.strftime('%b').lower()}}},")

        # Journal
        if paper.journal:
            lines.append(f"  journal = {{{self._escape_bibtex(paper.journal)}}},")

        # Volume, issue, pages
        if paper.volume:
            lines.append(f"  volume = {{{paper.volume}}},")
        if paper.issue:
            lines.append(f"  number = {{{paper.issue}}},")
        if paper.pages:
            lines.append(f"  pages = {{{paper.pages}}},")

        # DOI
        if paper.doi:
            lines.append(f"  doi = {{{paper.doi}}},")

        # Abstract
        if include_abstract and paper.abstract:
            lines.append(f"  abstract = {{{self._escape_bibtex(paper.abstract)}}},")

        # Keywords
        if paper.keywords:
            lines.append(f"  keywords = {{{', '.join(paper.keywords)}}},")

        lines.append("}")

        return "\n".join(lines)

    def _escape_bibtex(self, text: str) -> str:
        """Escape special BibTeX characters."""
        if not text:
            return ""

        # Replace special characters
        replacements = {
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\textasciicircum{}",
        }

        for char, replacement in replacements.items():
            text = text.replace(char, replacement)

        return text

    async def export_pdf(
        self,
        organization_id: UUID,
        paper_ids: list[UUID] | None = None,
        include_scores: bool = True,
        include_abstract: bool = True,
    ) -> tuple[bytes, int]:
        """Export papers to PDF format.

        Returns:
            Tuple of (pdf_bytes, paper_count)

        Note: This generates a simple text-based PDF. For production,
        consider using a library like WeasyPrint or ReportLab.
        """
        papers = await self._get_papers(organization_id, paper_ids, include_authors=True)

        if not papers:
            return b"", 0

        scores = {}
        if include_scores:
            scores = await self._get_scores(
                organization_id, [p.id for p in papers]
            )

        # Generate PDF content using simple text format
        # In production, use ReportLab or WeasyPrint for proper PDF generation
        pdf_content = self._generate_pdf_content(papers, scores, include_abstract)

        return pdf_content, len(papers)

    def _generate_pdf_content(
        self,
        papers: list[Paper],
        scores: dict[UUID, PaperScore],
        include_abstract: bool,
    ) -> bytes:
        """Generate PDF content.

        This is a simplified implementation that generates HTML-like content.
        For production, integrate with a proper PDF library.
        """
        # For now, we'll generate a simple text report
        # In a real implementation, use ReportLab or WeasyPrint
        lines = [
            "=" * 80,
            "PAPER EXPORT REPORT",
            f"Generated: {datetime.now(UTC).isoformat()}",
            f"Total Papers: {len(papers)}",
            "=" * 80,
            "",
        ]

        for i, paper in enumerate(papers, 1):
            lines.extend([
                f"[{i}] {paper.title}",
                "-" * 60,
            ])

            if paper.doi:
                lines.append(f"DOI: {paper.doi}")

            if paper.authors:
                lines.append(f"Authors: {', '.join(_get_sorted_author_names(paper))}")

            if paper.journal:
                lines.append(f"Journal: {paper.journal}")

            if paper.publication_date:
                lines.append(f"Published: {paper.publication_date.strftime('%Y-%m-%d')}")

            lines.append(f"Source: {paper.source.value}")

            if include_abstract and paper.abstract:
                lines.extend([
                    "",
                    "Abstract:",
                    paper.abstract[:500] + ("..." if len(paper.abstract) > 500 else ""),
                ])

            score = scores.get(paper.id)
            if score:
                lines.extend([
                    "",
                    "Scores:",
                    f"  Overall: {score.overall_score:.1f}/10",
                    f"  Novelty: {score.novelty:.1f}/10",
                    f"  IP Potential: {score.ip_potential:.1f}/10",
                    f"  Marketability: {score.marketability:.1f}/10",
                    f"  Feasibility: {score.feasibility:.1f}/10",
                    f"  Commercialization: {score.commercialization:.1f}/10",
                ])

            lines.extend(["", ""])

        return "\n".join(lines).encode("utf-8")
