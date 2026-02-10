"""Pydantic schemas for integration connectors."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from paper_scraper.modules.integrations.models import ConnectorStatus, ConnectorType


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
