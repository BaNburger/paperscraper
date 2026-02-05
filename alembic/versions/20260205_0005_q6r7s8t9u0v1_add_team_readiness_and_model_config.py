"""Sprint 23: Add team_readiness column to paper_scores and model_configurations tables.

Revision ID: q6r7s8t9u0v1
Revises: p6q7r8s9t0u1
Create Date: 2026-02-05
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "q6r7s8t9u0v1"
down_revision: str | None = "p6q7r8s9t0u1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add team_readiness column to paper_scores
    op.add_column(
        "paper_scores",
        sa.Column(
            "team_readiness",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    # Create model_configurations table
    op.create_table(
        "model_configurations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model_name", sa.String(200), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("api_key_encrypted", sa.Text(), nullable=True),
        sa.Column(
            "hosting_info",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("max_tokens", sa.Integer(), nullable=False, server_default="4096"),
        sa.Column("temperature", sa.Float(), nullable=False, server_default="0.3"),
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
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_model_configurations_org_id",
        "model_configurations",
        ["organization_id"],
    )
    op.create_index(
        "ix_model_configurations_org_default",
        "model_configurations",
        ["organization_id", "is_default"],
    )

    # Create model_usage table
    op.create_table(
        "model_usage",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("model_configuration_id", sa.Uuid(), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("operation", sa.String(50), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("model_name", sa.String(200), nullable=True),
        sa.Column("provider", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["model_configuration_id"],
            ["model_configurations.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_model_usage_org_id",
        "model_usage",
        ["organization_id"],
    )
    op.create_index(
        "ix_model_usage_org_created",
        "model_usage",
        ["organization_id", "created_at"],
    )

    # Add updated_at trigger for model_configurations
    op.execute("""
        CREATE TRIGGER update_model_configurations_updated_at
            BEFORE UPDATE ON model_configurations
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS update_model_configurations_updated_at "
        "ON model_configurations"
    )
    op.drop_table("model_usage")
    op.drop_table("model_configurations")
    op.drop_column("paper_scores", "team_readiness")
