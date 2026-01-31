"""FastAPI router for export endpoints."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser
from paper_scraper.core.database import get_db
from paper_scraper.modules.export.schemas import ExportFormat
from paper_scraper.modules.export.service import ExportService

router = APIRouter()


def get_export_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ExportService:
    """Dependency to get export service instance."""
    return ExportService(db)


@router.get(
    "/csv",
    summary="Export papers to CSV",
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
    csv_content, count = await export_service.export_csv(
        organization_id=current_user.organization_id,
        paper_ids=paper_ids,
        include_scores=include_scores,
        include_authors=include_authors,
    )

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"papers_export_{timestamp}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Paper-Count": str(count),
        },
    )


@router.get(
    "/bibtex",
    summary="Export papers to BibTeX",
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
    bibtex_content, count = await export_service.export_bibtex(
        organization_id=current_user.organization_id,
        paper_ids=paper_ids,
        include_abstract=include_abstract,
    )

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"papers_export_{timestamp}.bib"

    return Response(
        content=bibtex_content,
        media_type="application/x-bibtex",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Paper-Count": str(count),
        },
    )


@router.get(
    "/pdf",
    summary="Export papers to PDF",
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
    pdf_content, count = await export_service.export_pdf(
        organization_id=current_user.organization_id,
        paper_ids=paper_ids,
        include_scores=include_scores,
        include_abstract=include_abstract,
    )

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"papers_report_{timestamp}.txt"  # Using .txt for now

    return Response(
        content=pdf_content,
        media_type="text/plain",  # Would be application/pdf with proper library
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Paper-Count": str(count),
        },
    )


@router.post(
    "/batch",
    summary="Batch export papers",
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
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    if format == ExportFormat.CSV:
        content, count = await export_service.export_csv(
            organization_id=current_user.organization_id,
            paper_ids=paper_ids,
            include_scores=include_scores,
            include_authors=include_authors,
        )
        return Response(
            content=content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="papers_export_{timestamp}.csv"',
                "X-Paper-Count": str(count),
            },
        )

    elif format == ExportFormat.BIBTEX:
        content, count = await export_service.export_bibtex(
            organization_id=current_user.organization_id,
            paper_ids=paper_ids,
        )
        return Response(
            content=content,
            media_type="application/x-bibtex",
            headers={
                "Content-Disposition": f'attachment; filename="papers_export_{timestamp}.bib"',
                "X-Paper-Count": str(count),
            },
        )

    else:  # PDF
        content, count = await export_service.export_pdf(
            organization_id=current_user.organization_id,
            paper_ids=paper_ids,
            include_scores=include_scores,
        )
        return Response(
            content=content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f'attachment; filename="papers_report_{timestamp}.txt"',
                "X-Paper-Count": str(count),
            },
        )
