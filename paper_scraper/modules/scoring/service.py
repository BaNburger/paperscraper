"""Service layer for scoring module."""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.modules.papers.models import Paper
from paper_scraper.modules.scoring.dimensions.base import PaperContext
from paper_scraper.modules.scoring.embeddings import generate_paper_embedding
from paper_scraper.modules.scoring.models import PaperScore, ScoringJob
from paper_scraper.modules.scoring.orchestrator import (
    AggregatedScore,
    ScoringOrchestrator,
    ScoringWeights,
)
from paper_scraper.modules.scoring.schemas import (
    PaperScoreListResponse,
    PaperScoreSummary,
    ScoringJobListResponse,
    ScoringWeightsSchema,
)


class ScoringService:
    """Service for paper scoring operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.orchestrator = ScoringOrchestrator()

    # =========================================================================
    # Paper Scoring
    # =========================================================================

    async def score_paper(
        self,
        paper_id: UUID,
        organization_id: UUID,
        weights: ScoringWeightsSchema | None = None,
        dimensions: list[str] | None = None,
        force_rescore: bool = False,
    ) -> PaperScore:
        """
        Score a paper across all dimensions.

        Args:
            paper_id: ID of paper to score
            organization_id: Organization ID for tenant isolation
            weights: Optional custom scoring weights
            dimensions: Optional specific dimensions to score
            force_rescore: If True, rescore even if recent score exists

        Returns:
            PaperScore model with results

        Raises:
            NotFoundError: If paper not found
        """
        # Get paper
        paper = await self._get_paper(paper_id, organization_id)
        if not paper:
            raise NotFoundError("Paper", paper_id)

        # Check for existing recent score (within 24 hours)
        if not force_rescore:
            existing = await self.get_latest_score(paper_id, organization_id)
            if existing and existing.created_at > datetime.utcnow() - timedelta(hours=24):
                return existing

        # Ensure paper has embedding for similar paper lookup
        if not paper.embedding:
            await self.generate_embedding(paper_id, organization_id)
            await self.db.refresh(paper)

        # Find similar papers for context
        similar_papers = await self._find_similar_papers(paper, organization_id)

        # Create paper context
        paper_context = PaperContext.from_paper(paper)
        similar_contexts = [PaperContext.from_paper(p) for p in similar_papers]

        # Get orchestrator with custom weights if provided
        orchestrator = self.orchestrator
        if weights:
            scoring_weights = ScoringWeights(
                novelty=weights.novelty,
                ip_potential=weights.ip_potential,
                marketability=weights.marketability,
                feasibility=weights.feasibility,
                commercialization=weights.commercialization,
            )
            orchestrator = orchestrator.with_weights(scoring_weights)

        # Score the paper
        result = await orchestrator.score_paper(
            paper=paper_context,
            similar_papers=similar_contexts,
            dimensions=dimensions,
        )

        # Save score to database
        score = await self._save_score(paper, organization_id, result)
        return score

    async def get_latest_score(
        self,
        paper_id: UUID,
        organization_id: UUID,
    ) -> PaperScore | None:
        """Get the most recent score for a paper."""
        result = await self.db.execute(
            select(PaperScore)
            .where(
                PaperScore.paper_id == paper_id,
                PaperScore.organization_id == organization_id,
            )
            .order_by(PaperScore.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_paper_scores(
        self,
        paper_id: UUID,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 10,
    ) -> PaperScoreListResponse:
        """Get all scores for a paper with pagination."""
        # Verify paper exists
        paper = await self._get_paper(paper_id, organization_id)
        if not paper:
            raise NotFoundError("Paper", paper_id)

        query = select(PaperScore).where(
            PaperScore.paper_id == paper_id,
            PaperScore.organization_id == organization_id,
        )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(PaperScore.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        scores = list(result.scalars().all())

        return PaperScoreListResponse(
            items=[PaperScoreSummary.model_validate(s) for s in scores],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size if total > 0 else 0,
        )

    async def list_org_scores(
        self,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        min_score: float | None = None,
        max_score: float | None = None,
    ) -> PaperScoreListResponse:
        """List all scores for an organization with filtering."""
        # Build base query - get latest score per paper
        subquery = (
            select(
                PaperScore.paper_id,
                func.max(PaperScore.created_at).label("latest_created"),
            )
            .where(PaperScore.organization_id == organization_id)
            .group_by(PaperScore.paper_id)
            .subquery()
        )

        query = (
            select(PaperScore)
            .join(
                subquery,
                (PaperScore.paper_id == subquery.c.paper_id)
                & (PaperScore.created_at == subquery.c.latest_created),
            )
            .where(PaperScore.organization_id == organization_id)
        )

        # Apply filters
        if min_score is not None:
            query = query.where(PaperScore.overall_score >= min_score)
        if max_score is not None:
            query = query.where(PaperScore.overall_score <= max_score)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(PaperScore.overall_score.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        scores = list(result.scalars().all())

        return PaperScoreListResponse(
            items=[PaperScoreSummary.model_validate(s) for s in scores],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size if total > 0 else 0,
        )

    # =========================================================================
    # Batch Scoring
    # =========================================================================

    async def create_batch_job(
        self,
        paper_ids: list[UUID],
        organization_id: UUID,
        job_type: str = "batch",
    ) -> ScoringJob:
        """Create a batch scoring job."""
        job = ScoringJob(
            organization_id=organization_id,
            job_type=job_type,
            status="pending",
            paper_ids=[str(pid) for pid in paper_ids],
            total_papers=len(paper_ids),
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_job(
        self,
        job_id: UUID,
        organization_id: UUID,
    ) -> ScoringJob | None:
        """Get a scoring job by ID."""
        result = await self.db.execute(
            select(ScoringJob).where(
                ScoringJob.id == job_id,
                ScoringJob.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_jobs(
        self,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> ScoringJobListResponse:
        """List scoring jobs for an organization."""
        query = select(ScoringJob).where(ScoringJob.organization_id == organization_id)

        if status:
            query = query.where(ScoringJob.status == status)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(ScoringJob.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        jobs = list(result.scalars().all())

        from paper_scraper.modules.scoring.schemas import ScoringJobResponse

        return ScoringJobListResponse(
            items=[ScoringJobResponse.model_validate(j) for j in jobs],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size if total > 0 else 0,
        )

    async def update_job_status(
        self,
        job_id: UUID,
        status: str,
        completed_papers: int | None = None,
        failed_papers: int | None = None,
        error_message: str | None = None,
    ) -> None:
        """Update job status."""
        job = await self.db.get(ScoringJob, job_id)
        if not job:
            return

        job.status = status

        if status == "running" and not job.started_at:
            job.started_at = datetime.utcnow()
        if status in ("completed", "failed"):
            job.completed_at = datetime.utcnow()

        if completed_papers is not None:
            job.completed_papers = completed_papers
        if failed_papers is not None:
            job.failed_papers = failed_papers
        if error_message:
            job.error_message = error_message

        await self.db.commit()

    # =========================================================================
    # Embeddings
    # =========================================================================

    async def generate_embedding(
        self,
        paper_id: UUID,
        organization_id: UUID,
        force_regenerate: bool = False,
    ) -> bool:
        """
        Generate embedding for a paper.

        Args:
            paper_id: Paper ID
            organization_id: Organization ID
            force_regenerate: If True, regenerate even if exists

        Returns:
            True if embedding was generated
        """
        paper = await self._get_paper(paper_id, organization_id)
        if not paper:
            raise NotFoundError("Paper", paper_id)

        if paper.embedding and not force_regenerate:
            return False

        # Generate embedding
        embedding = await generate_paper_embedding(
            title=paper.title,
            abstract=paper.abstract,
            keywords=paper.keywords,
        )

        paper.embedding = embedding
        await self.db.commit()
        return True

    async def batch_generate_embeddings(
        self,
        organization_id: UUID,
        limit: int = 100,
    ) -> int:
        """
        Generate embeddings for papers without them.

        Args:
            organization_id: Organization ID
            limit: Maximum papers to process

        Returns:
            Number of embeddings generated
        """
        # Find papers without embeddings
        result = await self.db.execute(
            select(Paper)
            .where(
                Paper.organization_id == organization_id,
                Paper.embedding.is_(None),
            )
            .limit(limit)
        )
        papers = list(result.scalars().all())

        count = 0
        for paper in papers:
            try:
                embedding = await generate_paper_embedding(
                    title=paper.title,
                    abstract=paper.abstract,
                    keywords=paper.keywords,
                )
                paper.embedding = embedding
                count += 1
            except Exception:
                # Skip papers that fail
                continue

        await self.db.commit()
        return count

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

    async def _find_similar_papers(
        self,
        paper: Paper,
        organization_id: UUID,
        limit: int = 5,
    ) -> list[Paper]:
        """Find similar papers using embedding similarity."""
        if not paper.embedding:
            return []

        # Use pgvector cosine distance for similarity search
        result = await self.db.execute(
            select(Paper)
            .where(
                Paper.organization_id == organization_id,
                Paper.id != paper.id,
                Paper.embedding.is_not(None),
            )
            .order_by(Paper.embedding.cosine_distance(paper.embedding))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _save_score(
        self,
        paper: Paper,
        organization_id: UUID,
        result: AggregatedScore,
    ) -> PaperScore:
        """Save scoring result to database."""
        # Extract dimension details for storage
        dimension_details = {}
        for dim_name, dim_result in result.dimension_results.items():
            dimension_details[dim_name] = {
                "score": dim_result.score,
                "confidence": dim_result.confidence,
                "reasoning": dim_result.reasoning,
                "details": dim_result.details,
            }

        score = PaperScore(
            paper_id=paper.id,
            organization_id=organization_id,
            novelty=result.novelty,
            ip_potential=result.ip_potential,
            marketability=result.marketability,
            feasibility=result.feasibility,
            commercialization=result.commercialization,
            overall_score=result.overall_score,
            overall_confidence=result.overall_confidence,
            model_version=result.model_version,
            weights=result.weights.to_dict(),
            dimension_details=dimension_details,
            errors=result.errors,
        )
        self.db.add(score)
        await self.db.commit()
        await self.db.refresh(score)
        return score
