"""Replace KanBan projects with research group clustering.

Adds research group columns to projects, creates cluster tables,
drops KanBan-specific tables (paper_project_statuses, paper_stage_history).

Revision ID: research_groups_v1
Revises: global_score_cache_v1
Create Date: 2026-02-17 10:00:00.000000
"""

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "research_groups_v1"
down_revision: str | None = "global_score_cache_v1"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Replace KanBan projects with research groups."""

    # --- Drop old KanBan tables (order matters: history refs statuses) ---
    op.drop_index("ix_paper_stage_history_status_id", table_name="paper_stage_history")
    op.drop_table("paper_stage_history")

    op.drop_index("ix_paper_project_status_assigned", table_name="paper_project_statuses")
    op.drop_index("ix_paper_project_status_project_stage", table_name="paper_project_statuses")
    op.drop_index("ix_paper_project_statuses_project_id", table_name="paper_project_statuses")
    op.drop_index("ix_paper_project_statuses_paper_id", table_name="paper_project_statuses")
    op.drop_table("paper_project_statuses")

    # Drop the rejection reason enum
    sa.Enum(name="rejectionreason").drop(op.get_bind(), checkfirst=True)

    # --- Modify projects table: drop KanBan columns, add research group columns ---
    op.drop_column("projects", "stages")
    op.drop_column("projects", "scoring_weights")

    op.add_column(
        "projects",
        sa.Column("institution_name", sa.String(255), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column("openalex_institution_id", sa.String(100), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column("pi_name", sa.String(255), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column(
            "pi_author_id",
            sa.Uuid(),
            sa.ForeignKey("authors.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "projects",
        sa.Column("openalex_author_id", sa.String(100), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column("paper_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "projects",
        sa.Column("cluster_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "projects",
        sa.Column(
            "sync_status",
            sa.String(20),
            nullable=False,
            server_default="idle",
        ),
    )
    op.add_column(
        "projects",
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- Create project_papers junction table ---
    op.create_table(
        "project_papers",
        sa.Column(
            "project_id",
            sa.Uuid(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "paper_id",
            sa.Uuid(),
            sa.ForeignKey("papers.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_project_papers_paper_id", "project_papers", ["paper_id"])

    # --- Create project_clusters table ---
    op.create_table(
        "project_clusters",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "project_id",
            sa.Uuid(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "keywords",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("paper_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("centroid", Vector(1536), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_project_clusters_project_id", "project_clusters", ["project_id"])

    # --- Create project_cluster_papers junction table ---
    op.create_table(
        "project_cluster_papers",
        sa.Column(
            "cluster_id",
            sa.Uuid(),
            sa.ForeignKey("project_clusters.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "paper_id",
            sa.Uuid(),
            sa.ForeignKey("papers.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("similarity_score", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    """Revert to KanBan projects."""
    # Drop new tables
    op.drop_table("project_cluster_papers")
    op.drop_index("ix_project_clusters_project_id", table_name="project_clusters")
    op.drop_table("project_clusters")
    op.drop_index("ix_project_papers_paper_id", table_name="project_papers")
    op.drop_table("project_papers")

    # Remove research group columns from projects
    op.drop_column("projects", "last_synced_at")
    op.drop_column("projects", "sync_status")
    op.drop_column("projects", "cluster_count")
    op.drop_column("projects", "paper_count")
    op.drop_column("projects", "openalex_author_id")
    op.drop_column("projects", "pi_author_id")
    op.drop_column("projects", "pi_name")
    op.drop_column("projects", "openalex_institution_id")
    op.drop_column("projects", "institution_name")

    # Restore KanBan columns
    op.add_column(
        "projects",
        sa.Column(
            "stages",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "projects",
        sa.Column(
            "scoring_weights",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )

    # Recreate rejection reason enum
    rejection_reason_enum = sa.Enum(
        "out_of_scope",
        "low_novelty",
        "low_commercial_potential",
        "ip_concerns",
        "insufficient_data",
        "competitor_owned",
        "too_early_stage",
        "too_late_stage",
        "duplicate",
        "other",
        name="rejectionreason",
    )
    rejection_reason_enum.create(op.get_bind(), checkfirst=True)

    # Recreate paper_project_statuses
    op.create_table(
        "paper_project_statuses",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "paper_id",
            sa.Uuid(),
            sa.ForeignKey("papers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            sa.Uuid(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stage", sa.String(50), nullable=False, server_default="inbox"),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "assigned_to_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("rejection_reason", rejection_reason_enum, nullable=True),
        sa.Column("rejection_notes", sa.Text(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("tags", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "stage_entered_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("paper_id", "project_id", name="uq_paper_project"),
    )
    op.create_index("ix_paper_project_statuses_paper_id", "paper_project_statuses", ["paper_id"])
    op.create_index(
        "ix_paper_project_statuses_project_id",
        "paper_project_statuses",
        ["project_id"],
    )
    op.create_index(
        "ix_paper_project_status_project_stage",
        "paper_project_statuses",
        ["project_id", "stage"],
    )
    op.create_index(
        "ix_paper_project_status_assigned",
        "paper_project_statuses",
        ["assigned_to_id"],
    )

    # Recreate paper_stage_history
    op.create_table(
        "paper_stage_history",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "paper_project_status_id",
            sa.Uuid(),
            sa.ForeignKey("paper_project_statuses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "changed_by_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("from_stage", sa.String(50), nullable=True),
        sa.Column("to_stage", sa.String(50), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_paper_stage_history_status_id",
        "paper_stage_history",
        ["paper_project_status_id"],
    )
