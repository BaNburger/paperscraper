"""Add workflow column to model_configurations.

Revision ID: sprint38_workflow_assignment
Revises: sprint37_foundations_pipeline
Create Date: 2026-02-13 10:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "sprint38_workflow_assignment"
down_revision = "sprint37_foundations_pipeline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "model_configurations",
        sa.Column("workflow", sa.String(50), nullable=True),
    )
    op.create_index(
        "ix_model_configurations_org_workflow",
        "model_configurations",
        ["organization_id", "workflow"],
    )


def downgrade() -> None:
    op.drop_index("ix_model_configurations_org_workflow", table_name="model_configurations")
    op.drop_column("model_configurations", "workflow")
