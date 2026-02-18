"""Service layer for model settings module."""
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.core.secrets import decrypt_secret, encrypt_secret
from paper_scraper.modules.model_settings.models import ModelConfiguration, ModelUsage
from paper_scraper.modules.model_settings.schemas import (
    ModelConfigurationCreate,
    ModelConfigurationListResponse,
    ModelConfigurationResponse,
    ModelConfigurationUpdate,
    UsageAggregation,
)


class ModelSettingsService:
    """Service for model configuration and usage tracking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Model Configuration CRUD
    # =========================================================================

    async def list_configurations(
        self,
        organization_id: UUID,
    ) -> ModelConfigurationListResponse:
        """List all model configurations for an organization."""
        query = (
            select(ModelConfiguration)
            .where(ModelConfiguration.organization_id == organization_id)
            .order_by(ModelConfiguration.is_default.desc(), ModelConfiguration.created_at.desc())
        )
        result = await self.db.execute(query)
        configs = list(result.scalars().all())

        items = [self._config_to_response(c) for c in configs]
        return ModelConfigurationListResponse(items=items, total=len(items))

    async def create_configuration(
        self,
        organization_id: UUID,
        data: ModelConfigurationCreate,
    ) -> ModelConfigurationResponse:
        """Create a new model configuration."""
        # If setting as default, unset other defaults first
        if data.is_default:
            await self._unset_defaults(organization_id)

        config = ModelConfiguration(
            organization_id=organization_id,
            provider=data.provider,
            model_name=data.model_name,
            is_default=data.is_default,
            api_key_encrypted=self._encrypt_key(data.api_key) if data.api_key else None,
            hosting_info=data.hosting_info,
            max_tokens=data.max_tokens,
            temperature=data.temperature,
            workflow=data.workflow,
        )
        self.db.add(config)
        await self.db.flush()
        await self.db.refresh(config)
        return self._config_to_response(config)

    async def update_configuration(
        self,
        config_id: UUID,
        organization_id: UUID,
        data: ModelConfigurationUpdate,
    ) -> ModelConfigurationResponse:
        """Update a model configuration."""
        config = await self._get_config(config_id, organization_id)

        if data.provider is not None:
            config.provider = data.provider
        if data.model_name is not None:
            config.model_name = data.model_name
        if data.is_default is not None:
            if data.is_default:
                await self._unset_defaults(organization_id)
            config.is_default = data.is_default
        if data.api_key is not None:
            config.api_key_encrypted = self._encrypt_key(data.api_key)
        if data.hosting_info is not None:
            config.hosting_info = data.hosting_info
        if data.max_tokens is not None:
            config.max_tokens = data.max_tokens
        if data.temperature is not None:
            config.temperature = data.temperature
        if data.workflow is not None:
            config.workflow = data.workflow if data.workflow != "" else None

        await self.db.flush()
        await self.db.refresh(config)
        return self._config_to_response(config)

    async def delete_configuration(
        self,
        config_id: UUID,
        organization_id: UUID,
    ) -> None:
        """Delete a model configuration."""
        config = await self._get_config(config_id, organization_id)
        await self.db.delete(config)
        await self.db.flush()

    async def get_by_workflow(
        self,
        organization_id: UUID,
        workflow: str,
    ) -> ModelConfiguration | None:
        """Get the model configuration assigned to a specific workflow."""
        result = await self.db.execute(
            select(ModelConfiguration).where(
                ModelConfiguration.organization_id == organization_id,
                ModelConfiguration.workflow == workflow,
            ).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_hosting_info(
        self,
        config_id: UUID,
        organization_id: UUID,
    ) -> ModelConfiguration:
        """Get hosting/compliance information for a model configuration."""
        return await self._get_config(config_id, organization_id)

    # =========================================================================
    # Usage Tracking
    # =========================================================================

    async def get_usage_stats(
        self,
        organization_id: UUID,
        days: int = 30,
    ) -> UsageAggregation:
        """Get aggregated usage statistics."""
        since = datetime.now(UTC) - timedelta(days=days)

        base_query = select(ModelUsage).where(
            ModelUsage.organization_id == organization_id,
            ModelUsage.created_at >= since,
        )
        result = await self.db.execute(base_query)
        records = list(result.scalars().all())

        # Aggregate by operation
        by_operation: dict[str, dict[str, int | float]] = {}
        by_model: dict[str, dict[str, int | float]] = {}
        by_day_dict: dict[str, dict[str, int | float]] = {}

        total_input = 0
        total_output = 0
        total_cost = 0.0

        for r in records:
            total_input += r.input_tokens
            total_output += r.output_tokens
            total_cost += r.cost_usd

            # By operation
            op = r.operation
            if op not in by_operation:
                by_operation[op] = {"requests": 0, "tokens": 0, "cost_usd": 0.0}
            by_operation[op]["requests"] = int(by_operation[op]["requests"]) + 1
            by_operation[op]["tokens"] = int(by_operation[op]["tokens"]) + r.input_tokens + r.output_tokens
            by_operation[op]["cost_usd"] = float(by_operation[op]["cost_usd"]) + r.cost_usd

            # By model
            model = r.model_name or "unknown"
            if model not in by_model:
                by_model[model] = {"requests": 0, "tokens": 0, "cost_usd": 0.0}
            by_model[model]["requests"] = int(by_model[model]["requests"]) + 1
            by_model[model]["tokens"] = int(by_model[model]["tokens"]) + r.input_tokens + r.output_tokens
            by_model[model]["cost_usd"] = float(by_model[model]["cost_usd"]) + r.cost_usd

            # By day
            day = r.created_at.strftime("%Y-%m-%d")
            if day not in by_day_dict:
                by_day_dict[day] = {"date": day, "requests": 0, "tokens": 0, "cost_usd": 0.0}
            by_day_dict[day]["requests"] = int(by_day_dict[day]["requests"]) + 1
            by_day_dict[day]["tokens"] = int(by_day_dict[day]["tokens"]) + r.input_tokens + r.output_tokens
            by_day_dict[day]["cost_usd"] = float(by_day_dict[day]["cost_usd"]) + r.cost_usd

        by_day = sorted(by_day_dict.values(), key=lambda x: str(x["date"]))

        return UsageAggregation(
            total_requests=len(records),
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_tokens=total_input + total_output,
            total_cost_usd=round(total_cost, 6),
            by_operation=by_operation,
            by_model=by_model,
            by_day=by_day,
        )

    async def log_usage(
        self,
        organization_id: UUID,
        operation: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        model_name: str | None = None,
        provider: str | None = None,
        user_id: UUID | None = None,
        model_configuration_id: UUID | None = None,
    ) -> ModelUsage:
        """Log a model usage record."""
        usage = ModelUsage(
            organization_id=organization_id,
            model_configuration_id=model_configuration_id,
            user_id=user_id,
            operation=operation,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            model_name=model_name,
            provider=provider,
        )
        self.db.add(usage)
        await self.db.flush()
        return usage

    # =========================================================================
    # Private Methods
    # =========================================================================

    async def _get_config(
        self,
        config_id: UUID,
        organization_id: UUID,
    ) -> ModelConfiguration:
        """Get a model configuration with tenant isolation."""
        result = await self.db.execute(
            select(ModelConfiguration).where(
                ModelConfiguration.id == config_id,
                ModelConfiguration.organization_id == organization_id,
            )
        )
        config = result.scalar_one_or_none()
        if not config:
            raise NotFoundError("ModelConfiguration", str(config_id))
        return config

    async def _unset_defaults(self, organization_id: UUID) -> None:
        """Unset all default flags for an organization."""
        result = await self.db.execute(
            select(ModelConfiguration).where(
                ModelConfiguration.organization_id == organization_id,
                ModelConfiguration.is_default == True,  # noqa: E712
            )
        )
        for config in result.scalars().all():
            config.is_default = False

    def _config_to_response(self, config: ModelConfiguration) -> ModelConfigurationResponse:
        """Convert model to response schema."""
        return ModelConfigurationResponse(
            id=config.id,
            organization_id=config.organization_id,
            provider=config.provider,
            model_name=config.model_name,
            is_default=config.is_default,
            has_api_key=config.api_key_encrypted is not None,
            hosting_info=config.hosting_info,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            workflow=config.workflow,
            created_at=config.created_at,
            updated_at=config.updated_at,
        )

    @staticmethod
    def _encrypt_key(key: str) -> str:
        """Encrypt an API key for storage."""
        return f"enc:v1:{encrypt_secret(key)}"

    @staticmethod
    def _decrypt_key(encrypted: str) -> str:
        """Decrypt an API key from storage.
        """
        if not encrypted.startswith("enc:v1:"):
            raise ValueError("Unsupported encrypted key format")
        return decrypt_secret(encrypted.replace("enc:v1:", "", 1))
