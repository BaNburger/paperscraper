"""Pydantic schemas for compliance module."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Enums for API
class RetentionActionEnum(str, Enum):
    """Actions to take when retention period expires."""

    ARCHIVE = "archive"
    ANONYMIZE = "anonymize"
    DELETE = "delete"


class RetentionEntityTypeEnum(str, Enum):
    """Types of entities that can have retention policies."""

    PAPERS = "papers"
    AUDIT_LOGS = "audit_logs"
    CONVERSATIONS = "conversations"
    SUBMISSIONS = "submissions"
    ALERTS = "alerts"
    KNOWLEDGE = "knowledge"
    SEARCH_ACTIVITIES = "search_activities"


class SOC2ControlStatus(str, Enum):
    """Status of a SOC2 control implementation."""

    IMPLEMENTED = "implemented"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    NOT_APPLICABLE = "not_applicable"


# Retention Policy Schemas
class RetentionPolicyBase(BaseModel):
    """Base schema for retention policy."""

    entity_type: RetentionEntityTypeEnum
    retention_days: int = Field(..., ge=1, le=3650, description="Days to retain data (1-3650)")
    action: RetentionActionEnum = RetentionActionEnum.ARCHIVE
    description: str | None = None
    is_active: bool = True


class CreateRetentionPolicyRequest(RetentionPolicyBase):
    """Schema for creating a retention policy."""

    pass


class UpdateRetentionPolicyRequest(BaseModel):
    """Schema for updating a retention policy."""

    retention_days: int | None = Field(None, ge=1, le=3650)
    action: RetentionActionEnum | None = None
    description: str | None = None
    is_active: bool | None = None


class RetentionPolicyResponse(RetentionPolicyBase):
    """Schema for retention policy response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    last_applied_at: datetime | None
    records_affected: int
    created_at: datetime
    updated_at: datetime


class RetentionPolicyListResponse(BaseModel):
    """Schema for paginated retention policy list."""

    items: list[RetentionPolicyResponse]
    total: int


# Retention Apply Schemas
class ApplyRetentionRequest(BaseModel):
    """Schema for applying retention policies."""

    dry_run: bool = True
    entity_types: list[RetentionEntityTypeEnum] | None = None


class ApplyRetentionResult(BaseModel):
    """Result of applying a single retention policy."""

    entity_type: str
    action: str
    records_affected: int
    is_dry_run: bool
    status: str


class ApplyRetentionResponse(BaseModel):
    """Schema for apply retention response."""

    results: list[ApplyRetentionResult]
    total_affected: int
    is_dry_run: bool


# Retention Log Schemas
class RetentionLogResponse(BaseModel):
    """Schema for retention log response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    policy_id: UUID | None
    entity_type: str
    action: str
    records_affected: int
    is_dry_run: bool
    status: str
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None


class RetentionLogListResponse(BaseModel):
    """Schema for paginated retention log list."""

    items: list[RetentionLogResponse]
    total: int
    page: int
    page_size: int


# Audit Log Enhanced Schemas
class AuditLogExportRequest(BaseModel):
    """Schema for audit log export request."""

    start_date: datetime | None = None
    end_date: datetime | None = None
    actions: list[str] | None = None
    user_ids: list[UUID] | None = None
    resource_types: list[str] | None = None


class AuditLogSummary(BaseModel):
    """Schema for audit log summary/statistics."""

    total_logs: int
    logs_by_action: dict[str, int]
    logs_by_resource_type: dict[str, int]
    logs_by_user: list[dict]
    time_range: dict


# SOC2 Schemas
class SOC2Control(BaseModel):
    """Schema for a single SOC2 control."""

    id: str
    description: str
    status: SOC2ControlStatus
    evidence_url: str | None = None
    notes: str | None = None
    last_reviewed: datetime | None = None


class SOC2ControlCategory(BaseModel):
    """Schema for a SOC2 control category."""

    code: str
    name: str
    controls: list[SOC2Control]


class SOC2StatusResponse(BaseModel):
    """Schema for SOC2 status response."""

    categories: list[SOC2ControlCategory]
    summary: dict


class SOC2EvidenceResponse(BaseModel):
    """Schema for SOC2 evidence links."""

    control_id: str
    evidence_items: list[dict]


class SOC2ExportRequest(BaseModel):
    """Schema for SOC2 auditor export request."""

    include_evidence: bool = True
    format: str = "pdf"


# Data Processing Schemas
class DataProcessingInfo(BaseModel):
    """Schema for data processing transparency (GDPR)."""

    hosting_info: dict
    data_locations: list[str]
    processors: list[dict]
    retention_policies: list[RetentionPolicyResponse]
    data_categories: list[dict]
    legal_basis: dict
