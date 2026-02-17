"""FastAPI router for library-first features."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, require_permission
from paper_scraper.core.config import settings
from paper_scraper.core.database import get_db
from paper_scraper.core.permissions import Permission
from paper_scraper.modules.library.schemas import (
    CollectionPaperResponse,
    GenerateHighlightsRequest,
    HydrateFullTextResponse,
    HighlightCreate,
    HighlightUpdate,
    LibraryCollectionCreate,
    LibraryCollectionListResponse,
    LibraryCollectionResponse,
    LibraryCollectionUpdate,
    PaperHighlightListResponse,
    PaperHighlightResponse,
    PaperTagListResponse,
    PaperTagResponse,
    ReaderResponse,
    TagCreate,
)
from paper_scraper.modules.library.service import LibraryService

def require_library_feature_flag() -> None:
    """Gate Library V2 endpoints behind feature flag."""
    if not settings.LIBRARY_V2_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Library V2 feature is disabled",
        )


router = APIRouter(dependencies=[Depends(require_library_feature_flag)])


def get_library_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LibraryService:
    """Dependency provider for LibraryService."""
    return LibraryService(db)


@router.get(
    "/collections",
    response_model=LibraryCollectionListResponse,
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def list_collections(
    current_user: CurrentUser,
    service: Annotated[LibraryService, Depends(get_library_service)],
) -> LibraryCollectionListResponse:
    """List hierarchical library collections."""
    return await service.list_collections(current_user.organization_id)


@router.post(
    "/collections",
    response_model=LibraryCollectionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def create_collection(
    data: LibraryCollectionCreate,
    current_user: CurrentUser,
    service: Annotated[LibraryService, Depends(get_library_service)],
) -> LibraryCollectionResponse:
    """Create a library collection."""
    created = await service.create_collection(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        data=data,
    )
    return LibraryCollectionResponse.model_validate(created)


@router.patch(
    "/collections/{collection_id}",
    response_model=LibraryCollectionResponse,
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def update_collection(
    collection_id: UUID,
    data: LibraryCollectionUpdate,
    current_user: CurrentUser,
    service: Annotated[LibraryService, Depends(get_library_service)],
) -> LibraryCollectionResponse:
    """Update a library collection."""
    updated = await service.update_collection(
        collection_id=collection_id,
        organization_id=current_user.organization_id,
        data=data,
    )
    return LibraryCollectionResponse.model_validate(updated)


@router.delete(
    "/collections/{collection_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def delete_collection(
    collection_id: UUID,
    current_user: CurrentUser,
    service: Annotated[LibraryService, Depends(get_library_service)],
) -> None:
    """Delete a collection."""
    await service.delete_collection(collection_id, current_user.organization_id)


@router.post(
    "/collections/{collection_id}/papers/{paper_id}",
    response_model=CollectionPaperResponse,
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def add_paper_to_collection(
    collection_id: UUID,
    paper_id: UUID,
    current_user: CurrentUser,
    service: Annotated[LibraryService, Depends(get_library_service)],
) -> CollectionPaperResponse:
    """Add paper to collection."""
    await service.add_paper_to_collection(
        collection_id=collection_id,
        paper_id=paper_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )
    return CollectionPaperResponse(collection_id=collection_id, paper_id=paper_id, added=True)


@router.delete(
    "/collections/{collection_id}/papers/{paper_id}",
    response_model=CollectionPaperResponse,
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def remove_paper_from_collection(
    collection_id: UUID,
    paper_id: UUID,
    current_user: CurrentUser,
    service: Annotated[LibraryService, Depends(get_library_service)],
) -> CollectionPaperResponse:
    """Remove paper from collection."""
    await service.remove_paper_from_collection(
        collection_id=collection_id,
        paper_id=paper_id,
        organization_id=current_user.organization_id,
    )
    return CollectionPaperResponse(collection_id=collection_id, paper_id=paper_id, added=False)


@router.get(
    "/papers/{paper_id}/reader",
    response_model=ReaderResponse,
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def get_reader(
    paper_id: UUID,
    current_user: CurrentUser,
    service: Annotated[LibraryService, Depends(get_library_service)],
) -> ReaderResponse:
    """Get reader payload with chunked text for a paper."""
    return await service.get_reader_data(
        paper_id=paper_id,
        organization_id=current_user.organization_id,
    )


@router.post(
    "/papers/{paper_id}/hydrate-fulltext",
    response_model=HydrateFullTextResponse,
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def hydrate_fulltext(
    paper_id: UUID,
    current_user: CurrentUser,
    service: Annotated[LibraryService, Depends(get_library_service)],
) -> HydrateFullTextResponse:
    """Hydrate and chunk full text from available sources."""
    return await service.hydrate_full_text(
        paper_id=paper_id,
        organization_id=current_user.organization_id,
    )


@router.get(
    "/papers/{paper_id}/highlights",
    response_model=PaperHighlightListResponse,
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def list_highlights(
    paper_id: UUID,
    current_user: CurrentUser,
    service: Annotated[LibraryService, Depends(get_library_service)],
    include_inactive: bool = Query(default=False),
) -> PaperHighlightListResponse:
    """List highlights for a paper."""
    items = await service.highlight_service.list_highlights(
        paper_id=paper_id,
        organization_id=current_user.organization_id,
        active_only=not include_inactive,
    )
    payload = [PaperHighlightResponse.model_validate(item) for item in items]
    return PaperHighlightListResponse(items=payload, total=len(payload))


@router.post(
    "/papers/{paper_id}/highlights",
    response_model=PaperHighlightResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def create_highlight(
    paper_id: UUID,
    data: HighlightCreate,
    current_user: CurrentUser,
    service: Annotated[LibraryService, Depends(get_library_service)],
) -> PaperHighlightResponse:
    """Create manual highlight."""
    created = await service.create_manual_highlight(
        paper_id=paper_id,
        organization_id=current_user.organization_id,
        created_by=current_user.id,
        chunk_id=data.chunk_id,
        chunk_ref=data.chunk_ref,
        quote=data.quote,
        insight_summary=data.insight_summary,
        confidence=data.confidence,
    )
    return PaperHighlightResponse.model_validate(created)


@router.post(
    "/papers/{paper_id}/highlights/generate",
    response_model=PaperHighlightListResponse,
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def generate_highlights(
    paper_id: UUID,
    data: GenerateHighlightsRequest,
    current_user: CurrentUser,
    service: Annotated[LibraryService, Depends(get_library_service)],
) -> PaperHighlightListResponse:
    """Generate AI highlights for a paper."""
    items = await service.generate_highlights(
        paper_id=paper_id,
        organization_id=current_user.organization_id,
        created_by=current_user.id,
        target_count=data.target_count,
    )
    payload = [PaperHighlightResponse.model_validate(item) for item in items]
    return PaperHighlightListResponse(items=payload, total=len(payload))


@router.patch(
    "/papers/{paper_id}/highlights/{highlight_id}",
    response_model=PaperHighlightResponse,
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def update_highlight(
    paper_id: UUID,
    highlight_id: UUID,
    data: HighlightUpdate,
    current_user: CurrentUser,
    service: Annotated[LibraryService, Depends(get_library_service)],
) -> PaperHighlightResponse:
    """Update highlight fields."""
    updated = await service.highlight_service.update_highlight(
        highlight_id=highlight_id,
        paper_id=paper_id,
        organization_id=current_user.organization_id,
        quote=data.quote,
        insight_summary=data.insight_summary,
        confidence=data.confidence,
        is_active=data.is_active,
    )
    return PaperHighlightResponse.model_validate(updated)


@router.delete(
    "/papers/{paper_id}/highlights/{highlight_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def delete_highlight(
    paper_id: UUID,
    highlight_id: UUID,
    current_user: CurrentUser,
    service: Annotated[LibraryService, Depends(get_library_service)],
) -> None:
    """Delete highlight."""
    await service.highlight_service.delete_highlight(
        highlight_id=highlight_id,
        paper_id=paper_id,
        organization_id=current_user.organization_id,
    )


@router.get(
    "/tags",
    response_model=PaperTagListResponse,
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def list_tags(
    current_user: CurrentUser,
    service: Annotated[LibraryService, Depends(get_library_service)],
) -> PaperTagListResponse:
    """List tag usage across the organization."""
    return await service.list_tags(current_user.organization_id)


@router.post(
    "/papers/{paper_id}/tags",
    response_model=PaperTagResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def add_tag(
    paper_id: UUID,
    data: TagCreate,
    current_user: CurrentUser,
    service: Annotated[LibraryService, Depends(get_library_service)],
) -> PaperTagResponse:
    """Attach user-defined tag to a paper."""
    created = await service.add_tag(
        paper_id=paper_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        tag=data.tag,
    )
    return PaperTagResponse.model_validate(created)


@router.delete(
    "/papers/{paper_id}/tags/{tag}",
    response_model=dict[str, bool],
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def remove_tag(
    paper_id: UUID,
    tag: str,
    current_user: CurrentUser,
    service: Annotated[LibraryService, Depends(get_library_service)],
) -> dict[str, bool]:
    """Remove a user tag from a paper."""
    removed = await service.remove_tag(
        paper_id=paper_id,
        organization_id=current_user.organization_id,
        tag=tag,
    )
    return {"removed": removed}
