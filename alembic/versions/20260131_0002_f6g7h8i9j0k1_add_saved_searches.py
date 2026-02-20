"""Add saved searches table.

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2026-01-31 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6g7h8i9j0k1"
down_revision: str | None = "e5f6g7h8i9j0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "saved_searches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("mode", sa.String(50), nullable=False, server_default="hybrid"),
        sa.Column("filters", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("share_token", sa.String(64), nullable=True),
        sa.Column("alert_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("alert_frequency", sa.String(50), nullable=True),
        sa.Column("last_alert_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("run_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
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
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_saved_searches_organization_id",
        "saved_searches",
        ["organization_id"],
    )
    op.create_index(
        "ix_saved_searches_created_by_id",
        "saved_searches",
        ["created_by_id"],
    )
    op.create_index(
        "ix_saved_searches_share_token",
        "saved_searches",
        ["share_token"],
        unique=True,
    )
    op.create_index(
        "ix_saved_searches_org_name",
        "saved_searches",
        ["organization_id", "name"],
    )
    op.create_index(
        "ix_saved_searches_org_alert",
        "saved_searches",
        ["organization_id", "alert_enabled"],
    )


def downgrade() -> None:
    op.drop_index("ix_saved_searches_org_alert", table_name="saved_searches")
    op.drop_index("ix_saved_searches_org_name", table_name="saved_searches")
    op.drop_index("ix_saved_searches_share_token", table_name="saved_searches")
    op.drop_index("ix_saved_searches_created_by_id", table_name="saved_searches")
    op.drop_index("ix_saved_searches_organization_id", table_name="saved_searches")
    op.drop_table("saved_searches")
