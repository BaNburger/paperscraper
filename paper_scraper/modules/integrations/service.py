"""Service layer for integration connectors."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.modules.integrations.models import IntegrationConnector
from paper_scraper.modules.integrations.schemas import (
    IntegrationConnectorCreate,
    IntegrationConnectorListResponse,
    IntegrationConnectorResponse,
    IntegrationConnectorUpdate,
)


class IntegrationService:
    """Service for managing tenant-scoped external integrations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_connector(
        self,
        organization_id: UUID,
        data: IntegrationConnectorCreate,
    ) -> IntegrationConnector:
        """Create a connector."""
        connector = IntegrationConnector(
            organization_id=organization_id,
            connector_type=data.connector_type,
            config_json=data.config_json,
            status=data.status,
        )
        self.db.add(connector)
        await self.db.flush()
        await self.db.refresh(connector)
        return connector

    async def update_connector(
        self,
        connector_id: UUID,
        organization_id: UUID,
        data: IntegrationConnectorUpdate,
    ) -> IntegrationConnector:
        """Update an existing connector."""
        connector = await self.get_connector(connector_id, organization_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(connector, key, value)

        await self.db.flush()
        await self.db.refresh(connector)
        return connector

    async def get_connector(
        self,
        connector_id: UUID,
        organization_id: UUID,
    ) -> IntegrationConnector:
        """Get a connector with tenant isolation."""
        result = await self.db.execute(
            select(IntegrationConnector).where(
                IntegrationConnector.id == connector_id,
                IntegrationConnector.organization_id == organization_id,
            )
        )
        connector = result.scalar_one_or_none()
        if connector is None:
            raise NotFoundError("IntegrationConnector", str(connector_id))
        return connector

    async def list_connectors(
        self,
        organization_id: UUID,
    ) -> IntegrationConnectorListResponse:
        """List connectors for organization."""
        result = await self.db.execute(
            select(IntegrationConnector)
            .where(IntegrationConnector.organization_id == organization_id)
            .order_by(IntegrationConnector.created_at.desc())
        )
        items = [
            IntegrationConnectorResponse.model_validate(connector)
            for connector in result.scalars().all()
        ]
        return IntegrationConnectorListResponse(items=items, total=len(items))
