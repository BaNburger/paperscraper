"""Service layer for research groups module."""

import logging
from collections import defaultdict
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.core.sql_utils import escape_like
from paper_scraper.modules.papers.models import Author, Paper, PaperAuthor
from paper_scraper.modules.projects.models import (
    Project,
    ProjectCluster,
    ProjectClusterPaper,
    ProjectPaper,
    SyncStatus,
)
from paper_scraper.modules.projects.schemas import (
    ClusterDetailResponse,
    ClusterPaperSummary,
    ClusterResponse,
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for research group management and clustering."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Research Group CRUD
    # =========================================================================

    async def create_project(
        self,
        data: ProjectCreate,
        organization_id: UUID,
    ) -> Project:
        """Create a new research group."""
        project = Project(
            organization_id=organization_id,
            name=data.name,
            description=data.description,
            institution_name=data.institution_name,
            openalex_institution_id=data.openalex_institution_id,
            pi_name=data.pi_name,
            openalex_author_id=data.openalex_author_id,
            sync_status=SyncStatus.IDLE.value,
            settings={"max_papers": data.max_papers},
        )
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def get_project(
        self,
        project_id: UUID,
        organization_id: UUID,
    ) -> Project | None:
        """Get a research group by ID with tenant isolation."""
        result = await self.db.execute(
            select(Project).where(
                Project.id == project_id,
                Project.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_projects(
        self,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> ProjectListResponse:
        """List research groups with pagination."""
        query = select(Project).where(Project.organization_id == organization_id)

        if search:
            search_filter = f"%{escape_like(search)}%"
            query = query.where(Project.name.ilike(search_filter, escape="\\"))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(Project.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        projects = list(result.scalars().all())

        return ProjectListResponse(
            items=[ProjectResponse.model_validate(p) for p in projects],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size if total > 0 else 0,
        )

    async def update_project(
        self,
        project_id: UUID,
        organization_id: UUID,
        data: ProjectUpdate,
    ) -> Project:
        """Update a research group."""
        project = await self.get_project(project_id, organization_id)
        if not project:
            raise NotFoundError("Project", str(project_id))

        allowed_fields = {"name", "description"}
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key in allowed_fields:
                setattr(project, key, value)

        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def delete_project(
        self,
        project_id: UUID,
        organization_id: UUID,
    ) -> None:
        """Delete a research group and all its clusters."""
        project = await self.get_project(project_id, organization_id)
        if not project:
            raise NotFoundError("Project", str(project_id))

        await self.db.delete(project)
        await self.db.flush()

    # =========================================================================
    # Sync Management
    # =========================================================================

    async def start_sync(
        self,
        project_id: UUID,
        organization_id: UUID,
    ) -> Project:
        """Mark a research group as syncing and return it."""
        project = await self.get_project(project_id, organization_id)
        if not project:
            raise NotFoundError("Project", str(project_id))

        project.sync_status = SyncStatus.IMPORTING.value
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def update_sync_status(
        self,
        project_id: UUID,
        organization_id: UUID,
        status: SyncStatus,
        paper_count: int | None = None,
        cluster_count: int | None = None,
    ) -> None:
        """Update sync status and counts for a research group (tenant-isolated)."""
        result = await self.db.execute(
            select(Project).where(
                Project.id == project_id,
                Project.organization_id == organization_id,
            )
        )
        project = result.scalar_one_or_none()
        if not project:
            return

        project.sync_status = status.value
        if paper_count is not None:
            project.paper_count = paper_count
        if cluster_count is not None:
            project.cluster_count = cluster_count
        if status == SyncStatus.READY:
            project.last_synced_at = datetime.now(UTC)

        await self.db.flush()

    # =========================================================================
    # Paper Management
    # =========================================================================

    async def add_papers_to_project(
        self,
        project_id: UUID,
        organization_id: UUID,
        paper_ids: list[UUID],
    ) -> int:
        """Add papers to a research group (skip duplicates, tenant-isolated).

        Validates that all papers belong to the same organization before adding.

        Returns:
            Number of papers actually added.
        """
        if not paper_ids:
            return 0

        # Validate papers belong to the same organization
        valid_result = await self.db.execute(
            select(Paper.id).where(
                Paper.id.in_(paper_ids),
                Paper.organization_id == organization_id,
            )
        )
        valid_ids = {row[0] for row in valid_result.all()}

        # Find existing associations
        existing_result = await self.db.execute(
            select(ProjectPaper.paper_id).where(
                ProjectPaper.project_id == project_id,
                ProjectPaper.paper_id.in_(list(valid_ids)),
            )
        )
        existing_ids = {row[0] for row in existing_result.all()}

        added = 0
        for paper_id in valid_ids:
            if paper_id not in existing_ids:
                self.db.add(
                    ProjectPaper(
                        project_id=project_id,
                        paper_id=paper_id,
                    )
                )
                added += 1

        if added > 0:
            await self.db.flush()

        return added

    async def list_project_papers(
        self,
        project_id: UUID,
        organization_id: UUID,
    ) -> list[ClusterPaperSummary]:
        """List all papers in a research group (flat list)."""
        project = await self.get_project(project_id, organization_id)
        if not project:
            raise NotFoundError("Project", str(project_id))

        result = await self.db.execute(
            select(Paper)
            .join(ProjectPaper, ProjectPaper.paper_id == Paper.id)
            .where(ProjectPaper.project_id == project_id)
            .order_by(Paper.citations_count.desc().nullslast())
        )
        papers = list(result.scalars().all())

        authors_map = await self._batch_get_authors_display([p.id for p in papers])

        return [self._paper_to_summary(p, authors_map=authors_map) for p in papers]

    # =========================================================================
    # Cluster Management
    # =========================================================================

    async def save_clusters(
        self,
        project_id: UUID,
        organization_id: UUID,
        cluster_data: list[dict],
    ) -> int:
        """Save cluster results, replacing any existing clusters.

        Args:
            project_id: Research group ID.
            organization_id: Tenant org.
            cluster_data: List of dicts with keys:
                label, keywords, paper_ids, centroid, similarities

        Returns:
            Number of clusters created.
        """
        # Delete existing clusters for this project
        await self.db.execute(delete(ProjectCluster).where(ProjectCluster.project_id == project_id))
        await self.db.flush()

        from paper_scraper.core.sync import SyncService

        sync = SyncService()
        created = 0
        for cdata in cluster_data:
            cluster = ProjectCluster(
                project_id=project_id,
                organization_id=organization_id,
                label=cdata["label"],
                description=cdata.get("description"),
                keywords=cdata.get("keywords", []),
                paper_count=len(cdata.get("paper_ids", [])),
            )
            self.db.add(cluster)
            # Flush to generate cluster.id for paper associations
            await self.db.flush()

            # Sync centroid to Qdrant
            centroid = cdata.get("centroid")
            if centroid:
                await sync.sync_cluster(
                    cluster_id=cluster.id,
                    organization_id=organization_id,
                    project_id=project_id,
                    centroid=centroid,
                )

            paper_ids = cdata.get("paper_ids", [])
            similarities = cdata.get("similarities", {})
            for pid in paper_ids:
                self.db.add(
                    ProjectClusterPaper(
                        cluster_id=cluster.id,
                        paper_id=pid,
                        similarity_score=similarities.get(pid),
                    )
                )

            created += 1

        if created > 0:
            await self.db.flush()
        return created

    async def list_clusters(
        self,
        project_id: UUID,
        organization_id: UUID,
    ) -> list[ClusterResponse]:
        """List all clusters for a research group with top papers.

        Uses batch queries to avoid N+1: fetches all clusters, then all
        top papers across all clusters in a single query.
        """
        project = await self.get_project(project_id, organization_id)
        if not project:
            raise NotFoundError("Project", str(project_id))

        result = await self.db.execute(
            select(ProjectCluster)
            .where(ProjectCluster.project_id == project_id)
            .order_by(ProjectCluster.paper_count.desc())
        )
        clusters = list(result.scalars().all())

        if not clusters:
            return []

        # Batch-fetch top papers for ALL clusters in one query
        cluster_ids = [c.id for c in clusters]
        papers_result = await self.db.execute(
            select(
                ProjectClusterPaper.cluster_id,
                Paper,
                ProjectClusterPaper.similarity_score,
            )
            .join(Paper, Paper.id == ProjectClusterPaper.paper_id)
            .where(ProjectClusterPaper.cluster_id.in_(cluster_ids))
            .order_by(
                ProjectClusterPaper.cluster_id,
                Paper.citations_count.desc().nullslast(),
            )
        )
        all_rows = papers_result.all()

        # Group by cluster, keep top 3 per cluster
        papers_by_cluster: dict[UUID, list[tuple]] = defaultdict(list)
        for cluster_id, paper, sim in all_rows:
            if len(papers_by_cluster[cluster_id]) < 3:
                papers_by_cluster[cluster_id].append((paper, sim))

        # Batch-fetch author names for all top papers
        all_paper_ids = [p.id for papers in papers_by_cluster.values() for p, _ in papers]
        authors_map = await self._batch_get_authors_display(all_paper_ids)

        responses = []
        for cluster in clusters:
            top = papers_by_cluster.get(cluster.id, [])
            top_papers = [
                self._paper_to_summary(paper, similarity_score=sim, authors_map=authors_map)
                for paper, sim in top
            ]
            responses.append(
                ClusterResponse(
                    id=cluster.id,
                    label=cluster.label,
                    description=cluster.description,
                    keywords=cluster.keywords or [],
                    paper_count=cluster.paper_count,
                    top_papers=top_papers,
                )
            )

        return responses

    async def get_cluster_detail(
        self,
        project_id: UUID,
        cluster_id: UUID,
        organization_id: UUID,
    ) -> ClusterDetailResponse:
        """Get full cluster detail with all papers."""
        project = await self.get_project(project_id, organization_id)
        if not project:
            raise NotFoundError("Project", str(project_id))

        result = await self.db.execute(
            select(ProjectCluster).where(
                ProjectCluster.id == cluster_id,
                ProjectCluster.project_id == project_id,
            )
        )
        cluster = result.scalar_one_or_none()
        if not cluster:
            raise NotFoundError("Cluster", str(cluster_id))

        papers = await self._get_cluster_top_papers(cluster.id, limit=500)

        return ClusterDetailResponse(
            id=cluster.id,
            label=cluster.label,
            description=cluster.description,
            keywords=cluster.keywords or [],
            paper_count=cluster.paper_count,
            papers=papers,
        )

    async def update_cluster_label(
        self,
        project_id: UUID,
        cluster_id: UUID,
        organization_id: UUID,
        label: str,
    ) -> ProjectCluster:
        """Update a cluster's label."""
        project = await self.get_project(project_id, organization_id)
        if not project:
            raise NotFoundError("Project", str(project_id))

        result = await self.db.execute(
            select(ProjectCluster).where(
                ProjectCluster.id == cluster_id,
                ProjectCluster.project_id == project_id,
            )
        )
        cluster = result.scalar_one_or_none()
        if not cluster:
            raise NotFoundError("Cluster", str(cluster_id))

        cluster.label = label
        await self.db.flush()
        await self.db.refresh(cluster)
        return cluster

    # =========================================================================
    # Private Helpers
    # =========================================================================

    async def _get_cluster_top_papers(
        self,
        cluster_id: UUID,
        limit: int = 3,
    ) -> list[ClusterPaperSummary]:
        """Get top papers in a cluster, ordered by citations."""
        result = await self.db.execute(
            select(Paper, ProjectClusterPaper.similarity_score)
            .join(
                ProjectClusterPaper,
                ProjectClusterPaper.paper_id == Paper.id,
            )
            .where(ProjectClusterPaper.cluster_id == cluster_id)
            .order_by(Paper.citations_count.desc().nullslast())
            .limit(limit)
        )
        rows = result.all()

        paper_ids = [paper.id for paper, _ in rows]
        authors_map = await self._batch_get_authors_display(paper_ids)

        return [
            self._paper_to_summary(paper, similarity_score=sim, authors_map=authors_map)
            for paper, sim in rows
        ]

    async def _batch_get_authors_display(
        self,
        paper_ids: list[UUID],
    ) -> dict[UUID, str]:
        """Batch-fetch formatted author names for a list of papers.

        Returns:
            Dict mapping paper_id → "Smith J, et al." style display string.
        """
        if not paper_ids:
            return {}

        result = await self.db.execute(
            select(PaperAuthor.paper_id, Author.name)
            .join(Author, Author.id == PaperAuthor.author_id)
            .where(PaperAuthor.paper_id.in_(paper_ids))
            .order_by(PaperAuthor.paper_id, PaperAuthor.position)
        )

        names_by_paper: dict[UUID, list[str]] = defaultdict(list)
        for paper_id, name in result.all():
            names_by_paper[paper_id].append(name)

        return {
            paper_id: f"{names[0]}, et al." if len(names) > 2 else ", ".join(names)
            for paper_id, names in names_by_paper.items()
        }

    def _paper_to_summary(
        self,
        paper: Paper,
        similarity_score: float | None = None,
        authors_map: dict[UUID, str] | None = None,
    ) -> ClusterPaperSummary:
        """Convert a Paper model to a ClusterPaperSummary."""
        return ClusterPaperSummary(
            id=paper.id,
            title=paper.title or "Untitled",
            authors_display=(authors_map or {}).get(paper.id, ""),
            publication_date=paper.publication_date.strftime("%Y-%m-%d")
            if paper.publication_date
            else None,
            citations_count=paper.citations_count,
            similarity_score=similarity_score,
        )
