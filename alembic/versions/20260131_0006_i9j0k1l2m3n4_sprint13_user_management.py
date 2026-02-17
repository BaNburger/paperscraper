"""Sprint 13: Add user management and email verification fields.

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2026-01-31 14:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "i9j0k1l2m3n4"
down_revision: str | None = "h8i9j0k1l2m3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add email verification fields to users table
    op.add_column(
        "users",
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "users",
        sa.Column("email_verification_token", sa.String(255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("email_verification_token_expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Add password reset fields to users table
    op.add_column(
        "users",
        sa.Column("password_reset_token", sa.String(255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("password_reset_token_expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes for token lookups
    op.create_index(
        "ix_users_email_verification_token",
        "users",
        ["email_verification_token"],
    )
    op.create_index(
        "ix_users_password_reset_token",
        "users",
        ["password_reset_token"],
    )

    # Create invitation status enum (if not exists)
    op.execute(
        "DO $$ BEGIN CREATE TYPE invitationstatus AS ENUM ('pending', 'accepted', 'declined', 'expired'); EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )

    # Use existing userrole enum - reference it without creating
    userrole_enum = postgresql.ENUM(
        'admin', 'manager', 'member', 'viewer',
        name='userrole',
        create_type=False
    )
    invitationstatus_enum = postgresql.ENUM(
        'pending', 'accepted', 'declined', 'expired',
        name='invitationstatus',
        create_type=False
    )

    # Create team_invitations table
    op.create_table(
        "team_invitations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column(
            "role",
            userrole_enum,
            nullable=False,
            server_default="member",
        ),
        sa.Column("token", sa.String(255), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            invitationstatus_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
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
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index(
        "ix_team_invitations_organization_id",
        "team_invitations",
        ["organization_id"],
    )
    op.create_index(
        "ix_team_invitations_email",
        "team_invitations",
        ["email"],
    )
    op.create_index(
        "ix_team_invitations_token",
        "team_invitations",
        ["token"],
    )
    op.create_index(
        "ix_team_invitations_org_status",
        "team_invitations",
        ["organization_id", "status"],
    )


def downgrade() -> None:
    # Drop team_invitations table
    op.drop_index("ix_team_invitations_org_status", table_name="team_invitations")
    op.drop_index("ix_team_invitations_token", table_name="team_invitations")
    op.drop_index("ix_team_invitations_email", table_name="team_invitations")
    op.drop_index("ix_team_invitations_organization_id", table_name="team_invitations")
    op.drop_table("team_invitations")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS invitationstatus")

    # Drop indexes from users table
    op.drop_index("ix_users_password_reset_token", table_name="users")
    op.drop_index("ix_users_email_verification_token", table_name="users")

    # Drop columns from users table
    op.drop_column("users", "password_reset_token_expires_at")
    op.drop_column("users", "password_reset_token")
    op.drop_column("users", "email_verification_token_expires_at")
    op.drop_column("users", "email_verification_token")
    op.drop_column("users", "email_verified")
