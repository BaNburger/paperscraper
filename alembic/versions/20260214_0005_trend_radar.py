"""Add Trend Radar tables.

Revision ID: trend_radar_v1
Revises: zotero_sync_v2
Create Date: 2026-02-14 16:00:00.000000
"""


import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "trend_radar_v1"
down_revision: str | None = "zotero_sync_v2"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create trend radar tables."""
    # trend_topics
    op.create_table(
        "trend_topics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("embedding", postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_trend_topics_organization_id",
        "trend_topics",
        ["organization_id"],
    )
    op.create_index(
        "ix_trend_topics_org_active",
        "trend_topics",
        ["organization_id", "is_active"],
    )

    # Use raw SQL for the vector column and HNSW index (pgvector)
    op.execute(
        "ALTER TABLE trend_topics ADD COLUMN IF NOT EXISTS embedding_vec vector(1536)"
    )
    op.execute(
        "UPDATE trend_topics SET embedding_vec = embedding::vector WHERE embedding IS NOT NULL"
    )
    op.execute("ALTER TABLE trend_topics DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE trend_topics RENAME COLUMN embedding_vec TO embedding")
    op.execute(
        """
        CREATE INDEX ix_trend_topics_embedding_hnsw
        ON trend_topics USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )

    # trend_snapshots
    op.create_table(
        "trend_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("trend_topic_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("matched_papers_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_novelty", sa.Float(), nullable=True),
        sa.Column("avg_ip_potential", sa.Float(), nullable=True),
        sa.Column("avg_marketability", sa.Float(), nullable=True),
        sa.Column("avg_feasibility", sa.Float(), nullable=True),
        sa.Column("avg_commercialization", sa.Float(), nullable=True),
        sa.Column("avg_team_readiness", sa.Float(), nullable=True),
        sa.Column("avg_overall_score", sa.Float(), nullable=True),
        sa.Column("patent_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "patent_results",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column(
            "key_insights",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "top_keywords",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "timeline_data",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["trend_topic_id"],
            ["trend_topics.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_trend_snapshots_topic_created",
        "trend_snapshots",
        ["trend_topic_id", "created_at"],
    )

    # trend_papers
    op.create_table(
        "trend_papers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("trend_topic_id", sa.Uuid(), nullable=False),
        sa.Column("paper_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=False),
        sa.Column(
            "matched_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["trend_topic_id"],
            ["trend_topics.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["paper_id"],
            ["papers.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trend_topic_id", "paper_id", name="uq_trend_topic_paper"),
    )
    op.create_index(
        "ix_trend_papers_topic_relevance",
        "trend_papers",
        ["trend_topic_id", "relevance_score"],
    )
    op.create_index(
        "ix_trend_papers_topic_id",
        "trend_papers",
        ["trend_topic_id"],
    )
    op.create_index(
        "ix_trend_papers_paper_id",
        "trend_papers",
        ["paper_id"],
    )


def downgrade() -> None:
    """Drop trend radar tables."""
    op.drop_table("trend_papers")
    op.drop_table("trend_snapshots")
    op.drop_index("ix_trend_topics_embedding_hnsw", "trend_topics")
    op.drop_table("trend_topics")
