"""Add organization_usage table for cost tracking and quota enforcement.

Revision ID: org_usage_v1
Revises: global_catalog_pgvector_v1
Create Date: 2026-02-20 20:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "org_usage_v1"
down_revision: str | None = "global_catalog_pgvector_v1"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


def upgrade() -> None:
    op.create_table(
        "organization_usage",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column(
            "organization_id",
            UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period", sa.String(7), nullable=False),
        sa.Column("papers_imported", sa.Integer, nullable=False, server_default="0"),
        sa.Column("papers_scored", sa.Integer, nullable=False, server_default="0"),
        sa.Column("llm_input_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("llm_output_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("embedding_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("estimated_cost_usd", sa.Numeric(10, 4), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "period", name="uq_org_usage_period"),
    )

    op.create_index("ix_org_usage_org_id", "organization_usage", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_org_usage_org_id")
    op.drop_table("organization_usage")
