"""FastAPI router for export endpoints."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, require_permission
from paper_scraper.core.permissions import Permission
from paper_scraper.core.database import get_db
from paper_scraper.modules.export.schemas import ExportFormat
from paper_scraper.modules.export.service import ExportService

router = APIRouter()

# Format configuration: media_type, file_extension
FORMAT_CONFIG = {
    ExportFormat.CSV: ("text/csv", "csv"),
    ExportFormat.BIBTEX: ("application/x-bibtex", "bib"),
    ExportFormat.PDF: ("text/plain", "txt"),  # Would be application/pdf with proper library
}


def _create_export_response(
    content: str | bytes,
    format: ExportFormat,
    count: int,
    filename_prefix: str = "papers_export",
) -> Response:
    """Create a standardized export response."""
    media_type, extension = FORMAT_CONFIG[format]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.{extension}"

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Paper-Count": str(count),
        },
    )


def get_export_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ExportService:
    """Dependency to get export service instance."""
    return ExportService(db)


@router.get(
    "/csv",
    summary="Export papers to CSV",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def export_csv(
    current_user: CurrentUser,
    export_service: Annotated[ExportService, Depends(get_export_service)],
    paper_ids: list[UUID] | None = Query(default=None),
    include_scores: bool = Query(default=True),
    include_authors: bool = Query(default=True),
) -> Response:
    """Export papers to CSV format.

    Returns a CSV file containing paper metadata, optionally with
    scoring data and author information.
    """
    content, count = await export_service.export_csv(
        organization_id=current_user.organization_id,
        paper_ids=paper_ids,
        include_scores=include_scores,
        include_authors=include_authors,
    )
    return _create_export_response(content, ExportFormat.CSV, count)


@router.get(
    "/bibtex",
    summary="Export papers to BibTeX",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def export_bibtex(
    current_user: CurrentUser,
    export_service: Annotated[ExportService, Depends(get_export_service)],
    paper_ids: list[UUID] | None = Query(default=None),
    include_abstract: bool = Query(default=True),
) -> Response:
    """Export papers to BibTeX format.

    Returns a BibTeX file suitable for use with LaTeX and
    reference management software.
    """
    content, count = await export_service.export_bibtex(
        organization_id=current_user.organization_id,
        paper_ids=paper_ids,
        include_abstract=include_abstract,
    )
    return _create_export_response(content, ExportFormat.BIBTEX, count)


@router.get(
    "/pdf",
    summary="Export papers to PDF",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def export_pdf(
    current_user: CurrentUser,
    export_service: Annotated[ExportService, Depends(get_export_service)],
    paper_ids: list[UUID] | None = Query(default=None),
    include_scores: bool = Query(default=True),
    include_abstract: bool = Query(default=True),
) -> Response:
    """Export papers to PDF report format.

    Returns a PDF document containing paper details,
    optionally with scoring information and abstracts.
    """
    content, count = await export_service.export_pdf(
        organization_id=current_user.organization_id,
        paper_ids=paper_ids,
        include_scores=include_scores,
        include_abstract=include_abstract,
    )
    return _create_export_response(content, ExportFormat.PDF, count, "papers_report")


@router.post(
    "/batch",
    summary="Batch export papers",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def batch_export(
    current_user: CurrentUser,
    export_service: Annotated[ExportService, Depends(get_export_service)],
    paper_ids: list[UUID],
    format: ExportFormat = Query(default=ExportFormat.CSV),
    include_scores: bool = Query(default=True),
    include_authors: bool = Query(default=True),
) -> Response:
    """Batch export specific papers in the requested format."""
    org_id = current_user.organization_id

    if format == ExportFormat.CSV:
        content, count = await export_service.export_csv(
            organization_id=org_id,
            paper_ids=paper_ids,
            include_scores=include_scores,
            include_authors=include_authors,
        )
        return _create_export_response(content, format, count)

    if format == ExportFormat.BIBTEX:
        content, count = await export_service.export_bibtex(
            organization_id=org_id,
            paper_ids=paper_ids,
        )
        return _create_export_response(content, format, count)

    # PDF format
    content, count = await export_service.export_pdf(
        organization_id=org_id,
        paper_ids=paper_ids,
        include_scores=include_scores,
    )
    return _create_export_response(content, format, count, "papers_report")
