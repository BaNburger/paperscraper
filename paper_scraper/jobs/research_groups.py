"""Background jobs for research group sync and clustering."""

import logging
from collections import defaultdict
from typing import Any
from uuid import UUID

from sqlalchemy import func, select

from paper_scraper.core.database import get_db_session
from paper_scraper.modules.embeddings.service import EmbeddingService
from paper_scraper.modules.ingestion.filter_builder import build_openalex_entity_filters
from paper_scraper.modules.ingestion.models import SourceRecord
from paper_scraper.modules.ingestion.pipeline import IngestionPipeline
from paper_scraper.modules.papers.models import Paper
from paper_scraper.modules.projects.clustering import (
    cluster_embeddings,
    generate_cluster_label,
    generate_cluster_labels_llm,
)
from paper_scraper.modules.projects.models import Project, ProjectPaper, SyncStatus
from paper_scraper.modules.projects.service import ProjectService

logger = logging.getLogger(__name__)

# Cap embedding generation per sync to prevent runaway API costs
MAX_EMBEDDINGS_PER_SYNC = 50


async def sync_research_group_task(
    ctx: dict[str, Any],
    organization_id: str,
    project_id: str,
    max_papers: int = 100,
) -> dict[str, Any]:
    """Import papers from OpenAlex and cluster them for a research group.

    Steps:
    1. Update sync_status -> "importing"
    2. Run OpenAlex ingestion pipeline (institution/author scoped)
    3. Read canonical run outcomes from source_records
    4. Create ProjectPaper records
    5. Generate embeddings for papers without them
    6. Update sync_status -> "clustering"
    7. Run clustering algorithm
    8. Build cluster data with keyword labels
    9. Try LLM-generated labels (single call, falls back to keywords)
    10. Save clusters
    11. Update paper_count, cluster_count, sync_status -> "ready"

    Args:
        ctx: Worker context.
        organization_id: UUID string of organization.
        project_id: UUID string of research group.
        max_papers: Maximum papers to import from OpenAlex.

    Returns:
        Dict with sync results.
    """

    org_uuid = UUID(organization_id)
    proj_uuid = UUID(project_id)

    async with get_db_session() as db:
        try:
            project_service = ProjectService(db)

            # 1. Update status to importing
            await project_service.update_sync_status(proj_uuid, org_uuid, SyncStatus.IMPORTING)
            await db.commit()

            # 2. Get project to read OpenAlex IDs (tenant-isolated)
            result = await db.execute(
                select(Project).where(
                    Project.id == proj_uuid,
                    Project.organization_id == org_uuid,
                )
            )
            project = result.scalar_one_or_none()
            if not project:
                logger.error("Research group %s not found", project_id)
                return {"status": "error", "message": "Research group not found"}

            # 3. Resolve OpenAlex filter scope from project metadata
            entity_filters = build_openalex_entity_filters(
                institution_id=project.openalex_institution_id,
                author_id=project.openalex_author_id,
            )
            if not entity_filters:
                logger.warning(
                    "Research group %s has no OpenAlex IDs, skipping import",
                    project_id,
                )
                await project_service.update_sync_status(
                    proj_uuid, org_uuid, SyncStatus.READY, paper_count=0, cluster_count=0
                )
                await db.commit()
                return {"status": "ok", "papers_imported": 0, "clusters_created": 0}

            ingest_filters = {
                "query": project.name.strip() or "research",
                "filters": entity_filters,
            }
            ingest_run = await IngestionPipeline(db).run(
                source="openalex",
                organization_id=org_uuid,
                initiated_by_id=None,
                filters=ingest_filters,
                limit=max_papers,
            )
            stats = ingest_run.stats_json if isinstance(ingest_run.stats_json, dict) else {}
            imported_count = int(stats.get("papers_created", 0))
            matched_count = int(stats.get("papers_matched", 0))
            duplicate_count = int(stats.get("source_records_duplicates", 0))
            fetched_count = int(stats.get("fetched_records", imported_count + matched_count))
            run_errors = stats.get("errors")
            error_count = len(run_errors) if isinstance(run_errors, list) else 0

            run_records = await db.execute(
                select(SourceRecord.paper_id)
                .where(
                    SourceRecord.ingest_run_id == ingest_run.id,
                    SourceRecord.organization_id == org_uuid,
                    SourceRecord.paper_id.is_not(None),
                )
                .distinct()
            )
            imported_ids = [row[0] for row in run_records.all() if row[0] is not None]

            logger.info(
                "OpenAlex ingestion run %s for group %s fetched=%d created=%d matched=%d duplicates=%d errors=%d",
                ingest_run.id,
                project.name,
                fetched_count,
                imported_count,
                matched_count,
                duplicate_count,
                error_count,
            )

            # 5. Add papers to project (tenant-isolated)
            added = await project_service.add_papers_to_project(
                project_id=proj_uuid,
                organization_id=org_uuid,
                paper_ids=imported_ids,
            )
            await db.commit()

            logger.info(
                "Added %d papers to research group %s (of %d resolved)",
                added,
                project.name,
                len(imported_ids),
            )

            # 5b. Generate embeddings for project papers that lack them
            embeddings_generated = await _generate_missing_embeddings(
                db,
                proj_uuid,
                org_uuid,
                project.name,
            )

            # 6. Update status to clustering
            await project_service.update_sync_status(proj_uuid, org_uuid, SyncStatus.CLUSTERING)
            await db.commit()

            # 7. Get all project paper embeddings
            paper_result = await db.execute(
                select(Paper.id, Paper.embedding, Paper.keywords)
                .join(ProjectPaper, ProjectPaper.paper_id == Paper.id)
                .where(ProjectPaper.project_id == proj_uuid)
                .where(Paper.embedding.is_not(None))
            )
            paper_rows = paper_result.all()

            total_papers_in_project = await db.scalar(
                select(func.count())
                .select_from(ProjectPaper)
                .where(ProjectPaper.project_id == proj_uuid)
            )

            if len(paper_rows) < 2:
                logger.info(
                    "Not enough papers with embeddings (%d) to cluster for %s",
                    len(paper_rows),
                    project.name,
                )
                await project_service.update_sync_status(
                    proj_uuid,
                    org_uuid,
                    SyncStatus.READY,
                    paper_count=total_papers_in_project or 0,
                    cluster_count=0,
                )
                await db.commit()
                return {
                    "status": "ok",
                    "papers_imported": imported_count,
                    "papers_added": added,
                    "embeddings_generated": embeddings_generated,
                    "clusters_created": 0,
                    "message": "Not enough embeddings to cluster",
                }

            # 8. Run clustering
            paper_ids = [row[0] for row in paper_rows]
            embeddings = [list(row[1]) for row in paper_rows]
            keywords_map = {row[0]: row[2] or [] for row in paper_rows}

            assignments, centroids = cluster_embeddings(paper_ids, embeddings)

            # 9. Build cluster data (keyword labels as default)
            cluster_papers: dict[int, list[UUID]] = defaultdict(list)
            cluster_similarities: dict[int, dict[UUID, float]] = defaultdict(dict)
            for assignment in assignments:
                cluster_papers[assignment.cluster_index].append(assignment.paper_id)
                cluster_similarities[assignment.cluster_index][
                    assignment.paper_id
                ] = assignment.similarity_score

            cluster_data = []
            for c_idx in sorted(cluster_papers.keys()):
                pids = cluster_papers[c_idx]
                kws_per_paper = [keywords_map.get(pid, []) for pid in pids]
                label, top_kws = generate_cluster_label(kws_per_paper)

                centroid = centroids[c_idx] if c_idx < len(centroids) else None

                cluster_data.append({
                    "cluster_index": c_idx,
                    "label": label,
                    "description": None,
                    "keywords": top_kws,
                    "paper_ids": pids,
                    "centroid": centroid,
                    "similarities": cluster_similarities[c_idx],
                })

            # 9b. Try LLM-generated labels (single call for all clusters)
            await _try_llm_labels(db, cluster_data)

            # 10. Save clusters
            clusters_created = await project_service.save_clusters(
                project_id=proj_uuid,
                organization_id=org_uuid,
                cluster_data=cluster_data,
            )

            # 11. Update final status
            await project_service.update_sync_status(
                proj_uuid,
                org_uuid,
                SyncStatus.READY,
                paper_count=total_papers_in_project or 0,
                cluster_count=clusters_created,
            )
            await db.commit()

            logger.info(
                "Research group %s sync complete: %d papers, %d clusters, %d embeddings generated",
                project.name,
                total_papers_in_project or 0,
                clusters_created,
                embeddings_generated,
            )

            return {
                "status": "ok",
                "papers_imported": imported_count,
                "papers_added": added,
                "embeddings_generated": embeddings_generated,
                "total_papers": total_papers_in_project or 0,
                "clusters_created": clusters_created,
            }

        except Exception as exc:
            logger.exception(
                "Research group sync failed for %s: %s", project_id, exc
            )
            try:
                await db.rollback()
                project_service_err = ProjectService(db)
                await project_service_err.update_sync_status(
                    proj_uuid, org_uuid, SyncStatus.FAILED
                )
                await db.commit()
            except Exception:
                logger.warning("Failed to update sync status to FAILED for %s", project_id)
            return {"status": "error", "message": "Sync failed. Check logs for details."}


async def _generate_missing_embeddings(
    db: Any,
    project_id: UUID,
    organization_id: UUID,
    project_name: str,
) -> int:
    """Generate embeddings for project papers that lack them.

    Returns the number of embeddings generated.
    """
    embedding_service = EmbeddingService(db)
    summary = await embedding_service.backfill_for_project(
        project_id=project_id,
        organization_id=organization_id,
        batch_size=min(MAX_EMBEDDINGS_PER_SYNC, 100),
        max_papers=MAX_EMBEDDINGS_PER_SYNC,
    )

    if summary.papers_processed == 0:
        return 0

    if summary.papers_failed > 0:
        logger.warning(
            "Embedding backfill for group %s completed with failures (%d/%d)",
            project_name,
            summary.papers_failed,
            summary.papers_processed,
        )

    logger.info(
        "Generated %d embeddings for group %s",
        summary.papers_succeeded,
        project_name,
    )
    return summary.papers_succeeded


async def _try_llm_labels(db: Any, cluster_data: list[dict]) -> None:
    """Try to generate LLM labels for clusters. Modifies cluster_data in place.

    Falls back silently to existing keyword-based labels on any failure.
    """
    try:
        from paper_scraper.modules.scoring.llm_client import get_llm_client
    except ImportError:
        logger.debug("LLM client not available, using keyword labels")
        return

    try:
        # Build LLM input with paper titles
        llm_input = []
        for cdata in cluster_data:
            pids = cdata["paper_ids"]
            title_result = await db.execute(
                select(Paper.title).where(Paper.id.in_(pids)).limit(5)
            )
            titles = [row[0] or "Untitled" for row in title_result.all()]
            llm_input.append({
                "index": cdata["cluster_index"],
                "keywords": cdata["keywords"],
                "paper_titles": titles,
            })

        llm_client = get_llm_client()
        llm_labels = await generate_cluster_labels_llm(llm_input, llm_client)

        if llm_labels:
            label_map = {item["index"]: item for item in llm_labels}
            for cdata in cluster_data:
                llm_item = label_map.get(cdata["cluster_index"])
                if llm_item:
                    cdata["label"] = llm_item["label"]
                    cdata["description"] = llm_item.get("description")
    except Exception as e:
        logger.debug("LLM cluster labeling skipped: %s", e)
