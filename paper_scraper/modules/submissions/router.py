"""FastAPI router for research submissions endpoints."""

import os
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, ManagerOrAdminUser
from paper_scraper.core.database import get_db
from paper_scraper.modules.papers.schemas import PaperResponse
from paper_scraper.modules.submissions.models import AttachmentType, SubmissionStatus
from paper_scraper.modules.submissions.schemas import (
    AttachmentResponse,
    SubmissionCreate,
    SubmissionDetail,
    SubmissionListResponse,
    SubmissionResponse,
    SubmissionReview,
    SubmissionScoreResponse,
    SubmissionUpdate,
)
from paper_scraper.modules.submissions.service import SubmissionService

router = APIRouter()

# Allowed MIME types with magic byte signatures for validation
_ALLOWED_MIME_TYPES: dict[str, bytes] = {
    "application/pdf": b"%PDF",
    "application/msword": b"\xd0\xcf\x11\xe0",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": b"PK",
    "application/vnd.ms-powerpoint": b"\xd0\xcf\x11\xe0",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": b"PK",
    "image/png": b"\x89PNG",
    "image/jpeg": b"\xff\xd8\xff",
}
_MAX_ATTACHMENT_SIZE = 50_000_000  # 50MB
_CHUNK_SIZE = 64 * 1024  # 64KB read chunks


def get_submission_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SubmissionService:
    """Dependency to get submission service instance."""
    return SubmissionService(db)


# =============================================================================
# Researcher Endpoints
# =============================================================================


@router.get(
    "/my",
    response_model=SubmissionListResponse,
    summary="List my submissions",
)
async def list_my_submissions(
    current_user: CurrentUser,
    service: Annotated[SubmissionService, Depends(get_submission_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: SubmissionStatus | None = Query(default=None, alias="status"),
) -> SubmissionListResponse:
    """List submissions created by the current user."""
    return await service.list_my_submissions(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
    )


@router.post(
    "/",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create submission",
)
async def create_submission(
    request: SubmissionCreate,
    current_user: CurrentUser,
    service: Annotated[SubmissionService, Depends(get_submission_service)],
) -> SubmissionResponse:
    """Create a new research submission as a draft."""
    submission = await service.create_submission(
        data=request,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
    )
    return submission  # type: ignore


@router.get(
    "/{submission_id}",
    response_model=SubmissionDetail,
    summary="Get submission",
)
async def get_submission(
    submission_id: UUID,
    current_user: CurrentUser,
    service: Annotated[SubmissionService, Depends(get_submission_service)],
) -> SubmissionDetail:
    """Get submission details including attachments and scores."""
    submission = await service.get_submission(
        submission_id=submission_id,
        organization_id=current_user.organization_id,
    )
    return submission  # type: ignore


@router.patch(
    "/{submission_id}",
    response_model=SubmissionResponse,
    summary="Update draft submission",
)
async def update_submission(
    submission_id: UUID,
    request: SubmissionUpdate,
    current_user: CurrentUser,
    service: Annotated[SubmissionService, Depends(get_submission_service)],
) -> SubmissionResponse:
    """Update a draft submission (own submissions only)."""
    submission = await service.update_submission(
        submission_id=submission_id,
        data=request,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
    )
    return submission  # type: ignore


@router.post(
    "/{submission_id}/submit",
    response_model=SubmissionResponse,
    summary="Submit for review",
)
async def submit_for_review(
    submission_id: UUID,
    current_user: CurrentUser,
    service: Annotated[SubmissionService, Depends(get_submission_service)],
) -> SubmissionResponse:
    """Submit a draft for TTO review."""
    submission = await service.submit_for_review(
        submission_id=submission_id,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
    )
    return submission  # type: ignore


@router.post(
    "/{submission_id}/attachments",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload attachment",
)
async def upload_attachment(
    submission_id: UUID,
    current_user: CurrentUser,
    service: Annotated[SubmissionService, Depends(get_submission_service)],
    file: UploadFile = File(...),
    attachment_type: AttachmentType = AttachmentType.PDF,
) -> AttachmentResponse:
    """Upload a file attachment to a submission.

    Supported formats: PDF, DOC, DOCX, PPT, PPTX, PNG, JPEG.
    Maximum file size: 50MB.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    # Validate MIME type from Content-Type header
    content_type = file.content_type or "application/octet-stream"
    if content_type not in _ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {content_type}. Allowed: PDF, DOC, DOCX, PPT, PPTX, PNG, JPEG",
        )

    # Read file in chunks to prevent memory DoS
    chunks: list[bytes] = []
    total_size = 0
    while True:
        chunk = await file.read(_CHUNK_SIZE)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > _MAX_ATTACHMENT_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File too large (max 50MB)",
            )
        chunks.append(chunk)

    content = b"".join(chunks)

    # Validate magic bytes match declared MIME type
    expected_magic = _ALLOWED_MIME_TYPES[content_type]
    if not content.startswith(expected_magic):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match declared MIME type",
        )

    # Sanitize filename: strip path components and prefix with UUID
    safe_filename = os.path.basename(file.filename)
    unique_prefix = uuid4().hex[:12]
    storage_filename = f"{unique_prefix}_{safe_filename}"
    file_path = f"submissions/{submission_id}/{storage_filename}"

    # TODO: Persist content to MinIO/S3 storage using file_path as key
    # For now, we record the intended storage path in the database

    attachment = await service.add_attachment(
        submission_id=submission_id,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        filename=safe_filename,
        file_path=file_path,
        file_size=total_size,
        mime_type=content_type,
        attachment_type=attachment_type,
    )
    return attachment  # type: ignore


# =============================================================================
# TTO Review Endpoints
# =============================================================================


@router.get(
    "/",
    response_model=SubmissionListResponse,
    summary="List all submissions (TTO)",
)
async def list_all_submissions(
    current_user: ManagerOrAdminUser,
    service: Annotated[SubmissionService, Depends(get_submission_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: SubmissionStatus | None = Query(default=None, alias="status"),
) -> SubmissionListResponse:
    """List all submissions in the organization (manager/admin only)."""
    return await service.list_all_submissions(
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
    )


@router.patch(
    "/{submission_id}/review",
    response_model=SubmissionResponse,
    summary="Review submission",
)
async def review_submission(
    submission_id: UUID,
    request: SubmissionReview,
    current_user: ManagerOrAdminUser,
    service: Annotated[SubmissionService, Depends(get_submission_service)],
) -> SubmissionResponse:
    """Approve or reject a submission (manager/admin only)."""
    submission = await service.review_submission(
        submission_id=submission_id,
        reviewer_id=current_user.id,
        organization_id=current_user.organization_id,
        decision=request.decision,
        notes=request.notes,
    )
    return submission  # type: ignore


@router.post(
    "/{submission_id}/analyze",
    response_model=SubmissionScoreResponse,
    summary="AI analysis",
)
async def analyze_submission(
    submission_id: UUID,
    current_user: ManagerOrAdminUser,
    service: Annotated[SubmissionService, Depends(get_submission_service)],
) -> SubmissionScoreResponse:
    """Run AI scoring analysis on a submission (manager/admin only)."""
    score = await service.analyze_submission(
        submission_id=submission_id,
        organization_id=current_user.organization_id,
    )
    return score  # type: ignore


@router.post(
    "/{submission_id}/convert",
    response_model=PaperResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Convert to paper",
)
async def convert_to_paper(
    submission_id: UUID,
    current_user: ManagerOrAdminUser,
    service: Annotated[SubmissionService, Depends(get_submission_service)],
) -> PaperResponse:
    """Convert a submission into a paper (manager/admin only)."""
    paper = await service.convert_to_paper(
        submission_id=submission_id,
        organization_id=current_user.organization_id,
    )
    return paper  # type: ignore
