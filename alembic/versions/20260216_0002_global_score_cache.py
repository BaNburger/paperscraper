"""Add global_score_cache table for cross-tenant DOI-based score caching.

Revision ID: global_score_cache_v1
Revises: discovery_profiles_v1
Create Date: 2026-02-16 14:00:00.000000
"""

from typing import Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "global_score_cache_v1"
down_revision: Union[str, None] = "discovery_profiles_v1"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "global_score_cache",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("doi", sa.String(255), nullable=False),
        # Dimension scores
        sa.Column("novelty", sa.Float(), nullable=False),
        sa.Column("ip_potential", sa.Float(), nullable=False),
        sa.Column("marketability", sa.Float(), nullable=False),
        sa.Column("feasibility", sa.Float(), nullable=False),
        sa.Column("commercialization", sa.Float(), nullable=False),
        sa.Column("team_readiness", sa.Float(), nullable=False, server_default=sa.text("0")),
        # Aggregated
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("overall_confidence", sa.Float(), nullable=False),
        # Metadata
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column(
            "dimension_details",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "errors",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Unique index on DOI (one cache entry per DOI)
    op.create_index(
        "ix_global_score_cache_doi",
        "global_score_cache",
        ["doi"],
        unique=True,
    )
    # Index for cleanup queries
    op.create_index(
        "ix_global_score_cache_expires",
        "global_score_cache",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_global_score_cache_expires", table_name="global_score_cache")
    op.drop_index("ix_global_score_cache_doi", table_name="global_score_cache")
    op.drop_table("global_score_cache")
