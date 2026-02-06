"""Webhook dispatch background jobs."""

import json
import time
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from paper_scraper.core.config import settings
from paper_scraper.modules.developer import service as dev_service


# Create a separate engine for background jobs
_engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,
)
_async_session = async_sessionmaker(_engine, expire_on_commit=False)


async def dispatch_webhook_task(
    ctx: dict[str, Any],
    webhook_id: str,
    event: str,
    payload: dict,
) -> dict[str, Any]:
    """Dispatch a webhook to the configured URL.

    Args:
        ctx: Worker context.
        webhook_id: Webhook ID to dispatch.
        event: Event name.
        payload: Event payload.

    Returns:
        Result dict with success status and details.
    """
    async with _async_session() as db:
        try:
            webhook = await dev_service.get_webhook(db, UUID(webhook_id), UUID(webhook_id))
        except Exception:
            # Webhook not found or deleted
            return {
                "success": False,
                "error": "Webhook not found",
                "webhook_id": webhook_id,
            }

        # Prepare the payload
        full_payload = {
            "event": event,
            "timestamp": time.time(),
            "data": payload,
        }
        payload_bytes = json.dumps(full_payload).encode()

        # Sign the payload
        signature = dev_service.sign_webhook_payload(payload_bytes, webhook.secret)

        # Attempt delivery with retries
        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        webhook.url,
                        content=payload_bytes,
                        headers={
                            "Content-Type": "application/json",
                            "X-Webhook-Signature": signature,
                            "X-Webhook-Event": event,
                            "X-Webhook-Delivery": webhook_id,
                            **webhook.headers,
                        },
                    )

                if response.is_success:
                    await dev_service.record_webhook_success(db, webhook.id)
                    await db.commit()
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "webhook_id": webhook_id,
                        "event": event,
                        "attempts": attempt + 1,
                    }
                else:
                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"

            except httpx.RequestError as e:
                last_error = str(e)

            # Exponential backoff before retry
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)

        # All retries failed
        failure_count = await dev_service.record_webhook_failure(db, webhook.id)
        await db.commit()

        return {
            "success": False,
            "error": last_error,
            "webhook_id": webhook_id,
            "event": event,
            "attempts": max_retries,
            "failure_count": failure_count,
            "disabled": failure_count >= 10,
        }


async def dispatch_event_to_webhooks(
    db: AsyncSession,
    org_id: UUID,
    event: str,
    payload: dict,
) -> list[str]:
    """Dispatch an event to all subscribed webhooks.

    Args:
        db: Database session.
        org_id: Organization ID.
        event: Event name.
        payload: Event payload.

    Returns:
        List of job IDs for the dispatched webhooks.
    """
    from paper_scraper.jobs.worker import enqueue_job

    webhooks = await dev_service.get_webhooks_for_event(db, org_id, event)

    job_ids = []
    for webhook in webhooks:
        job = await enqueue_job(
            "dispatch_webhook_task",
            str(webhook.id),
            event,
            payload,
        )
        if job:
            job_ids.append(job.job_id)

    return job_ids


# Import asyncio for sleep
import asyncio
