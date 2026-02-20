"""Migrate vector columns to Qdrant + add Typesense search.

Drop all pgvector embedding/centroid columns and HNSW indexes from PostgreSQL.
Vectors now live in Qdrant; full-text search is handled by Typesense.

- papers.embedding (Vector 1536) -> dropped (moved to Qdrant papers collection)
- papers.has_embedding (Boolean) -> added (lightweight flag for query filtering)
- authors.embedding (Vector 768) -> dropped (moved to Qdrant authors collection)
- trend_topics.embedding (Vector 1536) -> dropped (moved to Qdrant trends collection)
- project_clusters.centroid (Vector 1536) -> dropped (moved to Qdrant clusters collection)
- HNSW indexes removed: ix_papers_embedding, ix_authors_embedding_hnsw,
  ix_trend_topics_embedding_hnsw

Revision ID: qdrant_typesense_v1
Revises: pipeline_v2_consolidation_v1
Create Date: 2026-02-20 12:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "qdrant_typesense_v1"
down_revision: str | None = "pipeline_v2_consolidation_v1"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Drop HNSW indexes (must happen before dropping columns)
    # ------------------------------------------------------------------
    op.execute("DROP INDEX IF EXISTS ix_papers_embedding")
    op.execute("DROP INDEX IF EXISTS ix_authors_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_trend_topics_embedding_hnsw")

    # ------------------------------------------------------------------
    # 2. Add papers.has_embedding boolean flag
    #    Populate from existing data before dropping the vector column.
    # ------------------------------------------------------------------
    op.add_column(
        "papers",
        sa.Column(
            "has_embedding",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )
    # Backfill: mark papers that currently have embeddings
    op.execute(
        "UPDATE papers SET has_embedding = true WHERE embedding IS NOT NULL"
    )

    # ------------------------------------------------------------------
    # 3. Drop vector columns
    # ------------------------------------------------------------------
    op.drop_column("papers", "embedding")
    op.drop_column("authors", "embedding")
    op.drop_column("trend_topics", "embedding")
    op.drop_column("project_clusters", "centroid")

    # ------------------------------------------------------------------
    # 4. Add index on has_embedding for efficient filtering
    # ------------------------------------------------------------------
    op.create_index(
        "ix_papers_has_embedding",
        "papers",
        ["has_embedding"],
        postgresql_where=sa.text("has_embedding = true"),
    )


def downgrade() -> None:
    # Remove has_embedding index and column
    op.drop_index("ix_papers_has_embedding", "papers")
    op.drop_column("papers", "has_embedding")

    # Re-add vector columns (data is NOT recoverable from Qdrant in downgrade)
    op.execute(
        "ALTER TABLE papers ADD COLUMN embedding vector(1536)"
    )
    op.execute(
        "ALTER TABLE authors ADD COLUMN embedding vector(768)"
    )
    op.execute(
        "ALTER TABLE trend_topics ADD COLUMN embedding vector(1536)"
    )
    op.execute(
        "ALTER TABLE project_clusters ADD COLUMN centroid vector(1536)"
    )

    # Re-create HNSW indexes
    op.execute(
        """
        CREATE INDEX ix_papers_embedding ON papers
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )
    op.execute(
        """
        CREATE INDEX ix_authors_embedding_hnsw
        ON authors
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )
    op.execute(
        """
        CREATE INDEX ix_trend_topics_embedding_hnsw
        ON trend_topics USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )
