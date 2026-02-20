"""Global paper catalog + pgvector consolidation.

Phase 1 of scaling PaperScraper to 15-25M papers:

1. Papers & authors become globally shared (organization_id nullable).
   - papers.is_global: True = shared catalog, org_id is NULL
   - authors.is_global: True = deduplicated globally
   - organization_papers junction: tracks which orgs claimed a paper

2. Vector embeddings restored to PostgreSQL (pgvector replaces Qdrant).
   - papers.embedding: vector(1536) column with HNSW index
   - papers.has_embedding backfilled from existing column

3. New source enums for patent databases (Lens.org, EPO, USPTO).

4. New paper types for patents.

Revision ID: global_catalog_pgvector_v1
Revises: qdrant_typesense_v1
Create Date: 2026-02-20 18:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "global_catalog_pgvector_v1"
down_revision: str | None = "qdrant_typesense_v1"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


def upgrade() -> None:
    # ==================================================================
    # 1. Papers table — global catalog support
    # ==================================================================

    # Make organization_id nullable (global papers have NULL org_id)
    op.alter_column(
        "papers",
        "organization_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )

    # Add is_global flag
    op.add_column(
        "papers",
        sa.Column("is_global", sa.Boolean(), nullable=False, server_default="false"),
    )

    # Add embedding vector column (pgvector consolidation — replaces Qdrant)
    op.execute("ALTER TABLE papers ADD COLUMN embedding vector(1536)")

    # Backfill: papers that had has_embedding=true in Qdrant need re-embedding.
    # We leave embedding as NULL and has_embedding=true so the backfill job
    # knows which papers to prioritize for re-embedding from Qdrant export.

    # Global catalog indexes
    op.create_index(
        "ix_papers_global_created",
        "papers",
        ["created_at"],
        postgresql_where=sa.text("is_global = true"),
    )
    op.create_index(
        "uq_papers_global_doi",
        "papers",
        [sa.text("lower(doi)")],
        unique=True,
        postgresql_where=sa.text("is_global = true AND doi IS NOT NULL"),
    )
    op.create_index(
        "ix_papers_global_source",
        "papers",
        ["source", "created_at"],
        postgresql_where=sa.text("is_global = true"),
    )

    # HNSW index for pgvector semantic search (tuned for 10M+ vectors)
    op.execute(
        """
        CREATE INDEX ix_papers_embedding_hnsw ON papers
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 32, ef_construction = 200)
        """
    )

    # Add new source enum values for patent databases
    op.execute("ALTER TYPE papersource ADD VALUE IF NOT EXISTS 'lens'")
    op.execute("ALTER TYPE papersource ADD VALUE IF NOT EXISTS 'epo'")
    op.execute("ALTER TYPE papersource ADD VALUE IF NOT EXISTS 'uspto'")

    # Add new paper type enum values for patents
    op.execute("ALTER TYPE papertype ADD VALUE IF NOT EXISTS 'patent'")
    op.execute("ALTER TYPE papertype ADD VALUE IF NOT EXISTS 'patent_application'")

    # ==================================================================
    # 2. Authors table — global deduplication
    # ==================================================================

    op.alter_column(
        "authors",
        "organization_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )

    op.add_column(
        "authors",
        sa.Column("is_global", sa.Boolean(), nullable=False, server_default="false"),
    )

    # Global dedup indexes for authors
    op.create_index(
        "uq_authors_global_orcid",
        "authors",
        ["orcid"],
        unique=True,
        postgresql_where=sa.text("is_global = true AND orcid IS NOT NULL"),
    )
    op.create_index(
        "uq_authors_global_openalex",
        "authors",
        ["openalex_id"],
        unique=True,
        postgresql_where=sa.text("is_global = true AND openalex_id IS NOT NULL"),
    )

    # ==================================================================
    # 3. Organization-papers junction table
    # ==================================================================

    op.create_table(
        "organization_papers",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("paper_id", sa.Uuid(), nullable=False),
        sa.Column("added_by_id", sa.Uuid(), nullable=True),
        sa.Column("source", sa.String(50), nullable=False, server_default="catalog"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["paper_id"],
            ["papers.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["added_by_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
    )

    op.create_index(
        "uq_org_papers_org_paper",
        "organization_papers",
        ["organization_id", "paper_id"],
        unique=True,
    )
    op.create_index(
        "ix_org_papers_org_id",
        "organization_papers",
        ["organization_id"],
    )
    op.create_index(
        "ix_org_papers_paper_id",
        "organization_papers",
        ["paper_id"],
    )


def downgrade() -> None:
    # Drop organization_papers table
    op.drop_index("ix_org_papers_paper_id", "organization_papers")
    op.drop_index("ix_org_papers_org_id", "organization_papers")
    op.drop_index("uq_org_papers_org_paper", "organization_papers")
    op.drop_table("organization_papers")

    # Remove author global columns and indexes
    op.drop_index("uq_authors_global_openalex", "authors")
    op.drop_index("uq_authors_global_orcid", "authors")
    op.drop_column("authors", "is_global")
    op.alter_column(
        "authors",
        "organization_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )

    # Remove paper HNSW index and embedding column
    op.execute("DROP INDEX IF EXISTS ix_papers_embedding_hnsw")
    op.drop_index("ix_papers_global_source", "papers")
    op.drop_index("uq_papers_global_doi", "papers")
    op.drop_index("ix_papers_global_created", "papers")
    op.drop_column("papers", "embedding")
    op.drop_column("papers", "is_global")
    op.alter_column(
        "papers",
        "organization_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )

    # Note: Cannot remove enum values in PostgreSQL without recreating the type.
    # The 'lens', 'epo', 'uspto', 'patent', 'patent_application' values will remain.
