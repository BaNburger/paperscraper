"""Add alerts tables.

Revision ID: g7h8i9j0k1l2
Revises: f6g7h8i9j0k1
Create Date: 2026-01-31 11:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "g7h8i9j0k1l2"
down_revision: str | None = "f6g7h8i9j0k2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create alerts table
    op.create_table(
        "alerts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("saved_search_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "channel",
            sa.Enum("EMAIL", "IN_APP", name="alertchannel"),
            nullable=False,
            server_default="EMAIL",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("frequency", sa.String(50), nullable=False, server_default="daily"),
        sa.Column("min_results", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trigger_count", sa.Integer(), nullable=False, server_default="0"),
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
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["saved_search_id"],
            ["saved_searches.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_alerts_organization_id",
        "alerts",
        ["organization_id"],
    )
    op.create_index(
        "ix_alerts_user_id",
        "alerts",
        ["user_id"],
    )
    op.create_index(
        "ix_alerts_saved_search_id",
        "alerts",
        ["saved_search_id"],
    )
    op.create_index(
        "ix_alerts_org_active",
        "alerts",
        ["organization_id", "is_active"],
    )
    op.create_index(
        "ix_alerts_user_active",
        "alerts",
        ["user_id", "is_active"],
    )

    # Create alert_results table
    op.create_table(
        "alert_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("alert_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "SENT", "FAILED", "SKIPPED", name="alertstatus"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("papers_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("new_papers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("paper_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["alert_id"],
            ["alerts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_alert_results_alert_id",
        "alert_results",
        ["alert_id"],
    )
    op.create_index(
        "ix_alert_results_alert_created",
        "alert_results",
        ["alert_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_alert_results_alert_created", table_name="alert_results")
    op.drop_index("ix_alert_results_alert_id", table_name="alert_results")
    op.drop_table("alert_results")

    op.drop_index("ix_alerts_user_active", table_name="alerts")
    op.drop_index("ix_alerts_org_active", table_name="alerts")
    op.drop_index("ix_alerts_saved_search_id", table_name="alerts")
    op.drop_index("ix_alerts_user_id", table_name="alerts")
    op.drop_index("ix_alerts_organization_id", table_name="alerts")
    op.drop_table("alerts")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS alertstatus")
    op.execute("DROP TYPE IF EXISTS alertchannel")
