"""Add paper highlights table.

Revision ID: paper_highlights_v2
Revises: paper_text_chunks_v2
Create Date: 2026-02-14 09:20:00.000000
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "paper_highlights_v2"
down_revision: str | None = "paper_text_chunks_v2"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create paper_highlights table and source enum."""
    highlight_source_enum = postgresql.ENUM(
        "ai",
        "manual",
        "zotero",
        name="highlightsource",
    )
    highlight_source_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "paper_highlights",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("paper_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_id", sa.Uuid(), nullable=True),
        sa.Column("chunk_ref", sa.String(length=128), nullable=False),
        sa.Column("quote", sa.Text(), nullable=False),
        sa.Column("insight_summary", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default=sa.text("0.5")),
        sa.Column(
            "source",
            postgresql.ENUM(
                "ai",
                "manual",
                "zotero",
                name="highlightsource",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("generation_id", sa.Uuid(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chunk_id"], ["paper_text_chunks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_paper_highlights_organization_id", "paper_highlights", ["organization_id"])
    op.create_index("ix_paper_highlights_paper_id", "paper_highlights", ["paper_id"])
    op.create_index(
        "ix_paper_highlights_org_paper_active",
        "paper_highlights",
        ["organization_id", "paper_id", "is_active"],
    )
    op.create_index(
        "ix_paper_highlights_generation",
        "paper_highlights",
        ["paper_id", "generation_id"],
    )


def downgrade() -> None:
    """Drop paper_highlights table and enum."""
    op.drop_index("ix_paper_highlights_generation", table_name="paper_highlights")
    op.drop_index("ix_paper_highlights_org_paper_active", table_name="paper_highlights")
    op.drop_index("ix_paper_highlights_paper_id", table_name="paper_highlights")
    op.drop_index("ix_paper_highlights_organization_id", table_name="paper_highlights")
    op.drop_table("paper_highlights")
    postgresql.ENUM(name="highlightsource").drop(op.get_bind(), checkfirst=True)
