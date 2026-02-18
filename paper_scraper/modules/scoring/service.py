"""Service layer for scoring module."""

import logging
import re
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.core.secrets import decrypt_secret
from paper_scraper.modules.embeddings.service import EmbeddingService
from paper_scraper.modules.model_settings.models import ModelConfiguration, ModelUsage
from paper_scraper.modules.papers.models import Paper, PaperAuthor
from paper_scraper.modules.scoring.dimension_context_builder import DimensionContextBuilder
from paper_scraper.modules.scoring.dimensions.base import PaperContext
from paper_scraper.modules.scoring.llm_client import get_llm_client
from paper_scraper.modules.scoring.models import (
    GlobalScoreCache,
    PaperScore,
    ScoringJob,
)
from paper_scraper.modules.scoring.orchestrator import (
    AggregatedScore,
    ScoringOrchestrator,
    ScoringWeights,
)
from paper_scraper.modules.scoring.schemas import (
    PaperScoreListResponse,
    PaperScoreSummary,
    ScoringJobListResponse,
    ScoringJobResponse,
    ScoringWeightsSchema,
)

logger = logging.getLogger(__name__)

GLOBAL_CACHE_TTL_DAYS = 90


class ScoringService:
    """Service for paper scoring operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_service = EmbeddingService(db)

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
        use_knowledge_context: bool = True,
        user_id: UUID | None = None,
    ) -> PaperScore:
        """
        Score a paper across all dimensions.

        Args:
            paper_id: ID of paper to score
            organization_id: Organization ID for tenant isolation
            weights: Optional custom scoring weights
            dimensions: Optional specific dimensions to score
            force_rescore: If True, rescore even if recent score exists
            use_knowledge_context: If True, inject org knowledge into prompts
            user_id: Optional user ID for personal knowledge context

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
            if existing and existing.created_at > datetime.now(UTC) - timedelta(hours=24):
                return existing

        # Check global DOI cache (cross-tenant, 90-day TTL)
        if not force_rescore and paper.doi and not dimensions:
            cached = await self._check_global_cache(paper.doi)
            if cached:
                logger.info(
                    "Global cache hit for paper %s (DOI: %s)", paper_id, paper.doi
                )
                return await self._create_score_from_cache(
                    paper, organization_id, cached, weights
                )

        # Ensure paper has embedding for similar paper lookup
        if not paper.embedding:
            await self.generate_embedding(paper_id, organization_id)
            await self.db.refresh(paper)

        # Find similar papers for context
        similar_papers = await self._find_similar_papers(paper, organization_id)

        # Create paper context
        paper_context = PaperContext.from_paper(paper)
        similar_contexts = [PaperContext.from_paper(p) for p in similar_papers]

        # Build dimension-specific context (replaces monolithic context assembler)
        knowledge_context = ""
        dimension_contexts = None
        jstor_references: list[dict] = []
        author_profiles: list[dict] = []
        if use_knowledge_context:
            builder = DimensionContextBuilder(self.db)
            dim_result = await builder.build_all(
                paper=paper,
                organization_id=organization_id,
                user_id=user_id,
                similar_papers=similar_papers,
                dimensions=dimensions,
            )
            dimension_contexts = dim_result.contexts
            jstor_references = dim_result.metadata.get("_jstor_references", [])
            author_profiles = dim_result.metadata.get("_author_profiles", [])
            if dim_result.has_knowledge_context:
                # Sentinel: org-specific knowledge was used — skip global cache write
                knowledge_context = "dimension_specific"
            if dimension_contexts:
                logger.debug(
                    "Built dimension-specific contexts for %d dimensions "
                    "(paper %s, %d JSTOR refs, %d author profiles)",
                    len(dimension_contexts),
                    paper_id,
                    len(jstor_references),
                    len(author_profiles),
                )

        # Resolve tenant-specific scoring policy (provider/model) if configured.
        llm_client = await self._resolve_llm_client(organization_id, workflow="scoring")
        orchestrator = ScoringOrchestrator(llm_client=llm_client)
        if weights:
            scoring_weights = ScoringWeights(
                novelty=weights.novelty,
                ip_potential=weights.ip_potential,
                marketability=weights.marketability,
                feasibility=weights.feasibility,
                commercialization=weights.commercialization,
                team_readiness=weights.team_readiness,
            )
            orchestrator = orchestrator.with_weights(scoring_weights)

        # Score the paper
        result = await orchestrator.score_paper(
            paper=paper_context,
            similar_papers=similar_contexts,
            dimensions=dimensions,
            dimension_contexts=dimension_contexts,
        )

        # Write to global DOI cache (before _save_score so commit is atomic).
        # Skip when org knowledge context was injected — those scores are
        # org-specific and must not pollute the cross-tenant cache.
        if paper.doi and not dimensions and not knowledge_context:
            try:
                await self._write_global_cache(paper.doi, result)
            except Exception as exc:
                logger.warning("Failed to write global score cache for DOI %s: %s", paper.doi, exc)

        # Save score to database
        score = await self._save_score(
            paper, organization_id, result, knowledge_context,
            jstor_references, author_profiles,
        )

        # Log usage if tracked
        if result.usage and result.usage.total_tokens > 0:
            await self._log_usage(organization_id, result)

        return score

    async def _get_knowledge_context(
        self,
        organization_id: UUID,
        user_id: UUID | None,
        keywords: list | None,
    ) -> str:
        """Fetch and format knowledge context for scoring prompts.

        Args:
            organization_id: Organization UUID.
            user_id: Optional user UUID for personal knowledge.
            keywords: Optional keywords to filter relevant sources.

        Returns:
            Formatted knowledge context string, or empty if none found.
        """
        try:
            from paper_scraper.modules.knowledge.service import KnowledgeService

            knowledge_service = KnowledgeService(self.db)
            sources = await knowledge_service.get_relevant_sources_for_scoring(
                organization_id=organization_id,
                user_id=user_id,
                keywords=keywords if keywords else None,
                limit=5,
            )

            if sources:
                return knowledge_service.format_knowledge_for_prompt(sources)
            return ""

        except Exception as e:
            logger.warning(f"Failed to fetch knowledge context: {e}")
            return ""

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
            job.started_at = datetime.now(UTC)
        if status in ("completed", "failed"):
            job.completed_at = datetime.now(UTC)

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
        generated = await self.embedding_service.generate_for_paper(
            paper_id=paper_id,
            organization_id=organization_id,
            force_regenerate=force_regenerate,
        )
        await self.db.commit()
        return generated

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
        summary = await self.embedding_service.backfill_for_organization(
            organization_id=organization_id,
            batch_size=min(max(limit, 1), 500),
            max_papers=limit,
        )
        await self.db.commit()
        return summary.papers_succeeded

    async def _resolve_llm_client(self, organization_id: UUID, workflow: str | None = None):
        """Resolve LLM client from workflow config, model config, or global defaults."""
        # 0) Workflow-specific model configuration
        if workflow:
            workflow_query = (
                select(ModelConfiguration)
                .where(
                    ModelConfiguration.organization_id == organization_id,
                    ModelConfiguration.workflow == workflow,
                )
                .limit(1)
            )
            wf_config = (await self.db.execute(workflow_query)).scalar_one_or_none()
            if wf_config:
                api_key = self._decrypt_model_key(wf_config.api_key_encrypted)
                try:
                    return get_llm_client(
                        provider=wf_config.provider,
                        model=wf_config.model_name,
                        api_key=api_key,
                    )
                except Exception as exc:
                    logger.warning("Failed to resolve workflow LLM client for %s: %s", workflow, exc)

        # 1) model_configurations default
        config_query = (
            select(ModelConfiguration)
            .where(ModelConfiguration.organization_id == organization_id)
            .order_by(ModelConfiguration.is_default.desc(), ModelConfiguration.created_at.desc())
            .limit(1)
        )
        config = (await self.db.execute(config_query)).scalar_one_or_none()
        if config:
            api_key = self._decrypt_model_key(config.api_key_encrypted)
            try:
                return get_llm_client(
                    provider=config.provider,
                    model=config.model_name,
                    api_key=api_key,
                )
            except Exception as exc:
                logger.warning("Failed to resolve model configuration LLM client: %s", exc)

        # 2) fallback to global settings
        return get_llm_client()

    @staticmethod
    def _decrypt_model_key(encrypted_value: str | None) -> str | None:
        """Decrypt model key in v2 encrypted format."""
        if not encrypted_value:
            return None

        try:
            if encrypted_value.startswith("enc:v1:"):
                return decrypt_secret(encrypted_value.replace("enc:v1:", "", 1))
        except Exception:
            return None
        return None

    # =========================================================================
    # Private Methods
    # =========================================================================

    async def _get_paper(
        self,
        paper_id: UUID,
        organization_id: UUID,
    ) -> Paper | None:
        """Get paper with tenant isolation and eager-loaded authors."""
        result = await self.db.execute(
            select(Paper)
            .options(
                selectinload(Paper.authors).selectinload(PaperAuthor.author)
            )
            .where(
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
        knowledge_context: str = "",
        jstor_references: list[dict] | None = None,
        author_profiles: list[dict] | None = None,
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

        # Add metadata about knowledge context usage, JSTOR refs, and author profiles
        metadata: dict = {}
        if knowledge_context:
            metadata["knowledge_context_used"] = True
            metadata["knowledge_context_length"] = len(knowledge_context)
        if jstor_references:
            metadata["jstor_references"] = jstor_references
            metadata["jstor_count"] = len(jstor_references)
        if author_profiles:
            metadata["author_profiles"] = author_profiles
            metadata["author_profiles_count"] = len(author_profiles)
        if metadata:
            dimension_details["_metadata"] = metadata

        score = PaperScore(
            paper_id=paper.id,
            organization_id=organization_id,
            novelty=result.novelty,
            ip_potential=result.ip_potential,
            marketability=result.marketability,
            feasibility=result.feasibility,
            commercialization=result.commercialization,
            team_readiness=result.team_readiness,
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

    # =========================================================================
    # Global Score Cache
    # =========================================================================

    @staticmethod
    def _normalize_doi(doi: str) -> str | None:
        """Normalize and validate a DOI string.

        Returns lowercase DOI if valid (matches 10.xxxx/... pattern),
        or None if invalid.
        """
        doi = doi.strip().lower()
        if re.match(r"^10\.\d{4,9}/\S+$", doi):
            return doi
        return None

    async def _check_global_cache(self, doi: str) -> GlobalScoreCache | None:
        """Look up a non-expired global score cache entry by DOI."""
        normalized = self._normalize_doi(doi)
        if not normalized:
            return None
        result = await self.db.execute(
            select(GlobalScoreCache).where(
                GlobalScoreCache.doi == normalized,
                GlobalScoreCache.expires_at > datetime.now(UTC),
            )
        )
        return result.scalar_one_or_none()

    async def _write_global_cache(
        self,
        doi: str,
        result: AggregatedScore,
    ) -> None:
        """Write or update the global score cache for a DOI (atomic upsert).

        Only numeric score/confidence per dimension are stored — reasoning
        and details are stripped to prevent cross-tenant data leakage.
        """
        normalized = self._normalize_doi(doi)
        if not normalized:
            return

        now = datetime.now(UTC)
        expires_at = now + timedelta(days=GLOBAL_CACHE_TTL_DAYS)

        # Only store numeric data — reasoning may contain org-specific context
        dimension_details: dict = {}
        for dim_name, dim_result in result.dimension_results.items():
            dimension_details[dim_name] = {
                "score": dim_result.score,
                "confidence": dim_result.confidence,
            }

        values = {
            "doi": normalized,
            "novelty": result.novelty,
            "ip_potential": result.ip_potential,
            "marketability": result.marketability,
            "feasibility": result.feasibility,
            "commercialization": result.commercialization,
            "team_readiness": result.team_readiness,
            "overall_score": result.overall_score,
            "overall_confidence": result.overall_confidence,
            "model_version": result.model_version,
            "dimension_details": dimension_details,
            "errors": result.errors,
            "expires_at": expires_at,
        }

        update_values = {k: v for k, v in values.items() if k != "doi"}
        update_values["created_at"] = now

        stmt = pg_insert(GlobalScoreCache).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["doi"],
            set_=update_values,
        )

        await self.db.execute(stmt)
        await self.db.flush()

    async def _create_score_from_cache(
        self,
        paper: Paper,
        organization_id: UUID,
        cache: GlobalScoreCache,
        weights: ScoringWeightsSchema | None = None,
    ) -> PaperScore:
        """Create a PaperScore from a global cache entry.

        If custom weights are provided, recalculates overall_score from
        the cached dimension scores.
        """
        overall_score = cache.overall_score

        if weights:
            dimension_scores = {
                "novelty": cache.novelty,
                "ip_potential": cache.ip_potential,
                "marketability": cache.marketability,
                "feasibility": cache.feasibility,
                "commercialization": cache.commercialization,
                "team_readiness": cache.team_readiness,
            }
            weight_values = {
                "novelty": weights.novelty,
                "ip_potential": weights.ip_potential,
                "marketability": weights.marketability,
                "feasibility": weights.feasibility,
                "commercialization": weights.commercialization,
                "team_readiness": weights.team_readiness,
            }
            overall_score = round(
                sum(dimension_scores[d] * weight_values[d] for d in dimension_scores),
                2,
            )

        dimension_details = dict(cache.dimension_details)
        dimension_details["_metadata"] = {
            "source": "global_score_cache",
            "cached_at": cache.created_at.isoformat(),
            "cache_doi": cache.doi,
        }

        default_w = 1.0 / 6
        weights_dict = (
            {
                "novelty": weights.novelty,
                "ip_potential": weights.ip_potential,
                "marketability": weights.marketability,
                "feasibility": weights.feasibility,
                "commercialization": weights.commercialization,
                "team_readiness": weights.team_readiness,
            }
            if weights
            else {k: default_w for k in [
                "novelty", "ip_potential", "marketability",
                "feasibility", "commercialization", "team_readiness",
            ]}
        )

        score = PaperScore(
            paper_id=paper.id,
            organization_id=organization_id,
            novelty=cache.novelty,
            ip_potential=cache.ip_potential,
            marketability=cache.marketability,
            feasibility=cache.feasibility,
            commercialization=cache.commercialization,
            team_readiness=cache.team_readiness,
            overall_score=overall_score,
            overall_confidence=cache.overall_confidence,
            model_version=cache.model_version,
            weights=weights_dict,
            dimension_details=dimension_details,
            errors=list(cache.errors),
        )
        self.db.add(score)
        await self.db.commit()
        await self.db.refresh(score)
        return score

    async def _log_usage(
        self,
        organization_id: UUID,
        result: AggregatedScore,
    ) -> None:
        """Log LLM usage from a scoring operation to ModelUsage table."""
        if not result.usage:
            return

        usage = ModelUsage(
            organization_id=organization_id,
            operation="scoring",
            input_tokens=result.usage.total_prompt_tokens,
            output_tokens=result.usage.total_completion_tokens,
            cost_usd=result.usage.estimated_cost_usd,
        )
        self.db.add(usage)
        await self.db.commit()
