"""Sprint 20: Add transfer conversations, messages, resources, stage_changes, and message_templates tables.

Revision ID: p6q7r8s9t0u1
Revises: o5p6q7r8s9t0
Create Date: 2026-02-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "p6q7r8s9t0u1"
down_revision: str | None = "o5p6q7r8s9t0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create transfer module tables."""
    # Create TransferType enum
    transfer_type_enum = postgresql.ENUM(
        "patent",
        "licensing",
        "startup",
        "partnership",
        "other",
        name="transfertype",
        create_type=False,
    )
    transfer_type_enum.create(op.get_bind(), checkfirst=True)

    # Create TransferStage enum
    transfer_stage_enum = postgresql.ENUM(
        "initial_contact",
        "discovery",
        "evaluation",
        "negotiation",
        "closed_won",
        "closed_lost",
        name="transferstage",
        create_type=False,
    )
    transfer_stage_enum.create(op.get_bind(), checkfirst=True)

    # --- transfer_conversations table ---
    op.create_table(
        "transfer_conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("paper_id", sa.Uuid(), nullable=True),
        sa.Column("researcher_id", sa.Uuid(), nullable=True),
        sa.Column("type", transfer_type_enum, nullable=False),
        sa.Column(
            "stage",
            transfer_stage_enum,
            nullable=False,
            server_default="initial_contact",
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
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
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["researcher_id"], ["authors.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_transfer_conversations_org_id",
        "transfer_conversations",
        ["organization_id"],
    )
    op.create_index(
        "ix_transfer_conversations_org_stage",
        "transfer_conversations",
        ["organization_id", "stage"],
    )
    op.create_index(
        "ix_transfer_conversations_paper",
        "transfer_conversations",
        ["paper_id"],
    )
    op.create_index(
        "ix_transfer_conversations_researcher",
        "transfer_conversations",
        ["researcher_id"],
    )

    # --- conversation_messages table ---
    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("sender_id", sa.Uuid(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "mentions",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["transfer_conversations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_conversation_messages_conv_id",
        "conversation_messages",
        ["conversation_id"],
    )
    op.create_index(
        "ix_conversation_messages_conv_created",
        "conversation_messages",
        ["conversation_id", "created_at"],
    )

    # --- conversation_resources table ---
    op.create_table(
        "conversation_resources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url", sa.String(1000), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["transfer_conversations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_conversation_resources_conv_id",
        "conversation_resources",
        ["conversation_id"],
    )

    # --- stage_changes table ---
    op.create_table(
        "stage_changes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("from_stage", transfer_stage_enum, nullable=False),
        sa.Column("to_stage", transfer_stage_enum, nullable=False),
        sa.Column("changed_by", sa.Uuid(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["transfer_conversations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_stage_changes_conv_id",
        "stage_changes",
        ["conversation_id"],
    )

    # --- message_templates table ---
    op.create_table(
        "message_templates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(500), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("stage", transfer_stage_enum, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_message_templates_org_id",
        "message_templates",
        ["organization_id"],
    )
    op.create_index(
        "ix_message_templates_org_stage",
        "message_templates",
        ["organization_id", "stage"],
    )

    # Create updated_at trigger for transfer_conversations
    op.execute(
        """
        CREATE TRIGGER update_transfer_conversations_updated_at
            BEFORE UPDATE ON transfer_conversations
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """
    )


def downgrade() -> None:
    """Drop transfer module tables and enums."""
    op.execute(
        "DROP TRIGGER IF EXISTS update_transfer_conversations_updated_at ON transfer_conversations"
    )
    op.drop_table("message_templates")
    op.drop_table("stage_changes")
    op.drop_table("conversation_resources")
    op.drop_table("conversation_messages")
    op.drop_table("transfer_conversations")

    # Drop enums
    sa.Enum(name="transferstage").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="transfertype").drop(op.get_bind(), checkfirst=True)
