"""Service layer for developer API keys, webhooks, and repository sources."""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.exceptions import DuplicateError, NotFoundError, ValidationError
from paper_scraper.modules.developer.models import APIKey, RepositorySource, Webhook
from paper_scraper.modules.developer.schemas import (
    APIKeyCreate,
    RepositorySourceCreate,
    RepositorySourceUpdate,
    WebhookCreate,
    WebhookUpdate,
)

# =============================================================================
# API Key Service
# =============================================================================


def generate_api_key() -> str:
    """Generate a secure API key.

    Returns:
        A 48-character URL-safe API key with 'ps_' prefix.
    """
    return f"ps_{secrets.token_urlsafe(36)}"


def hash_api_key(key: str) -> str:
    """Hash an API key using SHA-256.

    Args:
        key: The plain text API key.

    Returns:
        SHA-256 hash of the key.
    """
    return hashlib.sha256(key.encode()).hexdigest()


def get_key_prefix(key: str) -> str:
    """Extract the prefix from an API key for identification.

    Args:
        key: The full API key.

    Returns:
        First 12 characters of the key.
    """
    return key[:12]


async def create_api_key(
    db: AsyncSession,
    org_id: UUID,
    user_id: UUID,
    data: APIKeyCreate,
) -> tuple[APIKey, str]:
    """Create a new API key.

    Args:
        db: Database session.
        org_id: Organization ID.
        user_id: Creating user ID.
        data: API key creation data.

    Returns:
        Tuple of (APIKey model, plain text key).
    """
    # Generate the key
    plain_key = generate_api_key()
    key_hash = hash_api_key(plain_key)
    key_prefix = get_key_prefix(plain_key)

    api_key = APIKey(
        organization_id=org_id,
        created_by_id=user_id,
        name=data.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        permissions=data.permissions,
        expires_at=data.expires_at,
        is_active=True,
    )

    db.add(api_key)
    await db.flush()
    await db.refresh(api_key)

    return api_key, plain_key


async def list_api_keys(
    db: AsyncSession,
    org_id: UUID,
) -> list[APIKey]:
    """List all API keys for an organization.

    Args:
        db: Database session.
        org_id: Organization ID.

    Returns:
        List of API keys.
    """
    result = await db.execute(
        select(APIKey).where(APIKey.organization_id == org_id).order_by(APIKey.created_at.desc())
    )
    return list(result.scalars().all())


async def get_api_key_by_hash(
    db: AsyncSession,
    key_hash: str,
) -> APIKey | None:
    """Get an API key by its hash.

    Args:
        db: Database session.
        key_hash: SHA-256 hash of the key.

    Returns:
        APIKey if found and active, None otherwise.
    """
    result = await db.execute(
        select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True,  # noqa: E712
        )
    )
    api_key = result.scalar_one_or_none()

    if api_key:
        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.now(UTC):
            return None

    return api_key


async def update_api_key_last_used(
    db: AsyncSession,
    api_key_id: UUID,
) -> None:
    """Update the last_used_at timestamp for an API key.

    Args:
        db: Database session.
        api_key_id: API key ID.
    """
    await db.execute(update(APIKey).where(APIKey.id == api_key_id).values(last_used_at=func.now()))


async def revoke_api_key(
    db: AsyncSession,
    org_id: UUID,
    key_id: UUID,
) -> None:
    """Revoke (delete) an API key.

    Args:
        db: Database session.
        org_id: Organization ID (for tenant isolation).
        key_id: API key ID to revoke.

    Raises:
        NotFoundError: If key not found.
    """
    result = await db.execute(
        delete(APIKey).where(
            APIKey.id == key_id,
            APIKey.organization_id == org_id,
        )
    )
    if result.rowcount == 0:
        raise NotFoundError("API key", str(key_id))


# =============================================================================
# Webhook Service
# =============================================================================


def generate_webhook_secret() -> str:
    """Generate a secure webhook signing secret.

    Returns:
        A 64-character hex secret.
    """
    return secrets.token_hex(32)


def sign_webhook_payload(payload: bytes, secret: str) -> str:
    """Sign a webhook payload with HMAC-SHA256.

    Args:
        payload: The JSON payload bytes.
        secret: The webhook secret.

    Returns:
        HMAC-SHA256 signature as hex string.
    """
    return hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()


async def create_webhook(
    db: AsyncSession,
    org_id: UUID,
    user_id: UUID,
    data: WebhookCreate,
) -> Webhook:
    """Create a new webhook.

    Args:
        db: Database session.
        org_id: Organization ID.
        user_id: Creating user ID.
        data: Webhook creation data.

    Returns:
        Created Webhook model.
    """
    # Check for duplicate URL in org
    existing = await db.execute(
        select(Webhook).where(
            Webhook.organization_id == org_id,
            Webhook.url == str(data.url),
        )
    )
    if existing.scalar_one_or_none():
        raise DuplicateError("Webhook", "url", str(data.url))

    secret = generate_webhook_secret()
    webhook = Webhook(
        organization_id=org_id,
        created_by_id=user_id,
        name=data.name,
        url=str(data.url),
        events=[e.value for e in data.events],
        secret=secret,
        headers=data.headers,
        is_active=True,
    )

    db.add(webhook)
    await db.flush()
    await db.refresh(webhook)

    return webhook


async def list_webhooks(
    db: AsyncSession,
    org_id: UUID,
) -> list[Webhook]:
    """List all webhooks for an organization.

    Args:
        db: Database session.
        org_id: Organization ID.

    Returns:
        List of webhooks.
    """
    result = await db.execute(
        select(Webhook).where(Webhook.organization_id == org_id).order_by(Webhook.created_at.desc())
    )
    return list(result.scalars().all())


async def get_webhook(
    db: AsyncSession,
    org_id: UUID,
    webhook_id: UUID,
) -> Webhook:
    """Get a webhook by ID.

    Args:
        db: Database session.
        org_id: Organization ID.
        webhook_id: Webhook ID.

    Returns:
        Webhook model.

    Raises:
        NotFoundError: If webhook not found.
    """
    result = await db.execute(
        select(Webhook).where(
            Webhook.id == webhook_id,
            Webhook.organization_id == org_id,
        )
    )
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise NotFoundError("Webhook", str(webhook_id))
    return webhook


async def update_webhook(
    db: AsyncSession,
    org_id: UUID,
    webhook_id: UUID,
    data: WebhookUpdate,
) -> Webhook:
    """Update a webhook.

    Args:
        db: Database session.
        org_id: Organization ID.
        webhook_id: Webhook ID.
        data: Update data.

    Returns:
        Updated Webhook model.

    Raises:
        NotFoundError: If webhook not found.
    """
    webhook = await get_webhook(db, org_id, webhook_id)

    update_data = data.model_dump(exclude_unset=True)
    if "url" in update_data:
        update_data["url"] = str(update_data["url"])
    if "events" in update_data:
        update_data["events"] = [e.value for e in update_data["events"]]

    for key, value in update_data.items():
        setattr(webhook, key, value)

    await db.flush()
    await db.refresh(webhook)

    return webhook


async def delete_webhook(
    db: AsyncSession,
    org_id: UUID,
    webhook_id: UUID,
) -> None:
    """Delete a webhook.

    Args:
        db: Database session.
        org_id: Organization ID.
        webhook_id: Webhook ID.

    Raises:
        NotFoundError: If webhook not found.
    """
    result = await db.execute(
        delete(Webhook).where(
            Webhook.id == webhook_id,
            Webhook.organization_id == org_id,
        )
    )
    if result.rowcount == 0:
        raise NotFoundError("Webhook", str(webhook_id))


async def get_webhooks_for_event(
    db: AsyncSession,
    org_id: UUID,
    event: str,
) -> list[Webhook]:
    """Get all active webhooks subscribed to an event.

    Args:
        db: Database session.
        org_id: Organization ID.
        event: Event name.

    Returns:
        List of webhooks subscribed to the event.
    """
    # Use text-based check that works for both PostgreSQL JSONB and SQLite TEXT
    # The JSONB array is stored like: ["paper.created", "paper.scored"]
    # We search for the quoted event string within the JSON
    from sqlalchemy import String, cast

    result = await db.execute(
        select(Webhook).where(
            Webhook.organization_id == org_id,
            Webhook.is_active == True,  # noqa: E712
            cast(Webhook.events, String).contains(f'"{event}"'),
        )
    )
    return list(result.scalars().all())


async def record_webhook_success(
    db: AsyncSession,
    webhook_id: UUID,
) -> None:
    """Record a successful webhook delivery.

    Args:
        db: Database session.
        webhook_id: Webhook ID.
    """
    await db.execute(
        update(Webhook)
        .where(Webhook.id == webhook_id)
        .values(
            last_triggered_at=func.now(),
            failure_count=0,
        )
    )


async def record_webhook_failure(
    db: AsyncSession,
    webhook_id: UUID,
) -> int:
    """Record a webhook delivery failure.

    Args:
        db: Database session.
        webhook_id: Webhook ID.

    Returns:
        New failure count.
    """
    result = await db.execute(select(Webhook.failure_count).where(Webhook.id == webhook_id))
    current_count = result.scalar_one_or_none() or 0
    new_count = current_count + 1

    update_values: dict[str, Any] = {"failure_count": new_count}

    # Auto-disable after 10 consecutive failures
    if new_count >= 10:
        update_values["is_active"] = False

    await db.execute(update(Webhook).where(Webhook.id == webhook_id).values(**update_values))

    return new_count


# =============================================================================
# Repository Source Service
# =============================================================================


async def create_repository_source(
    db: AsyncSession,
    org_id: UUID,
    user_id: UUID,
    data: RepositorySourceCreate,
) -> RepositorySource:
    """Create a new repository source.

    Args:
        db: Database session.
        org_id: Organization ID.
        user_id: Creating user ID.
        data: Repository source creation data.

    Returns:
        Created RepositorySource model.
    """
    # Validate cron expression if provided
    if data.schedule:
        if not _validate_cron_expression(data.schedule):
            raise ValidationError("Invalid cron expression", field="schedule")

    source = RepositorySource(
        organization_id=org_id,
        created_by_id=user_id,
        name=data.name,
        provider=data.provider.value,
        config=data.config.model_dump() if data.config else {},
        schedule=data.schedule,
        is_active=True,
    )

    db.add(source)
    await db.flush()
    await db.refresh(source)

    return source


async def list_repository_sources(
    db: AsyncSession,
    org_id: UUID,
) -> list[RepositorySource]:
    """List all repository sources for an organization.

    Args:
        db: Database session.
        org_id: Organization ID.

    Returns:
        List of repository sources.
    """
    result = await db.execute(
        select(RepositorySource)
        .where(RepositorySource.organization_id == org_id)
        .order_by(RepositorySource.created_at.desc())
    )
    return list(result.scalars().all())


async def get_repository_source(
    db: AsyncSession,
    org_id: UUID,
    source_id: UUID,
) -> RepositorySource:
    """Get a repository source by ID.

    Args:
        db: Database session.
        org_id: Organization ID.
        source_id: Repository source ID.

    Returns:
        RepositorySource model.

    Raises:
        NotFoundError: If source not found.
    """
    result = await db.execute(
        select(RepositorySource).where(
            RepositorySource.id == source_id,
            RepositorySource.organization_id == org_id,
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise NotFoundError("Repository source", str(source_id))
    return source


async def update_repository_source(
    db: AsyncSession,
    org_id: UUID,
    source_id: UUID,
    data: RepositorySourceUpdate,
) -> RepositorySource:
    """Update a repository source.

    Args:
        db: Database session.
        org_id: Organization ID.
        source_id: Repository source ID.
        data: Update data.

    Returns:
        Updated RepositorySource model.

    Raises:
        NotFoundError: If source not found.
        ValidationError: If cron expression is invalid.
    """
    source = await get_repository_source(db, org_id, source_id)

    update_data = data.model_dump(exclude_unset=True)

    # Validate cron expression if being updated
    if "schedule" in update_data and update_data["schedule"]:
        if not _validate_cron_expression(update_data["schedule"]):
            raise ValidationError("Invalid cron expression", field="schedule")

    # Convert config model to dict
    if "config" in update_data and update_data["config"]:
        update_data["config"] = update_data["config"].model_dump()

    for key, value in update_data.items():
        setattr(source, key, value)

    await db.flush()
    await db.refresh(source)

    return source


async def delete_repository_source(
    db: AsyncSession,
    org_id: UUID,
    source_id: UUID,
) -> None:
    """Delete a repository source.

    Args:
        db: Database session.
        org_id: Organization ID.
        source_id: Repository source ID.

    Raises:
        NotFoundError: If source not found.
    """
    result = await db.execute(
        delete(RepositorySource).where(
            RepositorySource.id == source_id,
            RepositorySource.organization_id == org_id,
        )
    )
    if result.rowcount == 0:
        raise NotFoundError("Repository source", str(source_id))


async def record_sync_result(
    db: AsyncSession,
    source_id: UUID,
    result_data: dict,
    papers_imported: int,
) -> None:
    """Record the result of a sync operation.

    Args:
        db: Database session.
        source_id: Repository source ID.
        result_data: Sync result details.
        papers_imported: Number of papers imported.
    """
    await db.execute(
        update(RepositorySource)
        .where(RepositorySource.id == source_id)
        .values(
            last_sync_at=func.now(),
            last_sync_result=result_data,
            papers_synced=RepositorySource.papers_synced + papers_imported,
        )
    )


def _validate_cron_expression(expr: str) -> bool:
    """Validate a cron expression format.

    Args:
        expr: Cron expression string.

    Returns:
        True if valid, False otherwise.
    """
    parts = expr.split()
    if len(parts) != 5:
        return False

    # Basic validation - each part should be valid
    for part in parts:
        if not part:
            return False
        # Allow numbers, *, /, -, and ,
        valid_chars = set("0123456789*/,-")
        if not all(c in valid_chars for c in part):
            return False

    return True
