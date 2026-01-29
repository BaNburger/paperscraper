"""Add papers and authors models

Revision ID: a1b2c3d4e5f6
Revises: 51fca12defc7
Create Date: 2026-01-29 00:01:00.000000+00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "51fca12defc7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Enable pgvector extension for vector similarity search
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Enable pg_trgm extension for full-text search
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Create paper source enum
    paper_source = postgresql.ENUM(
        "doi",
        "openalex",
        "pubmed",
        "arxiv",
        "crossref",
        "semantic_scholar",
        "manual",
        "pdf",
        name="papersource",
        create_type=False,
    )
    paper_source.create(op.get_bind(), checkfirst=True)

    # Create authors table
    op.create_table(
        "authors",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("orcid", sa.String(50), nullable=True, unique=True),
        sa.Column("openalex_id", sa.String(100), nullable=True, unique=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column(
            "affiliations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("h_index", sa.Integer, nullable=True),
        sa.Column("citation_count", sa.Integer, nullable=True),
        sa.Column("works_count", sa.Integer, nullable=True),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Create papers table
    op.create_table(
        "papers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("doi", sa.String(255), nullable=True),
        sa.Column("source", paper_source, nullable=False),
        sa.Column("source_id", sa.String(255), nullable=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("abstract", sa.Text, nullable=True),
        sa.Column("publication_date", sa.DateTime, nullable=True),
        sa.Column("journal", sa.String(500), nullable=True),
        sa.Column("volume", sa.String(50), nullable=True),
        sa.Column("issue", sa.String(50), nullable=True),
        sa.Column("pages", sa.String(50), nullable=True),
        sa.Column(
            "keywords",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "mesh_terms",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("references_count", sa.Integer, nullable=True),
        sa.Column("citations_count", sa.Integer, nullable=True),
        sa.Column("pdf_path", sa.String(500), nullable=True),
        sa.Column("full_text", sa.Text, nullable=True),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column(
            "raw_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Create paper_authors junction table
    op.create_table(
        "paper_authors",
        sa.Column(
            "paper_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("papers.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "author_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("authors.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "is_corresponding", sa.Boolean, nullable=False, server_default="false"
        ),
    )

    # Create indexes for papers table
    op.create_index("ix_papers_organization_id", "papers", ["organization_id"])
    op.create_index("ix_papers_doi", "papers", ["doi"])
    op.create_index("ix_papers_source_source_id", "papers", ["source", "source_id"])
    op.create_index(
        "ix_papers_org_created", "papers", ["organization_id", "created_at"]
    )

    # Create HNSW index for vector similarity search on papers
    op.execute(
        """
        CREATE INDEX ix_papers_embedding ON papers
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """
    )

    # Create trigram indexes for full-text search
    op.execute(
        "CREATE INDEX ix_papers_title_trgm ON papers USING gin (title gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_papers_abstract_trgm ON papers USING gin (abstract gin_trgm_ops)"
    )

    # Create updated_at triggers for new tables
    op.execute(
        """
        CREATE TRIGGER update_authors_updated_at
            BEFORE UPDATE ON authors
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """
    )
    op.execute(
        """
        CREATE TRIGGER update_papers_updated_at
            BEFORE UPDATE ON papers
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_papers_updated_at ON papers")
    op.execute("DROP TRIGGER IF EXISTS update_authors_updated_at ON authors")

    # Drop trigram indexes
    op.execute("DROP INDEX IF EXISTS ix_papers_abstract_trgm")
    op.execute("DROP INDEX IF EXISTS ix_papers_title_trgm")

    # Drop HNSW index
    op.execute("DROP INDEX IF EXISTS ix_papers_embedding")

    # Drop regular indexes
    op.drop_index("ix_papers_org_created", table_name="papers")
    op.drop_index("ix_papers_source_source_id", table_name="papers")
    op.drop_index("ix_papers_doi", table_name="papers")
    op.drop_index("ix_papers_organization_id", table_name="papers")

    # Drop tables
    op.drop_table("paper_authors")
    op.drop_table("papers")
    op.drop_table("authors")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS papersource")

    # Note: We don't drop pg_trgm and vector extensions as they might be used elsewhere
