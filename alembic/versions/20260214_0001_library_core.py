"""Add library collections and paper tags.

Revision ID: library_core_v2
Revises: sprint38_workflow_assignment
Create Date: 2026-02-14 09:00:00.000000
"""


import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "library_core_v2"
down_revision: str | None = "sprint38_workflow_assignment"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create library collection and paper tag tables."""
    op.create_table(
        "library_collections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["library_collections.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_library_collections_organization_id", "library_collections", ["organization_id"]
    )
    op.create_index("ix_library_collections_parent_id", "library_collections", ["parent_id"])
    op.create_index(
        "ix_library_collections_org_parent",
        "library_collections",
        ["organization_id", "parent_id"],
    )

    op.create_table(
        "library_collection_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("collection_id", sa.Uuid(), nullable=False),
        sa.Column("paper_id", sa.Uuid(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["collection_id"], ["library_collections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_library_collection_items_organization_id",
        "library_collection_items",
        ["organization_id"],
    )
    op.create_index(
        "ix_library_collection_items_collection_id",
        "library_collection_items",
        ["collection_id"],
    )
    op.create_index(
        "ix_library_collection_items_paper_id", "library_collection_items", ["paper_id"]
    )
    op.create_index(
        "ix_library_collection_items_org_collection",
        "library_collection_items",
        ["organization_id", "collection_id"],
    )
    op.create_index(
        "ix_library_collection_items_unique",
        "library_collection_items",
        ["collection_id", "paper_id"],
        unique=True,
    )

    op.create_table(
        "paper_tags",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("paper_id", sa.Uuid(), nullable=False),
        sa.Column("tag", sa.String(length=64), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_paper_tags_organization_id", "paper_tags", ["organization_id"])
    op.create_index("ix_paper_tags_paper_id", "paper_tags", ["paper_id"])
    op.create_index("ix_paper_tags_org_tag", "paper_tags", ["organization_id", "tag"])
    op.create_index(
        "ix_paper_tags_unique",
        "paper_tags",
        ["organization_id", "paper_id", "tag"],
        unique=True,
    )


def downgrade() -> None:
    """Drop library collection and tag tables."""
    op.drop_index("ix_paper_tags_unique", table_name="paper_tags")
    op.drop_index("ix_paper_tags_org_tag", table_name="paper_tags")
    op.drop_index("ix_paper_tags_paper_id", table_name="paper_tags")
    op.drop_index("ix_paper_tags_organization_id", table_name="paper_tags")
    op.drop_table("paper_tags")

    op.drop_index("ix_library_collection_items_unique", table_name="library_collection_items")
    op.drop_index(
        "ix_library_collection_items_org_collection", table_name="library_collection_items"
    )
    op.drop_index("ix_library_collection_items_paper_id", table_name="library_collection_items")
    op.drop_index(
        "ix_library_collection_items_collection_id", table_name="library_collection_items"
    )
    op.drop_index(
        "ix_library_collection_items_organization_id", table_name="library_collection_items"
    )
    op.drop_table("library_collection_items")

    op.drop_index("ix_library_collections_org_parent", table_name="library_collections")
    op.drop_index("ix_library_collections_parent_id", table_name="library_collections")
    op.drop_index("ix_library_collections_organization_id", table_name="library_collections")
    op.drop_table("library_collections")
