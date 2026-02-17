"""Pydantic schemas for integration connectors and Zotero sync."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from paper_scraper.modules.integrations.models import (
    ConnectorStatus,
    ConnectorType,
    ZoteroConnectionStatus,
    ZoteroSyncDirection,
    ZoteroSyncRunStatus,
)


class IntegrationConnectorCreate(BaseModel):
    """Create request for an integration connector."""

    connector_type: ConnectorType
    config_json: dict = Field(default_factory=dict)
    status: ConnectorStatus = ConnectorStatus.ACTIVE


class IntegrationConnectorUpdate(BaseModel):
    """Partial update request for an integration connector."""

    config_json: dict | None = None
    status: ConnectorStatus | None = None
    last_error: str | None = None


class IntegrationConnectorResponse(BaseModel):
    """Response schema for integration connectors."""

    id: UUID
    organization_id: UUID
    connector_type: ConnectorType
    config_json: dict
    status: ConnectorStatus
    last_success_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IntegrationConnectorListResponse(BaseModel):
    """List response for integration connectors."""

    items: list[IntegrationConnectorResponse]
    total: int


class ZoteroConnectRequest(BaseModel):
    """Create/update Zotero connection request."""

    user_id: str = Field(min_length=1, max_length=64)
    api_key: str = Field(min_length=1, max_length=500)
    base_url: str = Field(default="https://api.zotero.org", max_length=255)
    library_type: str = Field(default="users", max_length=16)


class ZoteroConnectionStatusResponse(BaseModel):
    """Zotero connection status payload."""

    connected: bool
    status: ZoteroConnectionStatus
    user_id: str | None = None
    base_url: str | None = None
    library_type: str | None = None
    last_error: str | None = None
    last_synced_at: datetime | None = None


class ZoteroSyncRequest(BaseModel):
    """Request payload for manual sync trigger."""

    paper_ids: list[UUID] | None = None


class ZoteroSyncRunResponse(BaseModel):
    """Response for a Zotero sync run."""

    id: UUID
    organization_id: UUID
    direction: ZoteroSyncDirection
    status: ZoteroSyncRunStatus
    started_at: datetime
    completed_at: datetime | None = None
    stats_json: dict = Field(default_factory=dict)
    error_message: str | None = None

    model_config = {"from_attributes": True}
