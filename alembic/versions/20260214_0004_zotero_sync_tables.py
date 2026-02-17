"""Add Zotero integration sync tables.

Revision ID: zotero_sync_v2
Revises: paper_highlights_v2
Create Date: 2026-02-14 09:35:00.000000
"""


import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "zotero_sync_v2"
down_revision: str | None = "paper_highlights_v2"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create Zotero connection and sync tracking tables."""
    connection_status_enum = postgresql.ENUM(
        "connected",
        "disconnected",
        "error",
        name="zoteroconnectionstatus",
    )
    sync_direction_enum = postgresql.ENUM(
        "outbound",
        "inbound",
        name="zoterosyncdirection",
    )
    sync_status_enum = postgresql.ENUM(
        "queued",
        "running",
        "succeeded",
        "failed",
        name="zoterosyncrunstatus",
    )

    connection_status_enum.create(op.get_bind(), checkfirst=True)
    sync_direction_enum.create(op.get_bind(), checkfirst=True)
    sync_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "zotero_connections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("api_key", sa.Text(), nullable=False),
        sa.Column("base_url", sa.String(length=255), nullable=False, server_default=sa.text("'https://api.zotero.org'")),
        sa.Column("library_type", sa.String(length=16), nullable=False, server_default=sa.text("'users'")),
        sa.Column(
            "status",
            postgresql.ENUM(
                "connected",
                "disconnected",
                "error",
                name="zoteroconnectionstatus",
                create_type=False,
            ),
            nullable=False,
            server_default=sa.text("'connected'"),
        ),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", name="uq_zotero_connections_org"),
    )
    op.create_index("ix_zotero_connections_organization_id", "zotero_connections", ["organization_id"])
    op.create_index("ix_zotero_connections_status", "zotero_connections", ["status"])

    op.create_table(
        "zotero_item_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("paper_id", sa.Uuid(), nullable=False),
        sa.Column("zotero_item_key", sa.String(length=64), nullable=False),
        sa.Column("zotero_version", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "paper_id", "zotero_item_key", name="uq_zotero_item_links"),
    )
    op.create_index("ix_zotero_item_links_organization_id", "zotero_item_links", ["organization_id"])
    op.create_index("ix_zotero_item_links_paper_id", "zotero_item_links", ["paper_id"])
    op.create_index("ix_zotero_item_links_key", "zotero_item_links", ["zotero_item_key"])
    op.create_index(
        "ix_zotero_item_links_org_paper_active",
        "zotero_item_links",
        ["organization_id", "paper_id", "is_active"],
    )

    op.create_table(
        "zotero_sync_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column(
            "direction",
            postgresql.ENUM(
                "outbound",
                "inbound",
                name="zoterosyncdirection",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "queued",
                "running",
                "succeeded",
                "failed",
                name="zoterosyncrunstatus",
                create_type=False,
            ),
            nullable=False,
            server_default=sa.text("'queued'"),
        ),
        sa.Column("triggered_by", sa.Uuid(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stats_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["triggered_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_zotero_sync_runs_organization_id", "zotero_sync_runs", ["organization_id"])
    op.create_index("ix_zotero_sync_runs_status", "zotero_sync_runs", ["status"])
    op.create_index(
        "ix_zotero_sync_runs_org_direction_started",
        "zotero_sync_runs",
        ["organization_id", "direction", "started_at"],
    )


def downgrade() -> None:
    """Drop Zotero sync tables and enums."""
    op.drop_index("ix_zotero_sync_runs_org_direction_started", table_name="zotero_sync_runs")
    op.drop_index("ix_zotero_sync_runs_status", table_name="zotero_sync_runs")
    op.drop_index("ix_zotero_sync_runs_organization_id", table_name="zotero_sync_runs")
    op.drop_table("zotero_sync_runs")

    op.drop_index("ix_zotero_item_links_org_paper_active", table_name="zotero_item_links")
    op.drop_index("ix_zotero_item_links_key", table_name="zotero_item_links")
    op.drop_index("ix_zotero_item_links_paper_id", table_name="zotero_item_links")
    op.drop_index("ix_zotero_item_links_organization_id", table_name="zotero_item_links")
    op.drop_table("zotero_item_links")

    op.drop_index("ix_zotero_connections_status", table_name="zotero_connections")
    op.drop_index("ix_zotero_connections_organization_id", table_name="zotero_connections")
    op.drop_table("zotero_connections")

    postgresql.ENUM(name="zoterosyncrunstatus").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="zoterosyncdirection").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="zoteroconnectionstatus").drop(op.get_bind(), checkfirst=True)
