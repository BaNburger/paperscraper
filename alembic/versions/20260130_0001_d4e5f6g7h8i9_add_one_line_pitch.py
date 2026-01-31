"""Add one_line_pitch to papers

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-01-30 00:01:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6g7h8i9"
down_revision: str | None = "c3d4e5f6g7h8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add one_line_pitch column to papers table."""
    op.add_column("papers", sa.Column("one_line_pitch", sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove one_line_pitch column from papers table."""
    op.drop_column("papers", "one_line_pitch")
