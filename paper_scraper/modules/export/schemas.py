"""Pydantic schemas for export module."""

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ExportFormat(str, Enum):
    """Supported export formats."""

    CSV = "csv"
    PDF = "pdf"
    BIBTEX = "bibtex"
    RIS = "ris"
    CSLJSON = "csljson"


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
