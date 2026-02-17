"""Sprint 9: Add simplified_abstract and paper_notes

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-01-31 00:01:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6g7h8i9j0"
down_revision: str | None = "d4e5f6g7h8i9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add simplified_abstract column and paper_notes table."""
    # Add simplified_abstract to papers
    op.add_column("papers", sa.Column("simplified_abstract", sa.Text(), nullable=True))

    # Create paper_notes table
    op.create_table(
        "paper_notes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("paper_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("mentions", sa.JSON(), nullable=False, server_default="[]"),
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
            ["paper_id"], ["papers.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_paper_notes_paper_id", "paper_notes", ["paper_id"])
    op.create_index("ix_paper_notes_user_id", "paper_notes", ["user_id"])


def downgrade() -> None:
    """Remove simplified_abstract column and paper_notes table."""
    op.drop_index("ix_paper_notes_user_id", table_name="paper_notes")
    op.drop_index("ix_paper_notes_paper_id", table_name="paper_notes")
    op.drop_table("paper_notes")
    op.drop_column("papers", "simplified_abstract")
