"""Add scoring models (paper_scores, scoring_jobs)

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-29 00:02:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6g7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create paper_scores table
    op.create_table(
        "paper_scores",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "paper_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("papers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Individual dimension scores (0-10)
        sa.Column("novelty", sa.Float, nullable=False),
        sa.Column("ip_potential", sa.Float, nullable=False),
        sa.Column("marketability", sa.Float, nullable=False),
        sa.Column("feasibility", sa.Float, nullable=False),
        sa.Column("commercialization", sa.Float, nullable=False),
        # Aggregated scores
        sa.Column("overall_score", sa.Float, nullable=False),
        sa.Column("overall_confidence", sa.Float, nullable=False),
        # Metadata
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column(
            "weights",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "dimension_details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "errors",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Create scoring_jobs table
    op.create_table(
        "scoring_jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Job metadata
        sa.Column("job_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        # Job details
        sa.Column(
            "paper_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("total_papers", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completed_papers", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failed_papers", sa.Integer, nullable=False, server_default="0"),
        # Error tracking
        sa.Column("error_message", sa.Text, nullable=True),
        # arq job reference
        sa.Column("arq_job_id", sa.String(100), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes for paper_scores
    op.create_index("ix_paper_scores_paper_id", "paper_scores", ["paper_id"])
    op.create_index("ix_paper_scores_organization_id", "paper_scores", ["organization_id"])
    op.create_index("ix_paper_scores_paper_org", "paper_scores", ["paper_id", "organization_id"])
    op.create_index(
        "ix_paper_scores_org_created",
        "paper_scores",
        ["organization_id", "created_at"],
    )

    # Create indexes for scoring_jobs
    op.create_index("ix_scoring_jobs_organization_id", "scoring_jobs", ["organization_id"])
    op.create_index("ix_scoring_jobs_status", "scoring_jobs", ["status"])


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop indexes for scoring_jobs
    op.drop_index("ix_scoring_jobs_status", table_name="scoring_jobs")
    op.drop_index("ix_scoring_jobs_organization_id", table_name="scoring_jobs")

    # Drop indexes for paper_scores
    op.drop_index("ix_paper_scores_org_created", table_name="paper_scores")
    op.drop_index("ix_paper_scores_paper_org", table_name="paper_scores")
    op.drop_index("ix_paper_scores_organization_id", table_name="paper_scores")
    op.drop_index("ix_paper_scores_paper_id", table_name="paper_scores")

    # Drop tables
    op.drop_table("scoring_jobs")
    op.drop_table("paper_scores")
