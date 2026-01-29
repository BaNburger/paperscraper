"""Service layer for projects module."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from paper_scraper.core.exceptions import DuplicateError, NotFoundError
from paper_scraper.modules.auth.models import User
from paper_scraper.modules.papers.models import Paper
from paper_scraper.modules.projects.models import (
    PaperProjectStatus,
    PaperStageHistory,
    Project,
    RejectionReason,
)
from paper_scraper.modules.projects.schemas import (
    BatchAddPapersRequest,
    KanBanBoardResponse,
    KanBanStage,
    PaperInProjectResponse,
    PaperProjectStatusResponse,
    PaperSummaryForProject,
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectStatistics,
    ProjectUpdate,
    StageHistoryEntry,
    UserSummary,
)
from paper_scraper.modules.scoring.models import PaperScore


class ProjectService:
    """Service for project management and KanBan operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Project CRUD
    # =========================================================================

    async def create_project(
        self,
        data: ProjectCreate,
        organization_id: UUID,
    ) -> Project:
        """Create a new project."""
        project = Project(
            organization_id=organization_id,
            name=data.name,
            description=data.description,
            settings=data.settings,
        )

        # Set custom stages if provided
        if data.stages:
            project.stages = [s.model_dump() for s in data.stages]

        # Set custom weights if provided
        if data.scoring_weights:
            project.scoring_weights = data.scoring_weights.model_dump()

        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def get_project(
        self,
        project_id: UUID,
        organization_id: UUID,
    ) -> Project | None:
        """Get a project by ID with tenant isolation."""
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
        """List projects with pagination."""
        query = select(Project).where(Project.organization_id == organization_id)

        if search:
            search_filter = f"%{search}%"
            query = query.where(Project.name.ilike(search_filter))

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
        """Update a project."""
        project = await self.get_project(project_id, organization_id)
        if not project:
            raise NotFoundError("Project", project_id)

        update_data = data.model_dump(exclude_unset=True)

        if "stages" in update_data and update_data["stages"]:
            update_data["stages"] = [s.model_dump() if hasattr(s, "model_dump") else s for s in update_data["stages"]]

        if "scoring_weights" in update_data and update_data["scoring_weights"]:
            if hasattr(update_data["scoring_weights"], "model_dump"):
                update_data["scoring_weights"] = update_data["scoring_weights"].model_dump()

        for key, value in update_data.items():
            if value is not None:
                setattr(project, key, value)

        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def delete_project(
        self,
        project_id: UUID,
        organization_id: UUID,
    ) -> None:
        """Delete a project."""
        project = await self.get_project(project_id, organization_id)
        if not project:
            raise NotFoundError("Project", project_id)

        await self.db.delete(project)
        await self.db.commit()

    # =========================================================================
    # Paper Management in Projects
    # =========================================================================

    async def add_paper_to_project(
        self,
        project_id: UUID,
        paper_id: UUID,
        organization_id: UUID,
        stage: str = "inbox",
        assigned_to_id: UUID | None = None,
        notes: str | None = None,
        priority: int = 3,
        tags: list[str] | None = None,
        user_id: UUID | None = None,
    ) -> PaperProjectStatus:
        """Add a paper to a project."""
        # Verify project exists
        project = await self.get_project(project_id, organization_id)
        if not project:
            raise NotFoundError("Project", project_id)

        # Verify paper exists and belongs to org
        paper = await self._get_paper(paper_id, organization_id)
        if not paper:
            raise NotFoundError("Paper", paper_id)

        # Check if paper already in project
        existing = await self._get_paper_status(paper_id, project_id)
        if existing:
            raise DuplicateError("PaperProjectStatus", "paper_id", str(paper_id))

        # Get max position for the stage
        max_pos = await self._get_max_position(project_id, stage)

        # Create status
        status = PaperProjectStatus(
            paper_id=paper_id,
            project_id=project_id,
            stage=stage,
            position=max_pos + 1,
            assigned_to_id=assigned_to_id,
            notes=notes,
            priority=priority,
            tags=tags or [],
        )
        self.db.add(status)
        await self.db.flush()

        # Record history
        history = PaperStageHistory(
            paper_project_status_id=status.id,
            changed_by_id=user_id,
            from_stage=None,
            to_stage=stage,
            comment="Added to project",
        )
        self.db.add(history)

        await self.db.commit()
        await self.db.refresh(status)
        return status

    async def batch_add_papers(
        self,
        project_id: UUID,
        organization_id: UUID,
        request: BatchAddPapersRequest,
        user_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Add multiple papers to a project."""
        project = await self.get_project(project_id, organization_id)
        if not project:
            raise NotFoundError("Project", project_id)

        added = 0
        skipped = 0
        errors: list[str] = []

        # Get max position for the stage
        max_pos = await self._get_max_position(project_id, request.stage)

        for paper_id in request.paper_ids:
            try:
                # Check paper exists
                paper = await self._get_paper(paper_id, organization_id)
                if not paper:
                    errors.append(f"Paper {paper_id} not found")
                    continue

                # Check if already in project
                existing = await self._get_paper_status(paper_id, project_id)
                if existing:
                    skipped += 1
                    continue

                max_pos += 1
                status = PaperProjectStatus(
                    paper_id=paper_id,
                    project_id=project_id,
                    stage=request.stage,
                    position=max_pos,
                    tags=request.tags,
                )
                self.db.add(status)
                await self.db.flush()

                # Record history
                history = PaperStageHistory(
                    paper_project_status_id=status.id,
                    changed_by_id=user_id,
                    from_stage=None,
                    to_stage=request.stage,
                    comment="Added via batch import",
                )
                self.db.add(history)

                added += 1
            except Exception as e:
                errors.append(f"Error adding paper {paper_id}: {str(e)}")

        await self.db.commit()

        return {
            "added": added,
            "skipped": skipped,
            "errors": errors,
        }

    async def remove_paper_from_project(
        self,
        project_id: UUID,
        paper_id: UUID,
        organization_id: UUID,
    ) -> None:
        """Remove a paper from a project."""
        # Verify project
        project = await self.get_project(project_id, organization_id)
        if not project:
            raise NotFoundError("Project", project_id)

        status = await self._get_paper_status(paper_id, project_id)
        if not status:
            raise NotFoundError("PaperProjectStatus", paper_id)

        await self.db.delete(status)
        await self.db.commit()

    async def move_paper(
        self,
        project_id: UUID,
        paper_id: UUID,
        organization_id: UUID,
        stage: str,
        position: int | None = None,
        comment: str | None = None,
        user_id: UUID | None = None,
    ) -> PaperProjectStatus:
        """Move a paper to a different stage in the pipeline."""
        # Verify project
        project = await self.get_project(project_id, organization_id)
        if not project:
            raise NotFoundError("Project", project_id)

        # Verify stage exists in project
        stage_names = [s["name"] for s in project.stages]
        if stage not in stage_names:
            raise ValueError(f"Stage '{stage}' not found in project")

        status = await self._get_paper_status(paper_id, project_id)
        if not status:
            raise NotFoundError("PaperProjectStatus", paper_id)

        old_stage = status.stage

        # Update stage
        status.stage = stage
        status.stage_entered_at = datetime.utcnow()

        # Handle position
        if position is not None:
            # Reorder papers in target stage
            await self._reorder_stage(project_id, stage, status.id, position)
            status.position = position
        else:
            # Add to end of stage
            max_pos = await self._get_max_position(project_id, stage)
            status.position = max_pos + 1

        # Clear rejection info if moving out of rejected
        if old_stage == "rejected" and stage != "rejected":
            status.rejection_reason = None
            status.rejection_notes = None

        # Record history
        history = PaperStageHistory(
            paper_project_status_id=status.id,
            changed_by_id=user_id,
            from_stage=old_stage,
            to_stage=stage,
            comment=comment,
        )
        self.db.add(history)

        await self.db.commit()
        await self.db.refresh(status)
        return status

    async def reject_paper(
        self,
        project_id: UUID,
        paper_id: UUID,
        organization_id: UUID,
        reason: RejectionReason,
        notes: str | None = None,
        comment: str | None = None,
        user_id: UUID | None = None,
    ) -> PaperProjectStatus:
        """Reject a paper in a project."""
        status = await self.move_paper(
            project_id=project_id,
            paper_id=paper_id,
            organization_id=organization_id,
            stage="rejected",
            comment=comment or f"Rejected: {reason.value}",
            user_id=user_id,
        )

        status.rejection_reason = reason
        status.rejection_notes = notes

        await self.db.commit()
        await self.db.refresh(status)
        return status

    async def update_paper_status(
        self,
        project_id: UUID,
        paper_id: UUID,
        organization_id: UUID,
        assigned_to_id: UUID | None = None,
        notes: str | None = None,
        priority: int | None = None,
        tags: list[str] | None = None,
    ) -> PaperProjectStatus:
        """Update paper status metadata (assignment, notes, etc.)."""
        # Verify project
        project = await self.get_project(project_id, organization_id)
        if not project:
            raise NotFoundError("Project", project_id)

        status = await self._get_paper_status(paper_id, project_id)
        if not status:
            raise NotFoundError("PaperProjectStatus", paper_id)

        if assigned_to_id is not None:
            status.assigned_to_id = assigned_to_id
        if notes is not None:
            status.notes = notes
        if priority is not None:
            status.priority = priority
        if tags is not None:
            status.tags = tags

        await self.db.commit()
        await self.db.refresh(status)
        return status

    # =========================================================================
    # KanBan Views
    # =========================================================================

    async def get_kanban_board(
        self,
        project_id: UUID,
        organization_id: UUID,
        include_scores: bool = True,
    ) -> KanBanBoardResponse:
        """Get complete KanBan board view for a project."""
        project = await self.get_project(project_id, organization_id)
        if not project:
            raise NotFoundError("Project", project_id)

        # Get all paper statuses with relationships
        result = await self.db.execute(
            select(PaperProjectStatus)
            .options(
                selectinload(PaperProjectStatus.paper),
                selectinload(PaperProjectStatus.assigned_to),
            )
            .where(PaperProjectStatus.project_id == project_id)
            .order_by(PaperProjectStatus.position)
        )
        statuses = list(result.scalars().all())

        # Group by stage
        papers_by_stage: dict[str, list[PaperInProjectResponse]] = {}
        for stage_config in project.stages:
            papers_by_stage[stage_config["name"]] = []

        # Get latest scores if requested
        paper_ids = [s.paper_id for s in statuses]
        latest_scores: dict[UUID, PaperScore] = {}
        if include_scores and paper_ids:
            latest_scores = await self._get_latest_scores(paper_ids, organization_id)

        # Build response
        for status in statuses:
            paper_response = PaperInProjectResponse(
                status=PaperProjectStatusResponse.model_validate(status),
                paper=PaperSummaryForProject.model_validate(status.paper),
                assigned_to=UserSummary.model_validate(status.assigned_to)
                if status.assigned_to
                else None,
                latest_score=self._score_to_dict(latest_scores.get(status.paper_id)),
            )

            if status.stage in papers_by_stage:
                papers_by_stage[status.stage].append(paper_response)

        # Build stages list
        kanban_stages = []
        for stage_config in project.stages:
            stage_name = stage_config["name"]
            papers = papers_by_stage.get(stage_name, [])
            kanban_stages.append(
                KanBanStage(
                    name=stage_name,
                    label=stage_config["label"],
                    order=stage_config["order"],
                    paper_count=len(papers),
                    papers=papers,
                )
            )

        return KanBanBoardResponse(
            project=ProjectResponse.model_validate(project),
            stages=kanban_stages,
            total_papers=len(statuses),
        )

    async def get_paper_in_project(
        self,
        project_id: UUID,
        paper_id: UUID,
        organization_id: UUID,
    ) -> PaperInProjectResponse | None:
        """Get a paper's status in a project."""
        project = await self.get_project(project_id, organization_id)
        if not project:
            raise NotFoundError("Project", project_id)

        result = await self.db.execute(
            select(PaperProjectStatus)
            .options(
                selectinload(PaperProjectStatus.paper),
                selectinload(PaperProjectStatus.assigned_to),
            )
            .where(
                PaperProjectStatus.project_id == project_id,
                PaperProjectStatus.paper_id == paper_id,
            )
        )
        status = result.scalar_one_or_none()
        if not status:
            return None

        # Get latest score
        scores = await self._get_latest_scores([paper_id], organization_id)

        return PaperInProjectResponse(
            status=PaperProjectStatusResponse.model_validate(status),
            paper=PaperSummaryForProject.model_validate(status.paper),
            assigned_to=UserSummary.model_validate(status.assigned_to)
            if status.assigned_to
            else None,
            latest_score=self._score_to_dict(scores.get(paper_id)),
        )

    async def get_paper_history(
        self,
        project_id: UUID,
        paper_id: UUID,
        organization_id: UUID,
    ) -> list[StageHistoryEntry]:
        """Get stage transition history for a paper in a project."""
        project = await self.get_project(project_id, organization_id)
        if not project:
            raise NotFoundError("Project", project_id)

        status = await self._get_paper_status(paper_id, project_id)
        if not status:
            raise NotFoundError("PaperProjectStatus", paper_id)

        result = await self.db.execute(
            select(PaperStageHistory)
            .options(selectinload(PaperStageHistory.changed_by))
            .where(PaperStageHistory.paper_project_status_id == status.id)
            .order_by(PaperStageHistory.created_at.desc())
        )
        history = list(result.scalars().all())

        return [
            StageHistoryEntry(
                id=h.id,
                from_stage=h.from_stage,
                to_stage=h.to_stage,
                comment=h.comment,
                changed_by=UserSummary.model_validate(h.changed_by)
                if h.changed_by
                else None,
                created_at=h.created_at,
            )
            for h in history
        ]

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_project_statistics(
        self,
        project_id: UUID,
        organization_id: UUID,
    ) -> ProjectStatistics:
        """Get statistics for a project."""
        project = await self.get_project(project_id, organization_id)
        if not project:
            raise NotFoundError("Project", project_id)

        # Get all statuses
        result = await self.db.execute(
            select(PaperProjectStatus).where(
                PaperProjectStatus.project_id == project_id
            )
        )
        statuses = list(result.scalars().all())

        # Count by stage
        papers_by_stage: dict[str, int] = {}
        for stage_config in project.stages:
            papers_by_stage[stage_config["name"]] = 0
        for status in statuses:
            if status.stage in papers_by_stage:
                papers_by_stage[status.stage] += 1

        # Count by priority
        papers_by_priority: dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for status in statuses:
            papers_by_priority[status.priority] = (
                papers_by_priority.get(status.priority, 0) + 1
            )

        # Count rejection reasons
        rejection_reasons: dict[str, int] = {}
        for status in statuses:
            if status.rejection_reason:
                reason = status.rejection_reason.value
                rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1

        return ProjectStatistics(
            project_id=project_id,
            total_papers=len(statuses),
            papers_by_stage=papers_by_stage,
            papers_by_priority=papers_by_priority,
            avg_time_per_stage={},  # TODO: Calculate from history
            rejection_reasons=rejection_reasons,
        )

    # =========================================================================
    # Private Methods
    # =========================================================================

    async def _get_paper(
        self,
        paper_id: UUID,
        organization_id: UUID,
    ) -> Paper | None:
        """Get paper with tenant isolation."""
        result = await self.db.execute(
            select(Paper).where(
                Paper.id == paper_id,
                Paper.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def _get_paper_status(
        self,
        paper_id: UUID,
        project_id: UUID,
    ) -> PaperProjectStatus | None:
        """Get paper status in a project."""
        result = await self.db.execute(
            select(PaperProjectStatus).where(
                PaperProjectStatus.paper_id == paper_id,
                PaperProjectStatus.project_id == project_id,
            )
        )
        return result.scalar_one_or_none()

    async def _get_max_position(
        self,
        project_id: UUID,
        stage: str,
    ) -> int:
        """Get the maximum position in a stage."""
        result = await self.db.execute(
            select(func.max(PaperProjectStatus.position)).where(
                PaperProjectStatus.project_id == project_id,
                PaperProjectStatus.stage == stage,
            )
        )
        return result.scalar() or 0

    async def _reorder_stage(
        self,
        project_id: UUID,
        stage: str,
        moving_status_id: UUID,
        target_position: int,
    ) -> None:
        """Reorder papers in a stage when inserting at a specific position."""
        # Get all statuses in the stage except the one being moved
        result = await self.db.execute(
            select(PaperProjectStatus)
            .where(
                PaperProjectStatus.project_id == project_id,
                PaperProjectStatus.stage == stage,
                PaperProjectStatus.id != moving_status_id,
            )
            .order_by(PaperProjectStatus.position)
        )
        statuses = list(result.scalars().all())

        # Reorder
        new_position = 0
        for status in statuses:
            if new_position == target_position:
                new_position += 1
            status.position = new_position
            new_position += 1

    async def _get_latest_scores(
        self,
        paper_ids: list[UUID],
        organization_id: UUID,
    ) -> dict[UUID, PaperScore]:
        """Get latest scores for a list of papers."""
        if not paper_ids:
            return {}

        # Subquery to get latest score per paper
        subquery = (
            select(
                PaperScore.paper_id,
                func.max(PaperScore.created_at).label("latest"),
            )
            .where(
                PaperScore.paper_id.in_(paper_ids),
                PaperScore.organization_id == organization_id,
            )
            .group_by(PaperScore.paper_id)
            .subquery()
        )

        result = await self.db.execute(
            select(PaperScore).join(
                subquery,
                (PaperScore.paper_id == subquery.c.paper_id)
                & (PaperScore.created_at == subquery.c.latest),
            )
        )
        scores = result.scalars().all()
        return {score.paper_id: score for score in scores}

    def _score_to_dict(self, score: PaperScore | None) -> dict[str, Any] | None:
        """Convert a PaperScore to a dict for response."""
        if not score:
            return None
        return {
            "overall_score": score.overall_score,
            "novelty": score.novelty,
            "ip_potential": score.ip_potential,
            "marketability": score.marketability,
            "feasibility": score.feasibility,
            "commercialization": score.commercialization,
            "model_version": score.model_version,
            "created_at": score.created_at.isoformat(),
        }
