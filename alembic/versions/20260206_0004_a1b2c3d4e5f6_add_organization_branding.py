"""Add branding JSONB column to organizations.

Revision ID: sprint29_branding
Revises: s8t9u0v1w2x3
Create Date: 2026-02-06

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "sprint29_branding"
down_revision: str | None = "s8t9u0v1w2x3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column(
            "branding",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="Organization branding: logo_url, primary_color, accent_color, favicon_url",
        ),
    )


def downgrade() -> None:
    op.drop_column("organizations", "branding")
