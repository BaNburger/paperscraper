"""API router for developer API keys, webhooks, and repository sources."""

import json
from typing import Annotated
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, OrganizationId, require_permission
from paper_scraper.core.database import get_db
from paper_scraper.core.permissions import Permission
from paper_scraper.jobs.worker import enqueue_job
from paper_scraper.modules.audit.service import AuditService
from paper_scraper.modules.developer import service
from paper_scraper.modules.developer.schemas import (
    APIKeyCreate,
    APIKeyCreatedResponse,
    APIKeyListResponse,
    APIKeyResponse,
    RepositorySourceCreate,
    RepositorySourceListResponse,
    RepositorySourceResponse,
    RepositorySourceUpdate,
    RepositorySyncTriggerResponse,
    WebhookCreate,
    WebhookListResponse,
    WebhookResponse,
    WebhookTestResult,
    WebhookUpdate,
)

router = APIRouter()

# Type alias for permission dependency
DeveloperManager = Annotated[None, Depends(require_permission(Permission.DEVELOPER_MANAGE))]


# =============================================================================
# API Key Endpoints
# =============================================================================


@router.get(
    "/api-keys/",
    response_model=APIKeyListResponse,
    summary="List API keys",
    description="List all API keys for the organization.",
)
async def list_api_keys(
    db: Annotated[AsyncSession, Depends(get_db)],
    org_id: OrganizationId,
    _auth: DeveloperManager,
) -> APIKeyListResponse:
    """List all API keys for the organization."""
    keys = await service.list_api_keys(db, org_id)
    return APIKeyListResponse(
        items=[APIKeyResponse.model_validate(k) for k in keys],
        total=len(keys),
    )


@router.post(
    "/api-keys/",
    response_model=APIKeyCreatedResponse,
    status_code=201,
    summary="Create API key",
    description="Generate a new API key. The full key is returned ONLY in this response.",
)
async def create_api_key(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    org_id: OrganizationId,
    data: APIKeyCreate,
    _auth: DeveloperManager,
) -> APIKeyCreatedResponse:
    """Create a new API key."""
    api_key, plain_key = await service.create_api_key(
        db, org_id, current_user.id, data
    )

    # Audit log
    audit = AuditService(db)
    await audit.log(
        action="api_key.created",
        user_id=current_user.id,
        organization_id=org_id,
        resource_type="api_key",
        resource_id=api_key.id,
        details={"name": data.name, "permissions": data.permissions},
        request=request,
    )

    return APIKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        key=plain_key,
        key_prefix=api_key.key_prefix,
        permissions=api_key.permissions,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
    )


@router.delete(
    "/api-keys/{key_id}/",
    status_code=204,
    summary="Revoke API key",
    description="Revoke (delete) an API key.",
)
async def revoke_api_key(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    org_id: OrganizationId,
    key_id: UUID,
    _auth: DeveloperManager,
) -> None:
    """Revoke an API key."""
    await service.revoke_api_key(db, org_id, key_id)

    # Audit log
    audit = AuditService(db)
    await audit.log(
        action="api_key.revoked",
        user_id=current_user.id,
        organization_id=org_id,
        resource_type="api_key",
        resource_id=key_id,
        request=request,
    )


# =============================================================================
# Webhook Endpoints
# =============================================================================


@router.get(
    "/webhooks/",
    response_model=WebhookListResponse,
    summary="List webhooks",
    description="List all webhooks for the organization.",
)
async def list_webhooks(
    db: Annotated[AsyncSession, Depends(get_db)],
    org_id: OrganizationId,
    _auth: DeveloperManager,
) -> WebhookListResponse:
    """List all webhooks for the organization."""
    webhooks = await service.list_webhooks(db, org_id)
    return WebhookListResponse(
        items=[WebhookResponse.model_validate(w) for w in webhooks],
        total=len(webhooks),
    )


@router.post(
    "/webhooks/",
    response_model=WebhookResponse,
    status_code=201,
    summary="Create webhook",
    description="Create a new webhook subscription.",
)
async def create_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    org_id: OrganizationId,
    data: WebhookCreate,
    _auth: DeveloperManager,
) -> WebhookResponse:
    """Create a new webhook."""
    webhook = await service.create_webhook(db, org_id, current_user.id, data)

    # Audit log
    audit = AuditService(db)
    await audit.log(
        action="webhook.created",
        user_id=current_user.id,
        organization_id=org_id,
        resource_type="webhook",
        resource_id=webhook.id,
        details={"name": data.name, "url": str(data.url), "events": [e.value for e in data.events]},
        request=request,
    )

    return WebhookResponse.model_validate(webhook)


@router.patch(
    "/webhooks/{webhook_id}/",
    response_model=WebhookResponse,
    summary="Update webhook",
    description="Update a webhook configuration.",
)
async def update_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    org_id: OrganizationId,
    webhook_id: UUID,
    data: WebhookUpdate,
    _auth: DeveloperManager,
) -> WebhookResponse:
    """Update a webhook."""
    webhook = await service.update_webhook(db, org_id, webhook_id, data)

    # Audit log
    audit = AuditService(db)
    await audit.log(
        action="webhook.updated",
        user_id=current_user.id,
        organization_id=org_id,
        resource_type="webhook",
        resource_id=webhook_id,
        details=data.model_dump(exclude_unset=True),
        request=request,
    )

    return WebhookResponse.model_validate(webhook)


@router.post(
    "/webhooks/{webhook_id}/test/",
    response_model=WebhookTestResult,
    summary="Test webhook",
    description="Send a test event to the webhook.",
)
async def test_webhook(
    db: Annotated[AsyncSession, Depends(get_db)],
    org_id: OrganizationId,
    webhook_id: UUID,
    _auth: DeveloperManager,
) -> WebhookTestResult:
    """Send a test event to a webhook."""
    import time

    webhook = await service.get_webhook(db, org_id, webhook_id)

    # Prepare test payload
    test_payload = {
        "event": "test",
        "timestamp": time.time(),
        "data": {
            "message": "This is a test webhook from Paper Scraper",
            "webhook_id": str(webhook_id),
        },
    }
    payload_bytes = json.dumps(test_payload).encode()

    # Sign the payload
    signature = service.sign_webhook_payload(payload_bytes, webhook.secret)

    # Send the test request
    start_time = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook.url,
                content=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature,
                    "X-Webhook-Event": "test",
                    **webhook.headers,
                },
            )
        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        return WebhookTestResult(
            success=response.is_success,
            status_code=response.status_code,
            response_time_ms=elapsed_ms,
        )
    except httpx.RequestError as e:
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        return WebhookTestResult(
            success=False,
            response_time_ms=elapsed_ms,
            error=str(e),
        )


@router.delete(
    "/webhooks/{webhook_id}/",
    status_code=204,
    summary="Delete webhook",
    description="Delete a webhook.",
)
async def delete_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    org_id: OrganizationId,
    webhook_id: UUID,
    _auth: DeveloperManager,
) -> None:
    """Delete a webhook."""
    await service.delete_webhook(db, org_id, webhook_id)

    # Audit log
    audit = AuditService(db)
    await audit.log(
        action="webhook.deleted",
        user_id=current_user.id,
        organization_id=org_id,
        resource_type="webhook",
        resource_id=webhook_id,
        request=request,
    )


# =============================================================================
# Repository Source Endpoints
# =============================================================================


@router.get(
    "/repositories/",
    response_model=RepositorySourceListResponse,
    summary="List repository sources",
    description="List all repository sources for the organization.",
)
async def list_repositories(
    db: Annotated[AsyncSession, Depends(get_db)],
    org_id: OrganizationId,
    _auth: DeveloperManager,
) -> RepositorySourceListResponse:
    """List all repository sources."""
    sources = await service.list_repository_sources(db, org_id)
    return RepositorySourceListResponse(
        items=[RepositorySourceResponse.model_validate(s) for s in sources],
        total=len(sources),
    )


@router.post(
    "/repositories/",
    response_model=RepositorySourceResponse,
    status_code=201,
    summary="Create repository source",
    description="Add a new repository source for paper imports.",
)
async def create_repository(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    org_id: OrganizationId,
    data: RepositorySourceCreate,
    _auth: DeveloperManager,
) -> RepositorySourceResponse:
    """Create a new repository source."""
    source = await service.create_repository_source(
        db, org_id, current_user.id, data
    )

    # Audit log
    audit = AuditService(db)
    await audit.log(
        action="repository.created",
        user_id=current_user.id,
        organization_id=org_id,
        resource_type="repository_source",
        resource_id=source.id,
        details={"name": data.name, "provider": data.provider.value},
        request=request,
    )

    return RepositorySourceResponse.model_validate(source)


@router.patch(
    "/repositories/{source_id}/",
    response_model=RepositorySourceResponse,
    summary="Update repository source",
    description="Update a repository source configuration.",
)
async def update_repository(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    org_id: OrganizationId,
    source_id: UUID,
    data: RepositorySourceUpdate,
    _auth: DeveloperManager,
) -> RepositorySourceResponse:
    """Update a repository source."""
    source = await service.update_repository_source(db, org_id, source_id, data)

    # Audit log
    audit = AuditService(db)
    await audit.log(
        action="repository.updated",
        user_id=current_user.id,
        organization_id=org_id,
        resource_type="repository_source",
        resource_id=source_id,
        details=data.model_dump(exclude_unset=True),
        request=request,
    )

    return RepositorySourceResponse.model_validate(source)


@router.post(
    "/repositories/{source_id}/sync/",
    response_model=RepositorySyncTriggerResponse,
    summary="Trigger repository sync",
    description="Manually trigger a sync for a repository source.",
)
async def trigger_sync(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    org_id: OrganizationId,
    source_id: UUID,
    _auth: DeveloperManager,
) -> RepositorySyncTriggerResponse:
    """Trigger a manual sync for a repository source."""
    # Verify source exists
    source = await service.get_repository_source(db, org_id, source_id)

    # Enqueue the sync job
    job = await enqueue_job(
        "sync_repository_source_task",
        str(source_id),
        str(org_id),
    )

    # Audit log
    audit = AuditService(db)
    await audit.log(
        action="repository.sync_triggered",
        user_id=current_user.id,
        organization_id=org_id,
        resource_type="repository_source",
        resource_id=source_id,
        request=request,
    )

    return RepositorySyncTriggerResponse(
        message=f"Sync triggered for repository source '{source.name}'",
        source_id=source_id,
        job_id=job.job_id if job else None,
    )


@router.get(
    "/repositories/{source_id}/",
    response_model=RepositorySourceResponse,
    summary="Get repository source",
    description="Get details of a repository source.",
)
async def get_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
    org_id: OrganizationId,
    source_id: UUID,
    _auth: DeveloperManager,
) -> RepositorySourceResponse:
    """Get a repository source by ID."""
    source = await service.get_repository_source(db, org_id, source_id)
    return RepositorySourceResponse.model_validate(source)


@router.delete(
    "/repositories/{source_id}/",
    status_code=204,
    summary="Delete repository source",
    description="Delete a repository source.",
)
async def delete_repository(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    org_id: OrganizationId,
    source_id: UUID,
    _auth: DeveloperManager,
) -> None:
    """Delete a repository source."""
    await service.delete_repository_source(db, org_id, source_id)

    # Audit log
    audit = AuditService(db)
    await audit.log(
        action="repository.deleted",
        user_id=current_user.id,
        organization_id=org_id,
        resource_type="repository_source",
        resource_id=source_id,
        request=request,
    )
