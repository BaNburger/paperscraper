"""Sprint 10: Add author_contacts for contact tracking

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2026-01-31 00:02:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6g7h8i9j0k2"
down_revision: str | None = "f6g7h8i9j0k1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Define enum types
contact_type_enum = postgresql.ENUM(
    "email",
    "phone",
    "linkedin",
    "meeting",
    "conference",
    "other",
    name="contacttype",
    create_type=False,
)

contact_outcome_enum = postgresql.ENUM(
    "successful",
    "no_response",
    "declined",
    "follow_up_needed",
    "in_progress",
    name="contactoutcome",
    create_type=False,
)


def upgrade() -> None:
    """Add author_contacts table for contact tracking."""
    # Create enum types
    contact_type_enum.create(op.get_bind(), checkfirst=True)
    contact_outcome_enum.create(op.get_bind(), checkfirst=True)

    # Create author_contacts table
    op.create_table(
        "author_contacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("contacted_by_id", sa.Uuid(), nullable=True),
        # Contact details
        sa.Column(
            "contact_type",
            contact_type_enum,
            nullable=False,
            server_default="email",
        ),
        sa.Column(
            "contact_date",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("subject", sa.String(500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        # Outcome tracking
        sa.Column("outcome", contact_outcome_enum, nullable=True),
        sa.Column("follow_up_date", sa.DateTime(timezone=True), nullable=True),
        # Related paper
        sa.Column("paper_id", sa.Uuid(), nullable=True),
        # Timestamps
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
        # Foreign keys
        sa.ForeignKeyConstraint(["author_id"], ["authors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["contacted_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(
        "ix_author_contacts_author_id",
        "author_contacts",
        ["author_id"],
    )
    op.create_index(
        "ix_author_contacts_organization_id",
        "author_contacts",
        ["organization_id"],
    )
    op.create_index(
        "ix_author_contacts_org_author",
        "author_contacts",
        ["organization_id", "author_id"],
    )
    op.create_index(
        "ix_author_contacts_contact_date",
        "author_contacts",
        ["organization_id", "contact_date"],
    )


def downgrade() -> None:
    """Remove author_contacts table."""
    # Drop indexes
    op.drop_index("ix_author_contacts_contact_date", table_name="author_contacts")
    op.drop_index("ix_author_contacts_org_author", table_name="author_contacts")
    op.drop_index("ix_author_contacts_organization_id", table_name="author_contacts")
    op.drop_index("ix_author_contacts_author_id", table_name="author_contacts")

    # Drop table
    op.drop_table("author_contacts")

    # Drop enum types
    contact_outcome_enum.drop(op.get_bind(), checkfirst=True)
    contact_type_enum.drop(op.get_bind(), checkfirst=True)
