"""FastAPI router for compliance endpoints."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, require_admin
from paper_scraper.core.database import get_db
from paper_scraper.modules.audit.models import AuditAction
from paper_scraper.modules.audit.service import AuditService
from paper_scraper.modules.compliance.schemas import (
    ApplyRetentionRequest,
    ApplyRetentionResponse,
    AuditLogSummary,
    CreateRetentionPolicyRequest,
    DataProcessingInfo,
    RetentionLogListResponse,
    RetentionLogResponse,
    RetentionPolicyListResponse,
    RetentionPolicyResponse,
    SOC2EvidenceResponse,
    SOC2StatusResponse,
    UpdateRetentionPolicyRequest,
)
from paper_scraper.modules.compliance.service import ComplianceService

router = APIRouter()


def get_compliance_service(db: Annotated[AsyncSession, Depends(get_db)]) -> ComplianceService:
    """Dependency to get compliance service instance."""
    return ComplianceService(db)


def get_audit_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AuditService:
    """Dependency to get audit service instance."""
    return AuditService(db)


# ============================================================================
# Audit Logs (Enhanced)
# ============================================================================


@router.get(
    "/audit-logs",
    response_model=None,
    summary="Search audit logs",
    dependencies=[Depends(require_admin)],
)
async def search_audit_logs(
    current_user: CurrentUser,
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    action: str | None = Query(None, description="Filter by action type"),
    user_id: UUID | None = Query(None, description="Filter by user ID"),
    resource_type: str | None = Query(None, description="Filter by resource type"),
    start_date: datetime | None = Query(None, description="Filter from date"),
    end_date: datetime | None = Query(None, description="Filter to date"),
):
    """Search and filter audit logs with pagination.

    Admin only. Provides enhanced filtering beyond the basic /audit endpoint.
    """
    from paper_scraper.modules.audit.schemas import AuditLogFilters

    # Convert action string to enum if provided
    action_enum = None
    if action:
        try:
            action_enum = AuditAction(action)
        except ValueError:
            pass

    filters = AuditLogFilters(
        action=action_enum,
        user_id=user_id,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date,
    )

    return await audit_service.list_logs(
        organization_id=current_user.organization_id,
        filters=filters,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/audit-logs/export",
    summary="Export audit logs as CSV",
    dependencies=[Depends(require_admin)],
)
async def export_audit_logs(
    request: Request,
    current_user: CurrentUser,
    compliance_service: Annotated[ComplianceService, Depends(get_compliance_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    start_date: datetime | None = Query(None, description="Start date"),
    end_date: datetime | None = Query(None, description="End date"),
    actions: str | None = Query(None, description="Comma-separated action types"),
) -> StreamingResponse:
    """Export audit logs as CSV file.

    Admin only. Exports all matching logs for compliance reporting.
    """
    action_list = actions.split(",") if actions else None

    csv_content = await compliance_service.export_audit_logs_csv(
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        actions=action_list,
    )

    # Log the export
    await audit_service.log(
        action=AuditAction.DATA_EXPORT,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_type="audit_logs",
        details={
            "format": "csv",
            "filters": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "actions": action_list,
            },
        },
        request=request,
    )

    filename = f"audit_logs_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get(
    "/audit-logs/summary",
    response_model=AuditLogSummary,
    summary="Get audit log summary",
    dependencies=[Depends(require_admin)],
)
async def get_audit_log_summary(
    current_user: CurrentUser,
    compliance_service: Annotated[ComplianceService, Depends(get_compliance_service)],
    start_date: datetime | None = Query(None, description="Start date"),
    end_date: datetime | None = Query(None, description="End date"),
) -> AuditLogSummary:
    """Get aggregated audit log statistics.

    Admin only. Provides summary for compliance dashboards.
    """
    return await compliance_service.get_audit_log_summary(
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
    )


# ============================================================================
# Retention Policies
# ============================================================================


@router.get(
    "/retention",
    response_model=RetentionPolicyListResponse,
    summary="List retention policies",
    dependencies=[Depends(require_admin)],
)
async def list_retention_policies(
    current_user: CurrentUser,
    compliance_service: Annotated[ComplianceService, Depends(get_compliance_service)],
) -> RetentionPolicyListResponse:
    """List all retention policies for the organization.

    Admin only.
    """
    policies = await compliance_service.list_retention_policies(
        organization_id=current_user.organization_id
    )
    return RetentionPolicyListResponse(
        items=[RetentionPolicyResponse.model_validate(p) for p in policies],
        total=len(policies),
    )


@router.post(
    "/retention",
    response_model=RetentionPolicyResponse,
    summary="Create retention policy",
    dependencies=[Depends(require_admin)],
)
async def create_retention_policy(
    request: Request,
    current_user: CurrentUser,
    compliance_service: Annotated[ComplianceService, Depends(get_compliance_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    data: CreateRetentionPolicyRequest,
) -> RetentionPolicyResponse:
    """Create a new retention policy.

    Admin only. Only one policy per entity type is allowed.
    """
    policy = await compliance_service.create_retention_policy(
        organization_id=current_user.organization_id,
        data=data,
    )

    # Audit log
    await audit_service.log(
        action=AuditAction.ORGANIZATION_UPDATE,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_type="retention_policy",
        resource_id=policy.id,
        details={
            "action": "created",
            "entity_type": data.entity_type.value,
            "retention_days": data.retention_days,
        },
        request=request,
    )

    return RetentionPolicyResponse.model_validate(policy)


@router.patch(
    "/retention/{policy_id}",
    response_model=RetentionPolicyResponse,
    summary="Update retention policy",
    dependencies=[Depends(require_admin)],
)
async def update_retention_policy(
    policy_id: UUID,
    request: Request,
    current_user: CurrentUser,
    compliance_service: Annotated[ComplianceService, Depends(get_compliance_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    data: UpdateRetentionPolicyRequest,
) -> RetentionPolicyResponse:
    """Update a retention policy.

    Admin only.
    """
    policy = await compliance_service.update_retention_policy(
        policy_id=policy_id,
        organization_id=current_user.organization_id,
        data=data,
    )

    # Audit log
    await audit_service.log(
        action=AuditAction.ORGANIZATION_UPDATE,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_type="retention_policy",
        resource_id=policy.id,
        details={
            "action": "updated",
            "changes": data.model_dump(exclude_unset=True),
        },
        request=request,
    )

    return RetentionPolicyResponse.model_validate(policy)


@router.delete(
    "/retention/{policy_id}",
    status_code=204,
    summary="Delete retention policy",
    dependencies=[Depends(require_admin)],
)
async def delete_retention_policy(
    policy_id: UUID,
    request: Request,
    current_user: CurrentUser,
    compliance_service: Annotated[ComplianceService, Depends(get_compliance_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> Response:
    """Delete a retention policy.

    Admin only.
    """
    await compliance_service.delete_retention_policy(
        policy_id=policy_id,
        organization_id=current_user.organization_id,
    )

    # Audit log
    await audit_service.log(
        action=AuditAction.ORGANIZATION_UPDATE,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_type="retention_policy",
        resource_id=policy_id,
        details={"action": "deleted"},
        request=request,
    )

    return Response(status_code=204)


@router.post(
    "/retention/apply",
    response_model=ApplyRetentionResponse,
    summary="Apply retention policies",
    dependencies=[Depends(require_admin)],
)
async def apply_retention_policies(
    request: Request,
    current_user: CurrentUser,
    compliance_service: Annotated[ComplianceService, Depends(get_compliance_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    data: ApplyRetentionRequest,
) -> ApplyRetentionResponse:
    """Apply retention policies now.

    Admin only. Use dry_run=true to preview without actually deleting data.
    """
    results = await compliance_service.apply_retention_policies(
        organization_id=current_user.organization_id,
        dry_run=data.dry_run,
        entity_types=data.entity_types,
    )

    total_affected = sum(r.records_affected for r in results)

    # Audit log
    await audit_service.log(
        action=AuditAction.ORGANIZATION_UPDATE,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_type="retention_policy",
        details={
            "action": "applied",
            "dry_run": data.dry_run,
            "total_affected": total_affected,
            "entity_types": [et.value for et in data.entity_types] if data.entity_types else "all",
        },
        request=request,
    )

    return ApplyRetentionResponse(
        results=results,
        total_affected=total_affected,
        is_dry_run=data.dry_run,
    )


@router.get(
    "/retention/logs",
    response_model=RetentionLogListResponse,
    summary="List retention logs",
    dependencies=[Depends(require_admin)],
)
async def list_retention_logs(
    current_user: CurrentUser,
    compliance_service: Annotated[ComplianceService, Depends(get_compliance_service)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
) -> RetentionLogListResponse:
    """List retention policy application logs.

    Admin only. Shows history of retention policy executions.
    """
    logs, total = await compliance_service.list_retention_logs(
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
    )

    return RetentionLogListResponse(
        items=[RetentionLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
    )


# ============================================================================
# SOC2
# ============================================================================


@router.get(
    "/soc2/status",
    response_model=SOC2StatusResponse,
    summary="Get SOC2 control status",
    dependencies=[Depends(require_admin)],
)
async def get_soc2_status(
    current_user: CurrentUser,
    compliance_service: Annotated[ComplianceService, Depends(get_compliance_service)],
) -> SOC2StatusResponse:
    """Get SOC2 Type II control implementation status.

    Admin only. Returns all control categories and their implementation status.
    """
    status = compliance_service.get_soc2_status()
    return SOC2StatusResponse(**status)


@router.get(
    "/soc2/evidence/{control_id}",
    response_model=SOC2EvidenceResponse,
    summary="Get SOC2 control evidence",
    dependencies=[Depends(require_admin)],
)
async def get_soc2_evidence(
    control_id: str = Path(
        ..., description="SOC2 control ID (e.g., CC6.1)", pattern=r"^CC\d+\.\d+$"
    ),
    current_user: CurrentUser = None,
    compliance_service: Annotated[ComplianceService, Depends(get_compliance_service)] = None,
) -> SOC2EvidenceResponse:
    """Get evidence documentation for a specific SOC2 control.

    Admin only. Returns evidence items and links for auditor review.
    """
    from paper_scraper.core.exceptions import NotFoundError

    evidence = compliance_service.get_soc2_evidence(control_id)
    if not evidence:
        raise NotFoundError("SOC2Control", control_id)

    return SOC2EvidenceResponse(**evidence)


@router.post(
    "/soc2/export",
    summary="Export SOC2 auditor report",
    dependencies=[Depends(require_admin)],
)
async def export_soc2_report(
    request: Request,
    current_user: CurrentUser,
    compliance_service: Annotated[ComplianceService, Depends(get_compliance_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    include_evidence: bool = Query(True, description="Include evidence links"),
) -> dict:
    """Export SOC2 status report for auditor review.

    Admin only. Generates a comprehensive report of all controls.
    """
    status = compliance_service.get_soc2_status()

    # Log the export
    await audit_service.log(
        action=AuditAction.DATA_EXPORT,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_type="soc2_report",
        details={
            "include_evidence": include_evidence,
        },
        request=request,
    )

    return {
        "report": status,
        "generated_at": datetime.now(UTC).isoformat(),
        "organization_id": str(current_user.organization_id),
    }


# ============================================================================
# Data Processing (GDPR)
# ============================================================================


@router.get(
    "/data-processing",
    response_model=DataProcessingInfo,
    summary="Get data processing info",
    dependencies=[Depends(require_admin)],
)
async def get_data_processing_info(
    current_user: CurrentUser,
    compliance_service: Annotated[ComplianceService, Depends(get_compliance_service)],
) -> DataProcessingInfo:
    """Get GDPR data processing transparency information.

    Admin only. Shows where and how data is processed.
    """
    return await compliance_service.get_data_processing_info(
        organization_id=current_user.organization_id
    )
