"""Add foundations pipeline tables and policies.

Revision ID: sprint37_foundations_pipeline
Revises: sprint36_notifications
Create Date: 2026-02-09
"""

from typing import Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "sprint37_foundations_pipeline"
down_revision: Union[str, None] = "sprint36_notifications"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    """Create ingestion/integration/context/policy tables."""
    ingest_run_status_enum = postgresql.ENUM(
        "queued",
        "running",
        "completed",
        "completed_with_errors",
        "failed",
        name="ingestrunstatus",
    )
    connector_type_enum = postgresql.ENUM(
        "market_feed",
        "patent_epo",
        "research_graph",
        "custom",
        name="connectortype",
    )
    connector_status_enum = postgresql.ENUM(
        "active",
        "paused",
        "error",
        name="connectorstatus",
    )

    ingest_run_status_enum.create(op.get_bind(), checkfirst=True)
    connector_type_enum.create(op.get_bind(), checkfirst=True)
    connector_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "ingest_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("initiated_by_id", sa.Uuid(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "queued",
                "running",
                "completed",
                "completed_with_errors",
                "failed",
                name="ingestrunstatus",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("cursor_before", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("cursor_after", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("stats_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["initiated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ingest_runs_source", "ingest_runs", ["source"])
    op.create_index("ix_ingest_runs_organization_id", "ingest_runs", ["organization_id"])
    op.create_index("ix_ingest_runs_initiated_by_id", "ingest_runs", ["initiated_by_id"])
    op.create_index("ix_ingest_runs_status", "ingest_runs", ["status"])
    op.create_index("ix_ingest_runs_idempotency_key", "ingest_runs", ["idempotency_key"])
    op.create_index(
        "ix_ingest_runs_org_source_created",
        "ingest_runs",
        ["organization_id", "source", "created_at"],
    )

    op.create_table(
        "source_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("ingest_run_id", sa.Uuid(), nullable=False),
        sa.Column("raw_payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ingest_run_id"], ["ingest_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source",
            "source_record_id",
            "content_hash",
            name="uq_source_records_source_id_hash",
        ),
    )
    op.create_index("ix_source_records_source", "source_records", ["source"])
    op.create_index("ix_source_records_source_record_id", "source_records", ["source_record_id"])
    op.create_index("ix_source_records_organization_id", "source_records", ["organization_id"])
    op.create_index("ix_source_records_ingest_run_id", "source_records", ["ingest_run_id"])

    op.create_table(
        "ingest_checkpoints",
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("scope_key", sa.String(length=255), nullable=False),
        sa.Column("cursor_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("source", "scope_key"),
    )

    op.create_table(
        "integration_connectors",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column(
            "connector_type",
            postgresql.ENUM(
                "market_feed",
                "patent_epo",
                "research_graph",
                "custom",
                name="connectortype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("config_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "status",
            postgresql.ENUM(
                "active",
                "paused",
                "error",
                name="connectorstatus",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_integration_connectors_organization_id", "integration_connectors", ["organization_id"])
    op.create_index("ix_integration_connectors_connector_type", "integration_connectors", ["connector_type"])
    op.create_index(
        "ix_integration_connectors_org_type",
        "integration_connectors",
        ["organization_id", "connector_type"],
    )

    op.create_table(
        "paper_context_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("paper_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("enrichment_version", sa.String(length=64), nullable=False),
        sa.Column("context_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("freshness_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_paper_context_snapshots_paper_id", "paper_context_snapshots", ["paper_id"])
    op.create_index("ix_paper_context_snapshots_organization_id", "paper_context_snapshots", ["organization_id"])
    op.create_index("ix_paper_context_snapshots_freshness_at", "paper_context_snapshots", ["freshness_at"])
    op.create_index(
        "ix_paper_context_snapshots_org_paper_version",
        "paper_context_snapshots",
        ["organization_id", "paper_id", "enrichment_version"],
        unique=True,
    )

    op.create_table(
        "scoring_policies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=200), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False, server_default=sa.text("0.3")),
        sa.Column("max_tokens", sa.Integer(), nullable=False, server_default=sa.text("4096")),
        sa.Column("secret_ref", sa.String(length=255), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scoring_policies_organization_id", "scoring_policies", ["organization_id"])
    op.create_index(
        "ix_scoring_policies_org_default",
        "scoring_policies",
        ["organization_id", "is_default"],
    )


def downgrade() -> None:
    """Drop foundations pipeline tables and enums."""
    op.drop_index("ix_scoring_policies_org_default", table_name="scoring_policies")
    op.drop_index("ix_scoring_policies_organization_id", table_name="scoring_policies")
    op.drop_table("scoring_policies")

    op.drop_index(
        "ix_paper_context_snapshots_org_paper_version",
        table_name="paper_context_snapshots",
    )
    op.drop_index("ix_paper_context_snapshots_freshness_at", table_name="paper_context_snapshots")
    op.drop_index("ix_paper_context_snapshots_organization_id", table_name="paper_context_snapshots")
    op.drop_index("ix_paper_context_snapshots_paper_id", table_name="paper_context_snapshots")
    op.drop_table("paper_context_snapshots")

    op.drop_index("ix_integration_connectors_org_type", table_name="integration_connectors")
    op.drop_index("ix_integration_connectors_connector_type", table_name="integration_connectors")
    op.drop_index("ix_integration_connectors_organization_id", table_name="integration_connectors")
    op.drop_table("integration_connectors")

    op.drop_table("ingest_checkpoints")

    op.drop_index("ix_source_records_ingest_run_id", table_name="source_records")
    op.drop_index("ix_source_records_organization_id", table_name="source_records")
    op.drop_index("ix_source_records_source_record_id", table_name="source_records")
    op.drop_index("ix_source_records_source", table_name="source_records")
    op.drop_table("source_records")

    op.drop_index("ix_ingest_runs_org_source_created", table_name="ingest_runs")
    op.drop_index("ix_ingest_runs_idempotency_key", table_name="ingest_runs")
    op.drop_index("ix_ingest_runs_status", table_name="ingest_runs")
    op.drop_index("ix_ingest_runs_initiated_by_id", table_name="ingest_runs")
    op.drop_index("ix_ingest_runs_organization_id", table_name="ingest_runs")
    op.drop_index("ix_ingest_runs_source", table_name="ingest_runs")
    op.drop_table("ingest_runs")

    postgresql.ENUM(name="connectorstatus").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="connectortype").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="ingestrunstatus").drop(op.get_bind(), checkfirst=True)
