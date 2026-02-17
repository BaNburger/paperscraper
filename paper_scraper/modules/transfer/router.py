"""FastAPI router for technology transfer endpoints."""

import asyncio
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, require_permission
from paper_scraper.core.database import get_db
from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.core.permissions import Permission
from paper_scraper.core.storage import get_storage_service
from paper_scraper.core.uploads import (
    build_storage_key,
    read_upload_content,
    sanitize_filename,
    validate_content_type,
    validate_magic_bytes,
)
from paper_scraper.modules.audit.models import AuditAction
from paper_scraper.modules.audit.service import AuditService
from paper_scraper.modules.transfer.models import TransferStage
from paper_scraper.modules.transfer.schemas import (
    ConversationCreate,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageFromTemplateCreate,
    MessageResponse,
    NextStepsResponse,
    ResourceCreate,
    ResourceResponse,
    TemplateCreate,
    TemplateResponse,
    TemplateUpdate,
)
from paper_scraper.modules.transfer.service import TransferService

logger = logging.getLogger(__name__)

# Allowed MIME types with magic byte signatures for validation
_ALLOWED_MIME_TYPES: dict[str, bytes | None] = {
    "application/pdf": b"%PDF",
    "application/msword": b"\xd0\xcf\x11\xe0",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": b"PK",
    "application/vnd.ms-powerpoint": b"\xd0\xcf\x11\xe0",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": b"PK",
    "image/png": b"\x89PNG",
    "image/jpeg": b"\xff\xd8\xff",
    "text/plain": None,  # No reliable magic bytes for text
    "text/csv": None,
}
_MAX_FILE_SIZE = 50_000_000  # 50MB

router = APIRouter()


def get_transfer_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TransferService:
    """Dependency to get transfer service instance."""
    return TransferService(db)


def get_audit_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuditService:
    return AuditService(db)


# =============================================================================
# Template Endpoints (must be before /{conversation_id} to avoid route conflicts)
# =============================================================================


@router.get(
    "/templates/",
    response_model=list[TemplateResponse],
    summary="List templates",
    dependencies=[Depends(require_permission(Permission.TRANSFER_READ))],
)
async def list_templates(
    current_user: CurrentUser,
    service: Annotated[TransferService, Depends(get_transfer_service)],
    stage: TransferStage | None = Query(default=None),
) -> list[TemplateResponse]:
    """List message templates for the organization."""
    return await service.list_templates(
        organization_id=current_user.organization_id,
        stage=stage,
    )


@router.post(
    "/templates/",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create template",
    dependencies=[Depends(require_permission(Permission.TRANSFER_MANAGE))],
)
async def create_template(
    data: TemplateCreate,
    current_user: CurrentUser,
    service: Annotated[TransferService, Depends(get_transfer_service)],
) -> TemplateResponse:
    """Create a new message template."""
    template = await service.create_template(
        organization_id=current_user.organization_id,
        data=data,
    )
    return TemplateResponse.model_validate(template)


@router.patch(
    "/templates/{template_id}",
    response_model=TemplateResponse,
    summary="Update template",
    dependencies=[Depends(require_permission(Permission.TRANSFER_MANAGE))],
)
async def update_template(
    template_id: UUID,
    data: TemplateUpdate,
    current_user: CurrentUser,
    service: Annotated[TransferService, Depends(get_transfer_service)],
) -> TemplateResponse:
    """Update a message template."""
    template = await service.update_template(
        template_id=template_id,
        organization_id=current_user.organization_id,
        data=data,
    )
    return TemplateResponse.model_validate(template)


@router.delete(
    "/templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete template",
    dependencies=[Depends(require_permission(Permission.TRANSFER_MANAGE))],
)
async def delete_template(
    template_id: UUID,
    current_user: CurrentUser,
    service: Annotated[TransferService, Depends(get_transfer_service)],
) -> None:
    """Delete a message template."""
    await service.delete_template(
        template_id=template_id,
        organization_id=current_user.organization_id,
    )


# =============================================================================
# Conversation Endpoints
# =============================================================================


@router.get(
    "/",
    response_model=ConversationListResponse,
    summary="List conversations",
    dependencies=[Depends(require_permission(Permission.TRANSFER_READ))],
)
async def list_conversations(
    current_user: CurrentUser,
    service: Annotated[TransferService, Depends(get_transfer_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    stage: TransferStage | None = Query(default=None),
    search: str | None = Query(default=None),
) -> ConversationListResponse:
    """List all transfer conversations for the organization."""
    return await service.list_conversations(
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        stage=stage,
        search=search,
    )


@router.post(
    "/",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create conversation",
    dependencies=[Depends(require_permission(Permission.TRANSFER_MANAGE))],
)
async def create_conversation(
    request: Request,
    data: ConversationCreate,
    current_user: CurrentUser,
    service: Annotated[TransferService, Depends(get_transfer_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> ConversationResponse:
    """Create a new transfer conversation."""
    conv = await service.create_conversation(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        data=data,
    )
    await audit.log(
        action=AuditAction.TRANSFER_CREATE,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_type="transfer_conversation",
        resource_id=conv.id,
        details={"title": conv.title, "type": conv.type.value},
        request=request,
    )
    return ConversationResponse(
        id=conv.id,
        organization_id=conv.organization_id,
        paper_id=conv.paper_id,
        researcher_id=conv.researcher_id,
        type=conv.type,
        stage=conv.stage,
        title=conv.title,
        created_by=conv.created_by,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=0,
        resource_count=0,
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetailResponse,
    summary="Get conversation detail",
    dependencies=[Depends(require_permission(Permission.TRANSFER_READ))],
)
async def get_conversation_detail(
    conversation_id: UUID,
    current_user: CurrentUser,
    service: Annotated[TransferService, Depends(get_transfer_service)],
) -> ConversationDetailResponse:
    """Get full conversation detail with messages, resources, and stage history."""
    detail = await service.get_conversation_detail(
        conversation_id=conversation_id,
        organization_id=current_user.organization_id,
    )
    if not detail:
        raise NotFoundError("TransferConversation", str(conversation_id))
    return detail


@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Update conversation stage",
    dependencies=[Depends(require_permission(Permission.TRANSFER_MANAGE))],
)
async def update_conversation_stage(
    request: Request,
    conversation_id: UUID,
    data: ConversationUpdate,
    current_user: CurrentUser,
    service: Annotated[TransferService, Depends(get_transfer_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> ConversationResponse:
    """Update the stage of a transfer conversation."""
    conv = await service.update_conversation_stage(
        conversation_id=conversation_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        data=data,
    )
    await audit.log(
        action=AuditAction.TRANSFER_STAGE_CHANGE,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_type="transfer_conversation",
        resource_id=conv.id,
        details={"new_stage": conv.stage.value},
        request=request,
    )
    msg_count = await service.count_messages(conv.id)
    res_count = await service.count_resources(conv.id)
    return ConversationResponse(
        id=conv.id,
        organization_id=conv.organization_id,
        paper_id=conv.paper_id,
        researcher_id=conv.researcher_id,
        type=conv.type,
        stage=conv.stage,
        title=conv.title,
        created_by=conv.created_by,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=msg_count,
        resource_count=res_count,
    )


# =============================================================================
# Message Endpoints
# =============================================================================


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add message",
    dependencies=[Depends(require_permission(Permission.TRANSFER_MANAGE))],
)
async def add_message(
    conversation_id: UUID,
    data: MessageCreate,
    current_user: CurrentUser,
    service: Annotated[TransferService, Depends(get_transfer_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> MessageResponse:
    """Add a message to a conversation."""
    message = await service.add_message(
        conversation_id=conversation_id,
        organization_id=current_user.organization_id,
        sender_id=current_user.id,
        data=data,
    )
    await audit.log(
        action=AuditAction.TRANSFER_MESSAGE_SEND,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_type="transfer_message",
        resource_id=message.id,
        details={"conversation_id": str(conversation_id)},
    )
    return MessageResponse(
        id=message.id,
        conversation_id=message.conversation_id,
        sender_id=message.sender_id,
        content=message.content,
        mentions=message.mentions or [],
        created_at=message.created_at,
        sender_name=current_user.full_name,
    )


@router.post(
    "/{conversation_id}/messages/from-template",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add message from template",
    dependencies=[Depends(require_permission(Permission.TRANSFER_MANAGE))],
)
async def add_message_from_template(
    conversation_id: UUID,
    data: MessageFromTemplateCreate,
    current_user: CurrentUser,
    service: Annotated[TransferService, Depends(get_transfer_service)],
) -> MessageResponse:
    """Add a message to a conversation using a template."""
    message = await service.add_message_from_template(
        conversation_id=conversation_id,
        organization_id=current_user.organization_id,
        sender_id=current_user.id,
        template_id=data.template_id,
        mentions=data.mentions,
    )
    return MessageResponse(
        id=message.id,
        conversation_id=message.conversation_id,
        sender_id=message.sender_id,
        content=message.content,
        mentions=message.mentions or [],
        created_at=message.created_at,
        sender_name=current_user.full_name,
    )


# =============================================================================
# Resource Endpoints
# =============================================================================


@router.post(
    "/{conversation_id}/resources",
    response_model=ResourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Attach resource",
    dependencies=[Depends(require_permission(Permission.TRANSFER_MANAGE))],
)
async def add_resource(
    conversation_id: UUID,
    data: ResourceCreate,
    current_user: CurrentUser,
    service: Annotated[TransferService, Depends(get_transfer_service)],
) -> ResourceResponse:
    """Attach a resource to a conversation."""
    resource = await service.add_resource(
        conversation_id=conversation_id,
        organization_id=current_user.organization_id,
        data=data,
    )
    return ResourceResponse.model_validate(resource)


@router.post(
    "/{conversation_id}/resources/upload",
    response_model=ResourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload resource file",
    dependencies=[Depends(require_permission(Permission.TRANSFER_MANAGE))],
)
async def upload_resource(
    conversation_id: UUID,
    current_user: CurrentUser,
    service: Annotated[TransferService, Depends(get_transfer_service)],
    file: UploadFile = File(...),
) -> ResourceResponse:
    """Upload a file as a resource to a conversation.

    Supported formats: PDF, DOC, DOCX, PPT, PPTX, PNG, JPEG, TXT, CSV.
    Maximum file size: 50MB.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    content_type = validate_content_type(file.content_type, _ALLOWED_MIME_TYPES)
    content, total_size = await read_upload_content(file, max_size=_MAX_FILE_SIZE)
    validate_magic_bytes(content, _ALLOWED_MIME_TYPES[content_type])

    safe_filename = sanitize_filename(file.filename)
    file_path = build_storage_key("transfer", str(conversation_id), safe_filename)

    # Upload to MinIO/S3
    storage = get_storage_service()
    try:
        await asyncio.to_thread(
            storage.upload_file,
            file_content=content,
            key=file_path,
            content_type=content_type,
        )
    except Exception as e:
        logger.error("Failed to upload transfer resource: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to upload file to storage",
        ) from e

    # Create resource record
    data = ResourceCreate(
        name=safe_filename,
        file_path=file_path,
        resource_type="file",
    )
    resource = await service.add_resource(
        conversation_id=conversation_id,
        organization_id=current_user.organization_id,
        data=data,
    )
    return ResourceResponse.model_validate(resource)


@router.get(
    "/{conversation_id}/resources/{resource_id}/download",
    summary="Download resource",
    dependencies=[Depends(require_permission(Permission.TRANSFER_READ))],
)
async def download_resource(
    conversation_id: UUID,
    resource_id: UUID,
    current_user: CurrentUser,
    service: Annotated[TransferService, Depends(get_transfer_service)],
) -> RedirectResponse:
    """Download a conversation resource via pre-signed URL."""
    resource = await service.get_resource(
        conversation_id=conversation_id,
        resource_id=resource_id,
        organization_id=current_user.organization_id,
    )

    if not resource.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resource has no file attached (URL-only resource)",
        )

    storage = get_storage_service()
    try:
        url = storage.get_download_url(resource.file_path, expires_in=3600)
    except Exception as e:
        logger.error("Failed to generate download URL: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate download URL",
        ) from e

    return RedirectResponse(url=url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


# =============================================================================
# AI Next Steps Endpoint
# =============================================================================


@router.get(
    "/{conversation_id}/next-steps",
    response_model=NextStepsResponse,
    summary="Get AI-suggested next steps",
    dependencies=[Depends(require_permission(Permission.TRANSFER_READ))],
)
async def get_next_steps(
    conversation_id: UUID,
    current_user: CurrentUser,
    service: Annotated[TransferService, Depends(get_transfer_service)],
) -> NextStepsResponse:
    """Get AI-suggested next steps for a conversation."""
    return await service.get_next_steps(
        conversation_id=conversation_id,
        organization_id=current_user.organization_id,
    )
