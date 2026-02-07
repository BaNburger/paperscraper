"""Add retention policies for compliance.

Revision ID: s8t9u0v1w2x3
Revises: scheduled_reports
Create Date: 2026-02-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "s8t9u0v1w2x3"
down_revision: Union[str, None] = "scheduled_reports"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create retention_policies table
    op.create_table(
        "retention_policies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("retention_days", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False, server_default="archive"),
        sa.Column("is_active", sa.Boolean(), nullable=True, default=True),
        sa.Column("last_applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("records_affected", sa.Integer(), nullable=True, default=0),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_retention_policies_org_entity",
        "retention_policies",
        ["organization_id", "entity_type"],
        unique=True,
    )
    op.create_index(
        op.f("ix_retention_policies_organization_id"),
        "retention_policies",
        ["organization_id"],
        unique=False,
    )

    # Create retention_logs table
    op.create_table(
        "retention_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("policy_id", sa.UUID(), nullable=True),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("records_affected", sa.Integer(), nullable=True, default=0),
        sa.Column("is_dry_run", sa.Boolean(), nullable=True, default=False),
        sa.Column("status", sa.String(length=20), nullable=True, server_default="completed"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["policy_id"],
            ["retention_policies.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_retention_logs_org_started",
        "retention_logs",
        ["organization_id", "started_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_retention_logs_organization_id"),
        "retention_logs",
        ["organization_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_retention_logs_organization_id"), table_name="retention_logs")
    op.drop_index("ix_retention_logs_org_started", table_name="retention_logs")
    op.drop_table("retention_logs")

    op.drop_index(op.f("ix_retention_policies_organization_id"), table_name="retention_policies")
    op.drop_index("ix_retention_policies_org_entity", table_name="retention_policies")
    op.drop_table("retention_policies")
