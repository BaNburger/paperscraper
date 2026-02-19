"""Add projects models (projects, paper_project_statuses, paper_stage_history)

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-01-29 00:03:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6g7h8"
down_revision: str | None = "b2c3d4e5f6g7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Define the rejection reason enum
# create_type=False prevents SQLAlchemy from auto-creating it when used in create_table
rejection_reason_enum = postgresql.ENUM(
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
    create_type=False,
)


def upgrade() -> None:
    """Upgrade database schema."""
    # Create rejection reason enum type
    rejection_reason_enum.create(op.get_bind(), checkfirst=True)

    # Create projects table
    op.create_table(
        "projects",
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
        # Project metadata
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        # Configurable pipeline stages
        sa.Column(
            "stages",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text(
                """'[
                    {"name": "inbox", "label": "Inbox", "order": 0},
                    {"name": "screening", "label": "Screening", "order": 1},
                    {"name": "evaluation", "label": "Evaluation", "order": 2},
                    {"name": "shortlisted", "label": "Shortlisted", "order": 3},
                    {"name": "contacted", "label": "Contacted", "order": 4},
                    {"name": "rejected", "label": "Rejected", "order": 5},
                    {"name": "archived", "label": "Archived", "order": 6}
                ]'::jsonb"""
            ),
        ),
        # Scoring weights for this project
        sa.Column(
            "scoring_weights",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text(
                """'{
                    "novelty": 0.20,
                    "ip_potential": 0.20,
                    "marketability": 0.20,
                    "feasibility": 0.20,
                    "commercialization": 0.20
                }'::jsonb"""
            ),
        ),
        # Project settings
        sa.Column(
            "settings",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Create paper_project_statuses table
    op.create_table(
        "paper_project_statuses",
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
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Current stage in pipeline
        sa.Column("stage", sa.String(50), nullable=False, server_default="inbox"),
        # Position within stage for ordering
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
        # Assignment
        sa.Column(
            "assigned_to_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # Notes and rejection tracking
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("rejection_reason", rejection_reason_enum, nullable=True),
        sa.Column("rejection_notes", sa.Text, nullable=True),
        # Priority (1=highest, 5=lowest)
        sa.Column("priority", sa.Integer, nullable=False, server_default="3"),
        # Tags for filtering
        sa.Column(
            "tags",
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
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "stage_entered_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # Unique constraint: paper can only be in project once
        sa.UniqueConstraint("paper_id", "project_id", name="uq_paper_project"),
    )

    # Create paper_stage_history table
    op.create_table(
        "paper_stage_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "paper_project_status_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("paper_project_statuses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "changed_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # Transition details
        sa.Column("from_stage", sa.String(50), nullable=True),
        sa.Column("to_stage", sa.String(50), nullable=False),
        sa.Column("comment", sa.Text, nullable=True),
        # Timestamp
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Create indexes for projects
    op.create_index("ix_projects_organization_id", "projects", ["organization_id"])

    # Create indexes for paper_project_statuses
    op.create_index("ix_paper_project_statuses_paper_id", "paper_project_statuses", ["paper_id"])
    op.create_index(
        "ix_paper_project_statuses_project_id", "paper_project_statuses", ["project_id"]
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

    # Create indexes for paper_stage_history
    op.create_index(
        "ix_paper_stage_history_status_id",
        "paper_stage_history",
        ["paper_project_status_id"],
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop indexes for paper_stage_history
    op.drop_index("ix_paper_stage_history_status_id", table_name="paper_stage_history")

    # Drop indexes for paper_project_statuses
    op.drop_index("ix_paper_project_status_assigned", table_name="paper_project_statuses")
    op.drop_index("ix_paper_project_status_project_stage", table_name="paper_project_statuses")
    op.drop_index("ix_paper_project_statuses_project_id", table_name="paper_project_statuses")
    op.drop_index("ix_paper_project_statuses_paper_id", table_name="paper_project_statuses")

    # Drop indexes for projects
    op.drop_index("ix_projects_organization_id", table_name="projects")

    # Drop tables
    op.drop_table("paper_stage_history")
    op.drop_table("paper_project_statuses")
    op.drop_table("projects")

    # Drop the enum type
    rejection_reason_enum.drop(op.get_bind(), checkfirst=True)
