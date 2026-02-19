"""Add search_activities table and organization_id/is_custom to badges.

Revision ID: sprint30_search_badges
Revises: sprint30_created_by
Create Date: 2026-02-06

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "sprint30_search_badges"
down_revision: str | None = "sprint30_created_by"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- SearchActivity table ---
    op.create_table(
        "search_activities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("query", sa.String(1000), nullable=False),
        sa.Column("mode", sa.String(50), nullable=False, server_default="hybrid"),
        sa.Column("results_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("search_time_ms", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Composite indexes cover single-column lookups via leftmost prefix
    op.create_index(
        "ix_search_activities_user_created",
        "search_activities",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_search_activities_org_created",
        "search_activities",
        ["organization_id", "created_at"],
    )

    # --- Badge model: add organization_id + is_custom ---
    op.add_column(
        "badges",
        sa.Column("organization_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "badges",
        sa.Column("is_custom", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_foreign_key(
        "fk_badges_organization_id",
        "badges",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_badges_organization_id", "badges", ["organization_id"])

    # Replace global unique(name) with composite unique(name, organization_id)
    op.drop_constraint("badges_name_key", "badges", type_="unique")
    op.create_unique_constraint("uq_badges_name_org", "badges", ["name", "organization_id"])

    # Prevent duplicate badge awards
    op.create_unique_constraint("uq_user_badges_user_badge", "user_badges", ["user_id", "badge_id"])


def downgrade() -> None:
    # Restore unique constraints
    op.drop_constraint("uq_user_badges_user_badge", "user_badges", type_="unique")
    op.drop_constraint("uq_badges_name_org", "badges", type_="unique")
    op.create_unique_constraint("badges_name_key", "badges", ["name"])

    op.drop_index("ix_badges_organization_id", table_name="badges")
    op.drop_constraint("fk_badges_organization_id", "badges", type_="foreignkey")
    op.drop_column("badges", "is_custom")
    op.drop_column("badges", "organization_id")

    op.drop_index("ix_search_activities_org_created", table_name="search_activities")
    op.drop_index("ix_search_activities_user_created", table_name="search_activities")
    op.drop_table("search_activities")
