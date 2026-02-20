"""Add discovery profiles: extend saved_searches + create discovery_runs.

Revision ID: discovery_profiles_v1
Revises: trend_radar_v1
Create Date: 2026-02-16 10:00:00.000000
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "discovery_profiles_v1"
down_revision: str | None = "trend_radar_v1"
branch_labels: str | None = None
depends_on: str | None = None


# Enum for discovery run status
discovery_run_status_enum = postgresql.ENUM(
    "running",
    "completed",
    "completed_with_errors",
    "failed",
    name="discoveryrunstatus",
    create_type=False,
)


def upgrade() -> None:
    # Create enum type first
    discovery_run_status_enum.create(op.get_bind(), checkfirst=True)

    # --- Extend saved_searches table ---
    op.add_column(
        "saved_searches",
        sa.Column("semantic_description", sa.Text(), nullable=True),
    )
    # Vector column via raw SQL (pgvector)
    op.execute("ALTER TABLE saved_searches ADD COLUMN embedding vector(1536)")
    op.add_column(
        "saved_searches",
        sa.Column(
            "target_project_id",
            sa.Uuid(),
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "saved_searches",
        sa.Column(
            "auto_import_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "saved_searches",
        sa.Column(
            "import_sources",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "saved_searches",
        sa.Column(
            "max_import_per_run",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("20"),
        ),
    )
    op.add_column(
        "saved_searches",
        sa.Column("discovery_frequency", sa.String(50), nullable=True),
    )
    op.add_column(
        "saved_searches",
        sa.Column(
            "last_discovery_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # Index for discovery profile lookups
    op.create_index(
        "ix_saved_searches_org_auto_import",
        "saved_searches",
        ["organization_id", "auto_import_enabled"],
    )

    # --- Create discovery_runs table ---
    op.create_table(
        "discovery_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "saved_search_id",
            sa.Uuid(),
            sa.ForeignKey("saved_searches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            discovery_run_status_enum,
            nullable=False,
            server_default=sa.text("'running'"),
        ),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("papers_found", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "papers_imported",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "papers_skipped",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "papers_added_to_project",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_discovery_runs_search_created",
        "discovery_runs",
        ["saved_search_id", "created_at"],
    )
    op.create_index(
        "ix_discovery_runs_org",
        "discovery_runs",
        ["organization_id"],
    )


def downgrade() -> None:
    op.drop_table("discovery_runs")

    op.drop_index("ix_saved_searches_org_auto_import", table_name="saved_searches")
    op.drop_column("saved_searches", "last_discovery_at")
    op.drop_column("saved_searches", "discovery_frequency")
    op.drop_column("saved_searches", "max_import_per_run")
    op.drop_column("saved_searches", "import_sources")
    op.drop_column("saved_searches", "auto_import_enabled")
    op.drop_column("saved_searches", "target_project_id")
    op.drop_column("saved_searches", "embedding")
    op.drop_column("saved_searches", "semantic_description")

    discovery_run_status_enum.drop(op.get_bind(), checkfirst=True)
