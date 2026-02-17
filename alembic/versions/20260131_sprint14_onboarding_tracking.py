"""Sprint 14: Add onboarding tracking fields to users.

Revision ID: k1l2m3n4o5p6
Revises: i9j0k1l2m3n4
Create Date: 2026-01-31

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "k1l2m3n4o5p6"
down_revision = "i9j0k1l2m3n4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add onboarding tracking fields."""
    op.add_column(
        "users",
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "users",
        sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Remove onboarding tracking fields."""
    op.drop_column("users", "onboarding_completed_at")
    op.drop_column("users", "onboarding_completed")
