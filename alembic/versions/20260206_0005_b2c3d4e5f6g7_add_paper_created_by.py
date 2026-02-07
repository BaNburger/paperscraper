"""Add created_by_id to papers table.

Revision ID: sprint30_created_by
Revises: sprint29_branding
Create Date: 2026-02-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "sprint30_created_by"
down_revision: Union[str, None] = "sprint29_branding"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "papers",
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
    )
    op.create_index("ix_papers_created_by_id", "papers", ["created_by_id"])
    op.create_foreign_key(
        "fk_papers_created_by_id",
        "papers",
        "users",
        ["created_by_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_papers_created_by_id", "papers", type_="foreignkey")
    op.drop_index("ix_papers_created_by_id", table_name="papers")
    op.drop_column("papers", "created_by_id")
