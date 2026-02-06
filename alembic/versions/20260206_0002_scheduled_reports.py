"""Add scheduled_reports table.

Revision ID: scheduled_reports
Revises: r7s8t9u0v1w2
Create Date: 2026-02-06 12:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "scheduled_reports"
down_revision: Union[str, None] = "r7s8t9u0v1w2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create scheduled_reports table and enum types."""
    # Create enum types
    report_type_enum = postgresql.ENUM(
        "dashboard_summary",
        "paper_trends",
        "team_activity",
        name="reporttype",
        create_type=False,
    )
    report_type_enum.create(op.get_bind(), checkfirst=True)

    report_schedule_enum = postgresql.ENUM(
        "daily",
        "weekly",
        "monthly",
        name="reportschedule",
        create_type=False,
    )
    report_schedule_enum.create(op.get_bind(), checkfirst=True)

    report_format_enum = postgresql.ENUM(
        "pdf",
        "csv",
        name="reportformat",
        create_type=False,
    )
    report_format_enum.create(op.get_bind(), checkfirst=True)

    # Create scheduled_reports table
    op.create_table(
        "scheduled_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "report_type",
            report_type_enum,
            nullable=False,
        ),
        sa.Column(
            "schedule",
            report_schedule_enum,
            nullable=False,
        ),
        sa.Column(
            "recipients",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "filters",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "format",
            report_format_enum,
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(
        "ix_scheduled_reports_organization_id",
        "scheduled_reports",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_scheduled_reports_org_active",
        "scheduled_reports",
        ["organization_id", "is_active"],
        unique=False,
    )
    op.create_index(
        "ix_scheduled_reports_schedule",
        "scheduled_reports",
        ["schedule", "is_active"],
        unique=False,
    )


def downgrade() -> None:
    """Drop scheduled_reports table and enum types."""
    op.drop_index("ix_scheduled_reports_schedule", table_name="scheduled_reports")
    op.drop_index("ix_scheduled_reports_org_active", table_name="scheduled_reports")
    op.drop_index("ix_scheduled_reports_organization_id", table_name="scheduled_reports")
    op.drop_table("scheduled_reports")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS reporttype")
    op.execute("DROP TYPE IF EXISTS reportschedule")
    op.execute("DROP TYPE IF EXISTS reportformat")
