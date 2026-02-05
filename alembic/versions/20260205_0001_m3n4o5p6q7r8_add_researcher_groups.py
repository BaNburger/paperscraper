"""Sprint 16: Add researcher groups and group members tables.

Revision ID: m3n4o5p6q7r8
Revises: l2m3n4o5p6q7
Create Date: 2026-02-05

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "m3n4o5p6q7r8"
down_revision: str | None = "l2m3n4o5p6q7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create researcher_groups and group_members tables."""
    # Create GroupType enum (create_type=False since we create it manually with checkfirst)
    group_type_enum = postgresql.ENUM(
        "custom", "mailing_list", "speaker_pool",
        name="grouptype",
        create_type=False,
    )
    group_type_enum.create(op.get_bind(), checkfirst=True)

    # Create researcher_groups table
    op.create_table(
        "researcher_groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "type",
            group_type_enum,
            nullable=False,
            server_default="custom",
        ),
        sa.Column("keywords", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], ondelete="SET NULL"
        ),
    )

    # Create indexes for researcher_groups
    op.create_index(
        "ix_researcher_groups_organization_id",
        "researcher_groups",
        ["organization_id"],
    )

    # Create group_members table
    op.create_table(
        "group_members",
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("researcher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("added_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("group_id", "researcher_id"),
        sa.ForeignKeyConstraint(
            ["group_id"], ["researcher_groups.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["researcher_id"], ["authors.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["added_by"], ["users.id"], ondelete="SET NULL"
        ),
    )


def downgrade() -> None:
    """Drop researcher_groups and group_members tables."""
    op.drop_table("group_members")
    op.drop_index("ix_researcher_groups_organization_id", "researcher_groups")
    op.drop_table("researcher_groups")

    # Drop enum type
    group_type_enum = postgresql.ENUM(
        "custom", "mailing_list", "speaker_pool",
        name="grouptype",
    )
    group_type_enum.drop(op.get_bind(), checkfirst=True)
