"""Background jobs for research group sync and clustering."""

import logging
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


async def sync_research_group_task(
    ctx: dict[str, Any],
    organization_id: str,
    project_id: str,
    max_papers: int = 100,
) -> dict[str, Any]:
    """Import papers from OpenAlex and cluster them for a research group.

    Steps:
    1. Update sync_status → "importing"
    2. Fetch papers from OpenAlex (by institution or author filter)
    3. Import papers via PaperService (dedup by DOI)
    4. Create ProjectPaper records
    5. Update sync_status → "clustering"
    6. Generate embeddings for papers without them
    7. Run clustering algorithm
    8. Save clusters
    9. Update paper_count, cluster_count, sync_status → "ready"

    Args:
        ctx: Worker context.
        organization_id: UUID string of organization.
        project_id: UUID string of research group.
        max_papers: Maximum papers to import from OpenAlex.

    Returns:
        Dict with sync results.
    """
    from paper_scraper.core.database import get_db_session
    from paper_scraper.modules.papers.clients.openalex import OpenAlexClient
    from paper_scraper.modules.papers.models import Paper
    from paper_scraper.modules.papers.service import PaperService
    from paper_scraper.modules.projects.clustering import (
        cluster_embeddings,
        generate_cluster_label,
    )
    from paper_scraper.modules.projects.models import Project, ProjectPaper, SyncStatus
    from paper_scraper.modules.projects.service import ProjectService

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
            from sqlalchemy import func, select

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
                # Extract short ID from full URL (e.g., "https://openalex.org/I63966007" → "I63966007")
                inst_id = project.openalex_institution_id
                if "/" in inst_id:
                    inst_id = inst_id.rsplit("/", 1)[-1]
                filters["institutions.id"] = inst_id
            elif project.openalex_author_id:
                author_id = project.openalex_author_id
                if "/" in author_id:
                    author_id = author_id.rsplit("/", 1)[-1]
                filters["authorships.author.id"] = author_id
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

            # 6. Update status to clustering
            await project_service.update_sync_status(proj_uuid, org_uuid, SyncStatus.CLUSTERING)
            await db.commit()

            # 7. Get all project paper embeddings
            from paper_scraper.modules.projects.models import ProjectPaper as PP

            paper_result = await db.execute(
                select(Paper.id, Paper.embedding, Paper.keywords)
                .join(PP, PP.paper_id == Paper.id)
                .where(PP.project_id == proj_uuid)
                .where(Paper.embedding.is_not(None))
            )
            paper_rows = paper_result.all()

            total_papers_in_project = await db.scalar(
                select(func.count())
                .select_from(PP)
                .where(PP.project_id == proj_uuid)
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
                    "clusters_created": 0,
                    "message": "Not enough embeddings to cluster",
                }

            # 8. Run clustering
            paper_ids = [row[0] for row in paper_rows]
            embeddings = [list(row[1]) for row in paper_rows]
            keywords_map = {row[0]: row[2] or [] for row in paper_rows}

            assignments, centroids = cluster_embeddings(paper_ids, embeddings)

            # 9. Build cluster data
            from collections import defaultdict

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
                    "label": label,
                    "keywords": top_kws,
                    "paper_ids": pids,
                    "centroid": centroid,
                    "similarities": cluster_similarities[c_idx],
                })

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
                "Research group %s sync complete: %d papers, %d clusters",
                project.name,
                total_papers_in_project or 0,
                clusters_created,
            )

            return {
                "status": "ok",
                "papers_imported": len(imported_ids),
                "papers_added": added,
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
