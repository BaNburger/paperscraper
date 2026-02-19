"""Pydantic schemas for model settings module."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

# =============================================================================
# Model Configuration Schemas
# =============================================================================


class ModelConfigurationCreate(BaseModel):
    """Schema for creating a model configuration."""

    provider: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="LLM provider (openai, anthropic, azure, ollama, google)",
    )
    model_name: str = Field(
        ..., min_length=1, max_length=200, description="Model name (e.g., gpt-5-mini)"
    )
    is_default: bool = Field(default=False, description="Set as default model for organization")
    api_key: str | None = Field(default=None, description="API key (will be encrypted)")
    hosting_info: dict[str, Any] = Field(
        default_factory=dict, description="Hosting/compliance details"
    )
    max_tokens: int = Field(default=4096, ge=1, le=128000, description="Maximum tokens in response")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0, description="Sampling temperature")
    workflow: str | None = Field(
        default=None,
        max_length=50,
        description="AI workflow assignment (scoring, summary, classification, embedding)",
    )


class ModelConfigurationUpdate(BaseModel):
    """Schema for updating a model configuration."""

    provider: str | None = Field(default=None, min_length=1, max_length=50)
    model_name: str | None = Field(default=None, min_length=1, max_length=200)
    is_default: bool | None = None
    api_key: str | None = Field(default=None, description="New API key (will be encrypted)")
    hosting_info: dict[str, Any] | None = None
    max_tokens: int | None = Field(default=None, ge=1, le=128000)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    workflow: str | None = Field(default=None, max_length=50)


class ModelConfigurationResponse(BaseModel):
    """Response schema for model configuration."""

    id: UUID
    organization_id: UUID
    provider: str
    model_name: str
    is_default: bool
    has_api_key: bool = Field(description="Whether an API key is configured")
    hosting_info: dict[str, Any]
    max_tokens: int
    temperature: float
    workflow: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ModelConfigurationListResponse(BaseModel):
    """List of model configurations."""

    items: list[ModelConfigurationResponse]
    total: int


# =============================================================================
# Model Usage Schemas
# =============================================================================


class ModelUsageResponse(BaseModel):
    """Response schema for a model usage record."""

    id: UUID
    organization_id: UUID
    operation: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    model_name: str | None
    provider: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UsageAggregation(BaseModel):
    """Aggregated usage statistics."""

    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_cost_usd: float
    by_operation: dict[str, dict[str, int | float]]
    by_model: dict[str, dict[str, int | float]]
    by_day: list[dict[str, Any]]


class HostingInfoResponse(BaseModel):
    """Response schema for hosting/compliance information."""

    model_configuration_id: UUID
    provider: str
    model_name: str
    hosting_info: dict[str, Any]
    data_processing_region: str | None = None
    compliance_certifications: list[str] = Field(default_factory=list)
