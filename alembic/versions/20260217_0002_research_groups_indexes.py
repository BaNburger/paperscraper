"""Add missing indexes for research group tables.

Adds indexes on project_clusters.organization_id and
project_cluster_papers.paper_id to match model definitions.

Revision ID: research_groups_indexes_v1
Revises: research_groups_v1
Create Date: 2026-02-17 14:00:00.000000
"""

from alembic import op

revision: str = "research_groups_indexes_v1"
down_revision: str | None = "research_groups_v1"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Add missing indexes."""
    op.create_index(
        "ix_project_clusters_organization_id",
        "project_clusters",
        ["organization_id"],
    )
    op.create_index(
        "ix_project_cluster_papers_paper_id",
        "project_cluster_papers",
        ["paper_id"],
    )


def downgrade() -> None:
    """Remove indexes."""
    op.drop_index(
        "ix_project_cluster_papers_paper_id",
        table_name="project_cluster_papers",
    )
    op.drop_index(
        "ix_project_clusters_organization_id",
        table_name="project_clusters",
    )
