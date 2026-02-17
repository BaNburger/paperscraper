"""Background jobs for research group sync and clustering."""

import logging
from collections import defaultdict
from typing import Any
from uuid import UUID

from sqlalchemy import func, select

from paper_scraper.core.database import get_db_session
from paper_scraper.modules.papers.clients.openalex import OpenAlexClient
from paper_scraper.modules.papers.models import Paper
from paper_scraper.modules.papers.service import PaperService
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


def _extract_short_id(openalex_url: str) -> str:
    """Extract short ID from OpenAlex URL (e.g., 'https://openalex.org/I63966007' -> 'I63966007')."""
    if "/" in openalex_url:
        return openalex_url.rsplit("/", 1)[-1]
    return openalex_url


async def sync_research_group_task(
    ctx: dict[str, Any],
    organization_id: str,
    project_id: str,
    max_papers: int = 100,
) -> dict[str, Any]:
    """Import papers from OpenAlex and cluster them for a research group.

    Steps:
    1. Update sync_status -> "importing"
    2. Fetch papers from OpenAlex (by institution or author filter)
    3. Import papers via PaperService (dedup by DOI)
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
            paper_service = PaperService(db)

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

            # 3. Fetch papers from OpenAlex
            filters: dict[str, str] = {}
            if project.openalex_institution_id:
                filters["institutions.id"] = _extract_short_id(project.openalex_institution_id)
            elif project.openalex_author_id:
                filters["authorships.author.id"] = _extract_short_id(project.openalex_author_id)
            else:
                logger.warning(
                    "Research group %s has no OpenAlex IDs, skipping import",
                    project_id,
                )
                await project_service.update_sync_status(
                    proj_uuid, org_uuid, SyncStatus.READY, paper_count=0, cluster_count=0
                )
                await db.commit()
                return {"status": "ok", "papers_imported": 0, "clusters_created": 0}

            async with OpenAlexClient() as client:
                openalex_papers = await client.search(
                    "", max_results=max_papers, filters=filters
                )

            logger.info(
                "Fetched %d papers from OpenAlex for group %s",
                len(openalex_papers),
                project.name,
            )

            # 4. Import papers (dedup by DOI, reuse existing)
            imported_ids: list[UUID] = []
            for paper_data in openalex_papers:
                try:
                    doi = paper_data.get("doi")
                    if doi:
                        existing = await paper_service.get_paper_by_doi(
                            doi, org_uuid
                        )
                        if existing:
                            imported_ids.append(existing.id)
                            continue

                    paper = await paper_service._create_paper_from_data(
                        paper_data, org_uuid
                    )
                    imported_ids.append(paper.id)
                except Exception as e:
                    logger.debug("Skipping paper import: %s", e)

            await db.flush()

            # 5. Add papers to project (tenant-isolated)
            added = await project_service.add_papers_to_project(
                project_id=proj_uuid,
                organization_id=org_uuid,
                paper_ids=imported_ids,
            )
            await db.commit()

            logger.info(
                "Added %d papers to research group %s (of %d fetched)",
                added,
                project.name,
                len(openalex_papers),
            )

            # 5b. Generate embeddings for project papers that lack them
            embeddings_generated = await _generate_missing_embeddings(
                db, proj_uuid, project.name
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
                    "papers_imported": len(imported_ids),
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
                "papers_imported": len(imported_ids),
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
    project_name: str,
) -> int:
    """Generate embeddings for project papers that lack them.

    Returns the number of embeddings generated.
    """
    try:
        from paper_scraper.modules.scoring.embeddings import generate_paper_embedding
    except ImportError:
        logger.debug("Embedding module not available, skipping embedding generation")
        return 0

    result = await db.execute(
        select(Paper)
        .join(ProjectPaper, ProjectPaper.paper_id == Paper.id)
        .where(
            ProjectPaper.project_id == project_id,
            Paper.embedding.is_(None),
        )
        .limit(MAX_EMBEDDINGS_PER_SYNC)
    )
    papers_to_embed = list(result.scalars().all())

    if not papers_to_embed:
        return 0

    logger.info(
        "Generating embeddings for %d papers in group %s",
        len(papers_to_embed),
        project_name,
    )

    generated = 0
    for paper in papers_to_embed:
        try:
            embedding = await generate_paper_embedding(
                title=paper.title or "",
                abstract=paper.abstract,
                keywords=paper.keywords,
            )
            paper.embedding = embedding
            generated += 1
        except Exception as e:
            logger.debug("Embedding generation failed for paper %s: %s", paper.id, e)

    if generated > 0:
        await db.flush()
        logger.info(
            "Generated %d embeddings for group %s",
            generated,
            project_name,
        )

    return generated


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
