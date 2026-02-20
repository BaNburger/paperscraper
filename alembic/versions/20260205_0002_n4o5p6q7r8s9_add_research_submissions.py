"""Sprint 18: Add research submissions, attachments, and scores tables.

Revision ID: n4o5p6q7r8s9
Revises: m3n4o5p6q7r8
Create Date: 2026-02-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "n4o5p6q7r8s9"
down_revision: str | None = "m3n4o5p6q7r8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create research_submissions, submission_attachments, and submission_scores tables."""
    # Create SubmissionStatus enum
    submission_status_enum = postgresql.ENUM(
        "draft",
        "submitted",
        "under_review",
        "approved",
        "rejected",
        "converted",
        name="submissionstatus",
        create_type=False,
    )
    submission_status_enum.create(op.get_bind(), checkfirst=True)

    # Create AttachmentType enum
    attachment_type_enum = postgresql.ENUM(
        "pdf",
        "supplementary",
        "patent_draft",
        "presentation",
        "other",
        name="attachmenttype",
        create_type=False,
    )
    attachment_type_enum.create(op.get_bind(), checkfirst=True)

    # Create research_submissions table
    op.create_table(
        "research_submissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("submitted_by_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("research_field", sa.String(255), nullable=True),
        sa.Column("keywords", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column(
            "status",
            submission_status_enum,
            nullable=False,
            server_default="draft",
        ),
        sa.Column("doi", sa.String(255), nullable=True),
        sa.Column("publication_venue", sa.String(500), nullable=True),
        sa.Column("commercial_potential", sa.Text(), nullable=True),
        sa.Column("prior_art_notes", sa.Text(), nullable=True),
        sa.Column("ip_disclosure", sa.Text(), nullable=True),
        sa.Column("reviewed_by_id", sa.Uuid(), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("review_decision", sa.String(50), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("converted_paper_id", sa.Uuid(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["submitted_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewed_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["converted_paper_id"], ["papers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Composite indexes (cover single-column lookups as leading columns)
    op.create_index(
        "ix_submissions_org_status",
        "research_submissions",
        ["organization_id", "status"],
    )
    op.create_index(
        "ix_submissions_submitter",
        "research_submissions",
        ["submitted_by_id", "status"],
    )
    op.create_index(
        "ix_submissions_org_created",
        "research_submissions",
        ["organization_id", "created_at"],
    )
    # FK lookup indexes
    op.create_index(
        "ix_submissions_reviewed_by",
        "research_submissions",
        ["reviewed_by_id"],
    )
    op.create_index(
        "ix_submissions_converted_paper",
        "research_submissions",
        ["converted_paper_id"],
    )

    # Create submission_attachments table
    op.create_table(
        "submission_attachments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("submission_id", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column(
            "attachment_type",
            attachment_type_enum,
            nullable=False,
            server_default="pdf",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["submission_id"], ["research_submissions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_submission_attachments_submission",
        "submission_attachments",
        ["submission_id"],
    )

    # Create submission_scores table
    op.create_table(
        "submission_scores",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("submission_id", sa.Uuid(), nullable=False),
        sa.Column("novelty", sa.Float(), nullable=False),
        sa.Column("ip_potential", sa.Float(), nullable=False),
        sa.Column("marketability", sa.Float(), nullable=False),
        sa.Column("feasibility", sa.Float(), nullable=False),
        sa.Column("commercialization", sa.Float(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("overall_confidence", sa.Float(), nullable=False),
        sa.Column("analysis_summary", sa.Text(), nullable=True),
        sa.Column(
            "dimension_details",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["submission_id"], ["research_submissions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_submission_scores_submission",
        "submission_scores",
        ["submission_id", "created_at"],
    )


def downgrade() -> None:
    """Drop research submissions tables and enums."""
    op.drop_table("submission_scores")
    op.drop_table("submission_attachments")
    op.drop_table("research_submissions")

    # Drop enums
    sa.Enum(name="submissionstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="attachmenttype").drop(op.get_bind(), checkfirst=True)
