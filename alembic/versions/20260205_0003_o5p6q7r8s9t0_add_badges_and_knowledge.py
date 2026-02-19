"""Sprint 19: Add badges, user_badges, and knowledge_sources tables.

Revision ID: o5p6q7r8s9t0
Revises: n4o5p6q7r8s9
Create Date: 2026-02-05

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "o5p6q7r8s9t0"
down_revision: str | None = "n4o5p6q7r8s9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create badges, user_badges, and knowledge_sources tables."""
    # Create BadgeCategory enum
    badge_category_enum = postgresql.ENUM(
        "import",
        "scoring",
        "collaboration",
        "exploration",
        "milestone",
        name="badgecategory",
        create_type=False,
    )
    badge_category_enum.create(op.get_bind(), checkfirst=True)

    # Create BadgeTier enum
    badge_tier_enum = postgresql.ENUM(
        "bronze",
        "silver",
        "gold",
        "platinum",
        name="badgetier",
        create_type=False,
    )
    badge_tier_enum.create(op.get_bind(), checkfirst=True)

    # Create KnowledgeScope enum
    knowledge_scope_enum = postgresql.ENUM(
        "personal",
        "organization",
        name="knowledgescope",
        create_type=False,
    )
    knowledge_scope_enum.create(op.get_bind(), checkfirst=True)

    # Create KnowledgeType enum
    knowledge_type_enum = postgresql.ENUM(
        "research_focus",
        "industry_context",
        "evaluation_criteria",
        "domain_expertise",
        "custom",
        name="knowledgetype",
        create_type=False,
    )
    knowledge_type_enum.create(op.get_bind(), checkfirst=True)

    # --- badges table ---
    op.create_table(
        "badges",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("icon", sa.String(100), nullable=False, server_default="trophy"),
        sa.Column("category", badge_category_enum, nullable=False),
        sa.Column("tier", badge_tier_enum, nullable=False, server_default="bronze"),
        sa.Column(
            "criteria",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("threshold", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("points", sa.Integer(), nullable=False, server_default="10"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # --- user_badges table ---
    op.create_table(
        "user_badges",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("badge_id", sa.Uuid(), nullable=False),
        sa.Column(
            "earned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["badge_id"], ["badges.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_badges_user_id", "user_badges", ["user_id"])
    op.create_index("ix_user_badges_badge_id", "user_badges", ["badge_id"])
    op.create_index(
        "ix_user_badges_user_badge",
        "user_badges",
        ["user_id", "badge_id"],
        unique=True,
    )

    # --- knowledge_sources table ---
    op.create_table(
        "knowledge_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("scope", knowledge_scope_enum, nullable=False),
        sa.Column(
            "type",
            knowledge_type_enum,
            nullable=False,
            server_default="custom",
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "tags",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
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
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_knowledge_sources_org_id",
        "knowledge_sources",
        ["organization_id"],
    )
    op.create_index(
        "ix_knowledge_sources_user_id",
        "knowledge_sources",
        ["user_id"],
    )
    op.create_index(
        "ix_knowledge_sources_org_scope",
        "knowledge_sources",
        ["organization_id", "scope"],
    )
    op.create_index(
        "ix_knowledge_sources_user_scope",
        "knowledge_sources",
        ["user_id", "scope"],
    )


def downgrade() -> None:
    """Drop badges, user_badges, and knowledge_sources tables and enums."""
    op.drop_table("knowledge_sources")
    op.drop_table("user_badges")
    op.drop_table("badges")

    # Drop enums
    sa.Enum(name="knowledgetype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="knowledgescope").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="badgetier").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="badgecategory").drop(op.get_bind(), checkfirst=True)
