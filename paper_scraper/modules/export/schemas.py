"""Pydantic schemas for export module."""

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ExportFormat(str, Enum):
    """Supported export formats."""

    CSV = "csv"
    PDF = "pdf"
    BIBTEX = "bibtex"


class ExportRequest(BaseModel):
    """Request to export papers."""

    paper_ids: list[UUID] | None = Field(
        default=None,
        description="Specific paper IDs to export. If None, exports all papers.",
    )
    format: ExportFormat = Field(default=ExportFormat.CSV)
    include_scores: bool = Field(
        default=True, description="Include scoring data in export"
    )
    include_authors: bool = Field(default=True, description="Include author data")


class ExportResponse(BaseModel):
    """Response for export operation."""

    filename: str
    content_type: str
    paper_count: int


class BibTeXOptions(BaseModel):
    """Options for BibTeX export."""

    citation_key_format: str = Field(
        default="author_year",
        description="Format for citation keys: 'author_year', 'doi', 'custom'",
    )
    include_abstract: bool = Field(default=True)
    include_keywords: bool = Field(default=True)
    include_url: bool = Field(default=True)


class CSVOptions(BaseModel):
    """Options for CSV export."""

    delimiter: str = Field(default=",")
    include_header: bool = Field(default=True)
    columns: list[str] | None = Field(
        default=None,
        description="Specific columns to include. If None, includes all.",
    )


class PDFOptions(BaseModel):
    """Options for PDF export."""

    include_scores_chart: bool = Field(default=True)
    include_abstract: bool = Field(default=True)
    page_size: str = Field(default="A4")
