"""Add canonical paper text chunks.

Revision ID: paper_text_chunks_v2
Revises: library_core_v2
Create Date: 2026-02-14 09:10:00.000000
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "paper_text_chunks_v2"
down_revision: str | None = "library_core_v2"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create paper_text_chunks table."""
    op.create_table(
        "paper_text_chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("paper_id", sa.Uuid(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("char_start", sa.Integer(), nullable=False),
        sa.Column("char_end", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_paper_text_chunks_organization_id", "paper_text_chunks", ["organization_id"]
    )
    op.create_index("ix_paper_text_chunks_paper_id", "paper_text_chunks", ["paper_id"])
    op.create_index(
        "ix_paper_text_chunks_org_paper",
        "paper_text_chunks",
        ["organization_id", "paper_id"],
    )
    op.create_index(
        "ix_paper_text_chunks_unique",
        "paper_text_chunks",
        ["paper_id", "chunk_index"],
        unique=True,
    )


def downgrade() -> None:
    """Drop paper_text_chunks table."""
    op.drop_index("ix_paper_text_chunks_unique", table_name="paper_text_chunks")
    op.drop_index("ix_paper_text_chunks_org_paper", table_name="paper_text_chunks")
    op.drop_index("ix_paper_text_chunks_paper_id", table_name="paper_text_chunks")
    op.drop_index("ix_paper_text_chunks_organization_id", table_name="paper_text_chunks")
    op.drop_table("paper_text_chunks")
