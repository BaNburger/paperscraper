"""Pipeline v2 consolidation: dedupe hardening, ledger fields, and endpoint cleanup.

Revision ID: pipeline_v2_consolidation_v1
Revises: model_key_encryption_v1
Create Date: 2026-02-18 10:30:00.000000
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "pipeline_v2_consolidation_v1"
down_revision: str | None = "model_key_encryption_v1"
branch_labels: str | None = None
depends_on: str | None = None


def _table_exists(connection: Connection, table_name: str) -> bool:
    inspector = sa.inspect(connection)
    return table_name in inspector.get_table_names()


def _column_exists(connection: Connection, table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(connection)
    return any(column.get("name") == column_name for column in inspector.get_columns(table_name))


def _index_exists(connection: Connection, table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(connection)
    return any(index.get("name") == index_name for index in inspector.get_indexes(table_name))


def _constraint_exists(connection: Connection, table_name: str, constraint_name: str) -> bool:
    inspector = sa.inspect(connection)
    return any(
        constraint.get("name") == constraint_name
        for constraint in inspector.get_unique_constraints(table_name)
    )


def _foreign_key_exists(connection: Connection, table_name: str, constraint_name: str) -> bool:
    inspector = sa.inspect(connection)
    return any(fk.get("name") == constraint_name for fk in inspector.get_foreign_keys(table_name))


def _find(parent: dict[str, str], value: str) -> str:
    parent.setdefault(value, value)
    root = value
    while parent[root] != root:
        root = parent[root]
    while parent[value] != value:
        next_value = parent[value]
        parent[value] = root
        value = next_value
    return root


def _union(parent: dict[str, str], canonical: str, duplicate: str) -> None:
    canonical_root = _find(parent, canonical)
    duplicate_root = _find(parent, duplicate)
    if canonical_root != duplicate_root:
        parent[duplicate_root] = canonical_root


def _collect_duplicate_groups(
    connection: Connection,
    query: str,
) -> list[list[str]]:
    rows = connection.execute(sa.text(query)).mappings().all()
    groups: list[list[str]] = []
    for row in rows:
        ids = row.get("ids")
        if isinstance(ids, list):
            normalized = [str(item) for item in ids if item is not None]
            if len(normalized) > 1:
                groups.append(normalized)
    return groups


def _build_paper_merge_map(connection: Connection) -> dict[str, str]:
    """Build duplicate->canonical mapping from DOI and source identity groups."""
    parent: dict[str, str] = {}

    doi_groups = _collect_duplicate_groups(
        connection,
        """
        SELECT
            organization_id,
            lower(btrim(doi)) AS normalized_doi,
            array_agg(id::text ORDER BY created_at ASC, id ASC) AS ids
        FROM papers
        WHERE doi IS NOT NULL AND btrim(doi) <> ''
        GROUP BY organization_id, lower(btrim(doi))
        HAVING count(*) > 1
        """,
    )
    for ids in doi_groups:
        keep = ids[0]
        for duplicate in ids[1:]:
            _union(parent, keep, duplicate)

    source_groups = _collect_duplicate_groups(
        connection,
        """
        SELECT
            organization_id,
            source,
            source_id,
            array_agg(id::text ORDER BY created_at ASC, id ASC) AS ids
        FROM papers
        WHERE source_id IS NOT NULL AND btrim(source_id) <> ''
        GROUP BY organization_id, source, source_id
        HAVING count(*) > 1
        """,
    )
    for ids in source_groups:
        keep = _find(parent, ids[0])
        for duplicate in ids[1:]:
            _union(parent, keep, duplicate)

    mapping: dict[str, str] = {}
    for value in list(parent.keys()):
        resolved = _find(parent, value)
        if resolved != value:
            mapping[value] = resolved
    return mapping


def _run_conflict_safe_remap(
    connection: Connection,
    *,
    table_name: str,
    delete_stmt: str,
    update_stmt: str,
    params: dict[str, Any],
) -> None:
    if not _table_exists(connection, table_name):
        return
    connection.execute(sa.text(delete_stmt), params)
    connection.execute(sa.text(update_stmt), params)


def _run_simple_remap(
    connection: Connection,
    *,
    table_name: str,
    column_name: str,
    params: dict[str, Any],
) -> None:
    if not _table_exists(connection, table_name):
        return
    if not _column_exists(connection, table_name, column_name):
        return
    connection.execute(
        sa.text(
            f"""
            UPDATE {table_name}
            SET {column_name} = :canonical_id
            WHERE {column_name} = :duplicate_id
            """
        ),
        params,
    )


def _remap_paper_references(
    connection: Connection,
    *,
    duplicate_id: str,
    canonical_id: str,
) -> None:
    params = {"duplicate_id": duplicate_id, "canonical_id": canonical_id}

    _run_conflict_safe_remap(
        connection,
        table_name="paper_authors",
        delete_stmt="""
            DELETE FROM paper_authors dup
            USING paper_authors keep
            WHERE dup.paper_id = :duplicate_id
              AND keep.paper_id = :canonical_id
              AND dup.author_id = keep.author_id
        """,
        update_stmt="""
            UPDATE paper_authors
            SET paper_id = :canonical_id
            WHERE paper_id = :duplicate_id
        """,
        params=params,
    )
    _run_conflict_safe_remap(
        connection,
        table_name="project_papers",
        delete_stmt="""
            DELETE FROM project_papers dup
            USING project_papers keep
            WHERE dup.paper_id = :duplicate_id
              AND keep.paper_id = :canonical_id
              AND dup.project_id = keep.project_id
        """,
        update_stmt="""
            UPDATE project_papers
            SET paper_id = :canonical_id
            WHERE paper_id = :duplicate_id
        """,
        params=params,
    )
    _run_conflict_safe_remap(
        connection,
        table_name="project_cluster_papers",
        delete_stmt="""
            DELETE FROM project_cluster_papers dup
            USING project_cluster_papers keep
            WHERE dup.paper_id = :duplicate_id
              AND keep.paper_id = :canonical_id
              AND dup.cluster_id = keep.cluster_id
        """,
        update_stmt="""
            UPDATE project_cluster_papers
            SET paper_id = :canonical_id
            WHERE paper_id = :duplicate_id
        """,
        params=params,
    )
    _run_conflict_safe_remap(
        connection,
        table_name="library_collection_items",
        delete_stmt="""
            DELETE FROM library_collection_items dup
            USING library_collection_items keep
            WHERE dup.paper_id = :duplicate_id
              AND keep.paper_id = :canonical_id
              AND dup.collection_id = keep.collection_id
        """,
        update_stmt="""
            UPDATE library_collection_items
            SET paper_id = :canonical_id
            WHERE paper_id = :duplicate_id
        """,
        params=params,
    )
    _run_conflict_safe_remap(
        connection,
        table_name="paper_tags",
        delete_stmt="""
            DELETE FROM paper_tags dup
            USING paper_tags keep
            WHERE dup.paper_id = :duplicate_id
              AND keep.paper_id = :canonical_id
              AND dup.organization_id = keep.organization_id
              AND dup.tag = keep.tag
        """,
        update_stmt="""
            UPDATE paper_tags
            SET paper_id = :canonical_id
            WHERE paper_id = :duplicate_id
        """,
        params=params,
    )
    _run_conflict_safe_remap(
        connection,
        table_name="paper_text_chunks",
        delete_stmt="""
            DELETE FROM paper_text_chunks dup
            USING paper_text_chunks keep
            WHERE dup.paper_id = :duplicate_id
              AND keep.paper_id = :canonical_id
              AND dup.chunk_index = keep.chunk_index
        """,
        update_stmt="""
            UPDATE paper_text_chunks
            SET paper_id = :canonical_id
            WHERE paper_id = :duplicate_id
        """,
        params=params,
    )
    _run_conflict_safe_remap(
        connection,
        table_name="paper_context_snapshots",
        delete_stmt="""
            DELETE FROM paper_context_snapshots dup
            USING paper_context_snapshots keep
            WHERE dup.paper_id = :duplicate_id
              AND keep.paper_id = :canonical_id
              AND dup.organization_id = keep.organization_id
              AND dup.enrichment_version = keep.enrichment_version
        """,
        update_stmt="""
            UPDATE paper_context_snapshots
            SET paper_id = :canonical_id
            WHERE paper_id = :duplicate_id
        """,
        params=params,
    )
    _run_conflict_safe_remap(
        connection,
        table_name="trend_papers",
        delete_stmt="""
            DELETE FROM trend_papers dup
            USING trend_papers keep
            WHERE dup.paper_id = :duplicate_id
              AND keep.paper_id = :canonical_id
              AND dup.trend_topic_id = keep.trend_topic_id
        """,
        update_stmt="""
            UPDATE trend_papers
            SET paper_id = :canonical_id
            WHERE paper_id = :duplicate_id
        """,
        params=params,
    )
    _run_conflict_safe_remap(
        connection,
        table_name="zotero_item_links",
        delete_stmt="""
            DELETE FROM zotero_item_links dup
            USING zotero_item_links keep
            WHERE dup.paper_id = :duplicate_id
              AND keep.paper_id = :canonical_id
              AND dup.organization_id = keep.organization_id
              AND dup.zotero_item_key = keep.zotero_item_key
        """,
        update_stmt="""
            UPDATE zotero_item_links
            SET paper_id = :canonical_id
            WHERE paper_id = :duplicate_id
        """,
        params=params,
    )

    for table_name, column_name in [
        ("paper_scores", "paper_id"),
        ("paper_notes", "paper_id"),
        ("paper_highlights", "paper_id"),
        ("source_records", "paper_id"),
        ("transfer_conversations", "paper_id"),
        ("author_contacts", "paper_id"),
        ("research_submissions", "converted_paper_id"),
    ]:
        _run_simple_remap(
            connection,
            table_name=table_name,
            column_name=column_name,
            params=params,
        )


def _merge_duplicate_papers(connection: Connection) -> None:
    if not _table_exists(connection, "papers"):
        return

    connection.execute(
        sa.text("UPDATE papers SET doi = NULL WHERE doi IS NOT NULL AND btrim(doi) = ''")
    )
    connection.execute(
        sa.text(
            "UPDATE papers SET source_id = NULL WHERE source_id IS NOT NULL AND btrim(source_id) = ''"
        )
    )

    merge_map = _build_paper_merge_map(connection)
    if not merge_map:
        return

    processed: set[str] = set()
    for duplicate_id, canonical_id in sorted(merge_map.items()):
        if duplicate_id == canonical_id or duplicate_id in processed:
            continue
        _remap_paper_references(
            connection,
            duplicate_id=duplicate_id,
            canonical_id=canonical_id,
        )
        connection.execute(
            sa.text("DELETE FROM papers WHERE id = :duplicate_id"),
            {"duplicate_id": duplicate_id},
        )
        processed.add(duplicate_id)


def _create_indexes(connection: Connection, statements: Iterable[str]) -> None:
    for statement in statements:
        connection.execute(sa.text(statement))


def upgrade() -> None:
    connection = op.get_bind()

    # ------------------------------------------------------------------
    # Source record ledger + tenant-safe uniqueness
    # ------------------------------------------------------------------
    if _table_exists(connection, "source_records"):
        if not _column_exists(connection, "source_records", "paper_id"):
            op.add_column("source_records", sa.Column("paper_id", sa.Uuid(), nullable=True))
        if not _foreign_key_exists(connection, "source_records", "fk_source_records_paper_id"):
            op.create_foreign_key(
                "fk_source_records_paper_id",
                "source_records",
                "papers",
                ["paper_id"],
                ["id"],
                ondelete="SET NULL",
            )
        if not _index_exists(connection, "source_records", "ix_source_records_paper_id"):
            op.create_index("ix_source_records_paper_id", "source_records", ["paper_id"])

        if not _column_exists(connection, "source_records", "resolution_status"):
            op.add_column(
                "source_records",
                sa.Column("resolution_status", sa.String(length=32), nullable=True),
            )
        if not _column_exists(connection, "source_records", "matched_on"):
            op.add_column(
                "source_records", sa.Column("matched_on", sa.String(length=64), nullable=True)
            )
        if not _column_exists(connection, "source_records", "resolution_error"):
            op.add_column("source_records", sa.Column("resolution_error", sa.Text(), nullable=True))
        if not _column_exists(connection, "source_records", "resolved_at"):
            op.add_column(
                "source_records",
                sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
            )

        if not _index_exists(connection, "source_records", "ix_source_records_resolution_status"):
            op.create_index(
                "ix_source_records_resolution_status",
                "source_records",
                ["resolution_status"],
            )
        if not _index_exists(connection, "source_records", "ix_source_records_run_resolution"):
            op.create_index(
                "ix_source_records_run_resolution",
                "source_records",
                ["ingest_run_id", "resolution_status"],
            )

        # Backfill organization_id from ingest_runs and enforce non-null
        connection.execute(
            sa.text(
                """
                UPDATE source_records sr
                SET organization_id = ir.organization_id
                FROM ingest_runs ir
                WHERE sr.ingest_run_id = ir.id
                  AND sr.organization_id IS NULL
                  AND ir.organization_id IS NOT NULL
                """
            )
        )
        connection.execute(sa.text("DELETE FROM source_records WHERE organization_id IS NULL"))
        op.alter_column("source_records", "organization_id", nullable=False)

        if _constraint_exists(connection, "source_records", "uq_source_records_source_id_hash"):
            op.drop_constraint(
                "uq_source_records_source_id_hash",
                "source_records",
                type_="unique",
            )
        if not _constraint_exists(
            connection, "source_records", "uq_source_records_org_source_id_hash"
        ):
            op.create_unique_constraint(
                "uq_source_records_org_source_id_hash",
                "source_records",
                ["organization_id", "source", "source_record_id", "content_hash"],
            )

    # ------------------------------------------------------------------
    # Discovery <-> ingestion linkage
    # ------------------------------------------------------------------
    if _table_exists(connection, "discovery_runs"):
        if not _column_exists(connection, "discovery_runs", "ingest_run_id"):
            op.add_column("discovery_runs", sa.Column("ingest_run_id", sa.Uuid(), nullable=True))
        if not _foreign_key_exists(connection, "discovery_runs", "fk_discovery_runs_ingest_run_id"):
            op.create_foreign_key(
                "fk_discovery_runs_ingest_run_id",
                "discovery_runs",
                "ingest_runs",
                ["ingest_run_id"],
                ["id"],
                ondelete="SET NULL",
            )
        if not _index_exists(connection, "discovery_runs", "ix_discovery_runs_ingest_run_id"):
            op.create_index(
                "ix_discovery_runs_ingest_run_id",
                "discovery_runs",
                ["ingest_run_id"],
            )

    # ------------------------------------------------------------------
    # Paper dedupe remediation + strict uniqueness indexes
    # ------------------------------------------------------------------
    _merge_duplicate_papers(connection)
    if _table_exists(connection, "papers"):
        _create_indexes(
            connection,
            [
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_papers_org_lower_doi
                ON papers (organization_id, lower(doi))
                WHERE doi IS NOT NULL
                """,
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_papers_org_source_source_id
                ON papers (organization_id, source, source_id)
                WHERE source_id IS NOT NULL
                """,
            ],
        )

    # ------------------------------------------------------------------
    # Remove scoring policy runtime layer table
    # ------------------------------------------------------------------
    if _table_exists(connection, "scoring_policies"):
        connection.execute(sa.text("DROP TABLE IF EXISTS scoring_policies CASCADE"))


def downgrade() -> None:
    connection = op.get_bind()

    if _table_exists(connection, "papers"):
        connection.execute(sa.text("DROP INDEX IF EXISTS uq_papers_org_source_source_id"))
        connection.execute(sa.text("DROP INDEX IF EXISTS uq_papers_org_lower_doi"))

    if _table_exists(connection, "discovery_runs"):
        if _index_exists(connection, "discovery_runs", "ix_discovery_runs_ingest_run_id"):
            op.drop_index("ix_discovery_runs_ingest_run_id", table_name="discovery_runs")
        if _foreign_key_exists(connection, "discovery_runs", "fk_discovery_runs_ingest_run_id"):
            op.drop_constraint(
                "fk_discovery_runs_ingest_run_id",
                "discovery_runs",
                type_="foreignkey",
            )
        if _column_exists(connection, "discovery_runs", "ingest_run_id"):
            op.drop_column("discovery_runs", "ingest_run_id")

    if _table_exists(connection, "source_records"):
        if _constraint_exists(connection, "source_records", "uq_source_records_org_source_id_hash"):
            op.drop_constraint(
                "uq_source_records_org_source_id_hash",
                "source_records",
                type_="unique",
            )
        if not _constraint_exists(connection, "source_records", "uq_source_records_source_id_hash"):
            op.create_unique_constraint(
                "uq_source_records_source_id_hash",
                "source_records",
                ["source", "source_record_id", "content_hash"],
            )

        op.alter_column("source_records", "organization_id", nullable=True)

        if _index_exists(connection, "source_records", "ix_source_records_run_resolution"):
            op.drop_index("ix_source_records_run_resolution", table_name="source_records")
        if _index_exists(connection, "source_records", "ix_source_records_resolution_status"):
            op.drop_index("ix_source_records_resolution_status", table_name="source_records")

        if _foreign_key_exists(connection, "source_records", "fk_source_records_paper_id"):
            op.drop_constraint("fk_source_records_paper_id", "source_records", type_="foreignkey")
        if _index_exists(connection, "source_records", "ix_source_records_paper_id"):
            op.drop_index("ix_source_records_paper_id", table_name="source_records")

        for column_name in [
            "resolved_at",
            "resolution_error",
            "matched_on",
            "resolution_status",
            "paper_id",
        ]:
            if _column_exists(connection, "source_records", column_name):
                op.drop_column("source_records", column_name)

    if not _table_exists(connection, "scoring_policies"):
        op.create_table(
            "scoring_policies",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("organization_id", sa.Uuid(), nullable=False),
            sa.Column("provider", sa.String(length=50), nullable=False),
            sa.Column("model", sa.String(length=200), nullable=False),
            sa.Column("temperature", sa.Float(), nullable=False, server_default=sa.text("0.3")),
            sa.Column("max_tokens", sa.Integer(), nullable=False, server_default=sa.text("4096")),
            sa.Column("secret_ref", sa.String(length=255), nullable=True),
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_scoring_policies_organization_id",
            "scoring_policies",
            ["organization_id"],
        )
        op.create_index(
            "ix_scoring_policies_org_default",
            "scoring_policies",
            ["organization_id", "is_default"],
        )
