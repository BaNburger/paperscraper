"""Add paper_type column for classification.

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-01-31 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "h8i9j0k1l2m3"
down_revision: str | None = "g7h8i9j0k1l2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create the enum type first
    papertype_enum = sa.Enum(
        "original_research",
        "review",
        "case_study",
        "methodology",
        "theoretical",
        "commentary",
        "preprint",
        "other",
        name="papertype",
    )
    papertype_enum.create(op.get_bind(), checkfirst=True)

    # Add the column
    op.add_column(
        "papers",
        sa.Column("paper_type", papertype_enum, nullable=True),
    )
    op.create_index(
        "ix_papers_paper_type",
        "papers",
        ["paper_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_papers_paper_type", table_name="papers")
    op.drop_column("papers", "paper_type")
    op.execute("DROP TYPE IF EXISTS papertype")
