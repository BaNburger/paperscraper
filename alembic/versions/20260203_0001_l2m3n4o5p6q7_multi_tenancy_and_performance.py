"""Multi-tenancy and performance fixes.

This migration:
1. Adds organization_id to authors table for proper multi-tenancy
2. Adds organization_id to paper_notes table for proper multi-tenancy
3. Converts JSON columns to JSONB for better PostgreSQL performance
4. Adds HNSW index for author embeddings
5. Adds partial unique indexes for ORCID/OpenAlex within organizations

Revision ID: l2m3n4o5p6q7
Revises: j0k1l2m3n4o5
Create Date: 2026-02-03

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "l2m3n4o5p6q7"
down_revision: str | None = "j0k1l2m3n4o5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply multi-tenancy and performance improvements."""

    # =========================================================================
    # 1. Add organization_id to authors table
    # =========================================================================

    # Add column as nullable first
    op.add_column(
        "authors",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Populate organization_id from papers via paper_authors join
    # Each author gets the organization_id from their first associated paper
    op.execute("""
        UPDATE authors
        SET organization_id = subq.org_id
        FROM (
            SELECT DISTINCT ON (pa.author_id)
                pa.author_id,
                p.organization_id AS org_id
            FROM paper_authors pa
            JOIN papers p ON p.id = pa.paper_id
            ORDER BY pa.author_id, p.created_at ASC
        ) AS subq
        WHERE authors.id = subq.author_id
    """)

    # For any orphan authors (no papers), assign to the first organization
    # This handles edge cases during data migration
    op.execute("""
        UPDATE authors
        SET organization_id = (SELECT id FROM organizations LIMIT 1)
        WHERE organization_id IS NULL
    """)

    # Now make the column NOT NULL
    op.alter_column(
        "authors",
        "organization_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )

    # Add foreign key constraint
    op.create_foreign_key(
        "fk_authors_organization_id",
        "authors",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Add index on organization_id
    op.create_index(
        "ix_authors_organization_id",
        "authors",
        ["organization_id"],
    )

    # Drop old unique constraints on orcid and openalex_id (if they exist)
    # They need to be scoped to organization
    try:
        op.drop_constraint("authors_orcid_key", "authors", type_="unique")
    except Exception:
        pass  # Constraint may not exist

    try:
        op.drop_constraint("authors_openalex_id_key", "authors", type_="unique")
    except Exception:
        pass  # Constraint may not exist

    # Add partial unique indexes scoped to organization
    op.execute("""
        CREATE UNIQUE INDEX ix_authors_org_orcid
        ON authors (organization_id, orcid)
        WHERE orcid IS NOT NULL
    """)

    op.execute("""
        CREATE UNIQUE INDEX ix_authors_org_openalex
        ON authors (organization_id, openalex_id)
        WHERE openalex_id IS NOT NULL
    """)

    # =========================================================================
    # 2. Add HNSW index for author embeddings
    # =========================================================================

    # Note: This requires pgvector extension to be installed
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_authors_embedding_hnsw
        ON authors
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    # =========================================================================
    # 3. Add organization_id to paper_notes table
    # =========================================================================

    # Add column as nullable first
    op.add_column(
        "paper_notes",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Populate from the associated paper's organization
    op.execute("""
        UPDATE paper_notes
        SET organization_id = papers.organization_id
        FROM papers
        WHERE paper_notes.paper_id = papers.id
    """)

    # For any orphan notes, assign to first organization
    op.execute("""
        UPDATE paper_notes
        SET organization_id = (SELECT id FROM organizations LIMIT 1)
        WHERE organization_id IS NULL
    """)

    # Make NOT NULL
    op.alter_column(
        "paper_notes",
        "organization_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )

    # Add foreign key
    op.create_foreign_key(
        "fk_paper_notes_organization_id",
        "paper_notes",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Add index
    op.create_index(
        "ix_paper_notes_organization_id",
        "paper_notes",
        ["organization_id"],
    )

    # Add composite index for org + paper queries
    op.create_index(
        "ix_paper_notes_org_paper",
        "paper_notes",
        ["organization_id", "paper_id"],
    )

    # =========================================================================
    # 4. Convert JSON columns to JSONB for better performance
    # =========================================================================

    # Papers table
    op.alter_column(
        "papers",
        "keywords",
        existing_type=postgresql.JSON(),
        type_=postgresql.JSONB(),
        existing_nullable=False,
        postgresql_using="keywords::jsonb",
    )

    op.alter_column(
        "papers",
        "mesh_terms",
        existing_type=postgresql.JSON(),
        type_=postgresql.JSONB(),
        existing_nullable=False,
        postgresql_using="mesh_terms::jsonb",
    )

    op.alter_column(
        "papers",
        "raw_metadata",
        existing_type=postgresql.JSON(),
        type_=postgresql.JSONB(),
        existing_nullable=False,
        postgresql_using="raw_metadata::jsonb",
    )

    # Authors table
    op.alter_column(
        "authors",
        "affiliations",
        existing_type=postgresql.JSON(),
        type_=postgresql.JSONB(),
        existing_nullable=False,
        postgresql_using="affiliations::jsonb",
    )

    # Paper notes table
    op.alter_column(
        "paper_notes",
        "mentions",
        existing_type=postgresql.JSON(),
        type_=postgresql.JSONB(),
        existing_nullable=False,
        postgresql_using="mentions::jsonb",
    )

    # Paper scores table
    op.alter_column(
        "paper_scores",
        "weights",
        existing_type=postgresql.JSON(),
        type_=postgresql.JSONB(),
        existing_nullable=False,
        postgresql_using="weights::jsonb",
    )

    op.alter_column(
        "paper_scores",
        "dimension_details",
        existing_type=postgresql.JSON(),
        type_=postgresql.JSONB(),
        existing_nullable=False,
        postgresql_using="dimension_details::jsonb",
    )

    op.alter_column(
        "paper_scores",
        "errors",
        existing_type=postgresql.JSON(),
        type_=postgresql.JSONB(),
        existing_nullable=False,
        postgresql_using="errors::jsonb",
    )

    # Scoring jobs table
    op.alter_column(
        "scoring_jobs",
        "paper_ids",
        existing_type=postgresql.JSON(),
        type_=postgresql.JSONB(),
        existing_nullable=False,
        postgresql_using="paper_ids::jsonb",
    )

    # Saved searches table
    op.alter_column(
        "saved_searches",
        "filters",
        existing_type=postgresql.JSON(),
        type_=postgresql.JSONB(),
        existing_nullable=False,
        postgresql_using="filters::jsonb",
    )

    # Alert results table
    op.alter_column(
        "alert_results",
        "paper_ids",
        existing_type=postgresql.JSON(),
        type_=postgresql.JSONB(),
        existing_nullable=False,
        postgresql_using="paper_ids::jsonb",
    )

    # Audit logs table
    op.alter_column(
        "audit_logs",
        "details",
        existing_type=postgresql.JSON(),
        type_=postgresql.JSONB(),
        existing_nullable=False,
        postgresql_using="details::jsonb",
    )


def downgrade() -> None:
    """Revert multi-tenancy and performance changes."""

    # =========================================================================
    # Revert JSON columns back to JSON type
    # =========================================================================

    op.alter_column(
        "audit_logs",
        "details",
        existing_type=postgresql.JSONB(),
        type_=postgresql.JSON(),
        existing_nullable=False,
    )

    op.alter_column(
        "alert_results",
        "paper_ids",
        existing_type=postgresql.JSONB(),
        type_=postgresql.JSON(),
        existing_nullable=False,
    )

    op.alter_column(
        "saved_searches",
        "filters",
        existing_type=postgresql.JSONB(),
        type_=postgresql.JSON(),
        existing_nullable=False,
    )

    op.alter_column(
        "scoring_jobs",
        "paper_ids",
        existing_type=postgresql.JSONB(),
        type_=postgresql.JSON(),
        existing_nullable=False,
    )

    op.alter_column(
        "paper_scores",
        "errors",
        existing_type=postgresql.JSONB(),
        type_=postgresql.JSON(),
        existing_nullable=False,
    )

    op.alter_column(
        "paper_scores",
        "dimension_details",
        existing_type=postgresql.JSONB(),
        type_=postgresql.JSON(),
        existing_nullable=False,
    )

    op.alter_column(
        "paper_scores",
        "weights",
        existing_type=postgresql.JSONB(),
        type_=postgresql.JSON(),
        existing_nullable=False,
    )

    op.alter_column(
        "paper_notes",
        "mentions",
        existing_type=postgresql.JSONB(),
        type_=postgresql.JSON(),
        existing_nullable=False,
    )

    op.alter_column(
        "authors",
        "affiliations",
        existing_type=postgresql.JSONB(),
        type_=postgresql.JSON(),
        existing_nullable=False,
    )

    op.alter_column(
        "papers",
        "raw_metadata",
        existing_type=postgresql.JSONB(),
        type_=postgresql.JSON(),
        existing_nullable=False,
    )

    op.alter_column(
        "papers",
        "mesh_terms",
        existing_type=postgresql.JSONB(),
        type_=postgresql.JSON(),
        existing_nullable=False,
    )

    op.alter_column(
        "papers",
        "keywords",
        existing_type=postgresql.JSONB(),
        type_=postgresql.JSON(),
        existing_nullable=False,
    )

    # =========================================================================
    # Remove paper_notes organization_id
    # =========================================================================

    op.drop_index("ix_paper_notes_org_paper", "paper_notes")
    op.drop_index("ix_paper_notes_organization_id", "paper_notes")
    op.drop_constraint("fk_paper_notes_organization_id", "paper_notes", type_="foreignkey")
    op.drop_column("paper_notes", "organization_id")

    # =========================================================================
    # Remove authors HNSW index
    # =========================================================================

    op.execute("DROP INDEX IF EXISTS ix_authors_embedding_hnsw")

    # =========================================================================
    # Remove authors organization_id and restore unique constraints
    # =========================================================================

    op.execute("DROP INDEX IF EXISTS ix_authors_org_openalex")
    op.execute("DROP INDEX IF EXISTS ix_authors_org_orcid")
    op.drop_index("ix_authors_organization_id", "authors")
    op.drop_constraint("fk_authors_organization_id", "authors", type_="foreignkey")
    op.drop_column("authors", "organization_id")

    # Restore original unique constraints
    op.create_unique_constraint("authors_orcid_key", "authors", ["orcid"])
    op.create_unique_constraint("authors_openalex_id_key", "authors", ["openalex_id"])
