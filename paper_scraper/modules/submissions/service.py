"""Service layer for research submissions module."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from paper_scraper.modules.scoring.orchestrator import AggregatedScore

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from paper_scraper.core.exceptions import (
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from paper_scraper.modules.papers.models import Paper, PaperSource
from paper_scraper.modules.submissions.models import (
    AttachmentType,
    ResearchSubmission,
    SubmissionAttachment,
    SubmissionScore,
    SubmissionStatus,
)
from paper_scraper.modules.submissions.schemas import (
    SubmissionCreate,
    SubmissionListResponse,
    SubmissionUpdate,
)

logger = logging.getLogger(__name__)


class SubmissionService:
    """Service for research submission management."""

    def __init__(self, db: AsyncSession):
        """Initialize submission service.

        Args:
            db: Async database session.
        """
        self.db = db

    # =========================================================================
    # Researcher Endpoints
    # =========================================================================

    async def create_submission(
        self,
        data: SubmissionCreate,
        user_id: UUID,
        organization_id: UUID,
    ) -> ResearchSubmission:
        """Create a new research submission as draft.

        Args:
            data: Submission creation data.
            user_id: Submitting user's ID.
            organization_id: Organization UUID for tenant isolation.

        Returns:
            Created ResearchSubmission object.
        """
        submission = ResearchSubmission(
            organization_id=organization_id,
            submitted_by_id=user_id,
            title=data.title,
            abstract=data.abstract,
            research_field=data.research_field,
            keywords=data.keywords,
            doi=data.doi,
            publication_venue=data.publication_venue,
            commercial_potential=data.commercial_potential,
            prior_art_notes=data.prior_art_notes,
            ip_disclosure=data.ip_disclosure,
            status=SubmissionStatus.DRAFT,
        )
        self.db.add(submission)
        await self.db.flush()
        # Reload with relationships
        return await self._get_submission_with_relations(submission.id, organization_id)

    async def get_submission(
        self,
        submission_id: UUID,
        organization_id: UUID,
    ) -> ResearchSubmission:
        """Get submission by ID with tenant isolation.

        Args:
            submission_id: Submission UUID.
            organization_id: Organization UUID for tenant isolation.

        Returns:
            ResearchSubmission with relations loaded.

        Raises:
            NotFoundError: If submission not found.
        """
        return await self._get_submission_with_relations(
            submission_id, organization_id
        )

    async def list_my_submissions(
        self,
        user_id: UUID,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status_filter: SubmissionStatus | None = None,
    ) -> SubmissionListResponse:
        """List submissions created by the current user.

        Args:
            user_id: Current user's ID.
            organization_id: Organization UUID for tenant isolation.
            page: Page number (1-indexed).
            page_size: Number of items per page.
            status_filter: Optional status filter.

        Returns:
            Paginated list response.
        """
        query = select(ResearchSubmission).where(
            ResearchSubmission.organization_id == organization_id,
            ResearchSubmission.submitted_by_id == user_id,
        )

        if status_filter:
            query = query.where(ResearchSubmission.status == status_filter)

        return await self._paginate_submissions(query, page, page_size)

    async def update_submission(
        self,
        submission_id: UUID,
        data: SubmissionUpdate,
        user_id: UUID,
        organization_id: UUID,
    ) -> ResearchSubmission:
        """Update a draft submission.

        Args:
            submission_id: Submission UUID.
            data: Update data.
            user_id: Current user's ID (must be the submitter).
            organization_id: Organization UUID for tenant isolation.

        Returns:
            Updated ResearchSubmission.

        Raises:
            NotFoundError: If submission not found.
            ForbiddenError: If user is not the submitter.
            ValidationError: If submission is not in draft status.
        """
        submission = await self._get_submission(submission_id, organization_id)

        if submission.submitted_by_id != user_id:
            raise ForbiddenError("You can only edit your own submissions")

        if submission.status != SubmissionStatus.DRAFT:
            raise ValidationError("Only draft submissions can be edited")

        # Apply updates
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(submission, field, value)

        await self.db.flush()
        return await self._get_submission_with_relations(submission_id, organization_id)

    async def submit_for_review(
        self,
        submission_id: UUID,
        user_id: UUID,
        organization_id: UUID,
    ) -> ResearchSubmission:
        """Submit a draft for TTO review.

        Args:
            submission_id: Submission UUID.
            user_id: Current user's ID (must be the submitter).
            organization_id: Organization UUID for tenant isolation.

        Returns:
            Updated ResearchSubmission with submitted status.

        Raises:
            NotFoundError: If submission not found.
            ForbiddenError: If user is not the submitter.
            ValidationError: If submission is not in draft status or missing required fields.
        """
        submission = await self._get_submission(submission_id, organization_id)

        if submission.submitted_by_id != user_id:
            raise ForbiddenError("You can only submit your own submissions")

        if submission.status != SubmissionStatus.DRAFT:
            raise ValidationError("Only draft submissions can be submitted")

        # Validate required fields for submission
        if not submission.title:
            raise ValidationError("Title is required for submission")
        if not submission.abstract:
            raise ValidationError("Abstract is required for submission")

        submission.status = SubmissionStatus.SUBMITTED
        submission.submitted_at = datetime.now(timezone.utc)

        await self.db.flush()
        return await self._get_submission_with_relations(submission_id, organization_id)

    async def add_attachment(
        self,
        submission_id: UUID,
        user_id: UUID,
        organization_id: UUID,
        filename: str,
        file_path: str,
        file_size: int,
        mime_type: str,
        attachment_type: AttachmentType = AttachmentType.PDF,
    ) -> SubmissionAttachment:
        """Add an attachment to a submission.

        Args:
            submission_id: Submission UUID.
            user_id: Current user's ID (must be the submitter).
            organization_id: Organization UUID for tenant isolation.
            filename: Original filename.
            file_path: Storage path.
            file_size: File size in bytes.
            mime_type: MIME type of the file.
            attachment_type: Type of attachment.

        Returns:
            Created SubmissionAttachment.

        Raises:
            NotFoundError: If submission not found.
            ForbiddenError: If user is not the submitter.
            ValidationError: If submission is not in draft status.
        """
        submission = await self._get_submission(submission_id, organization_id)

        if submission.submitted_by_id != user_id:
            raise ForbiddenError("You can only add attachments to your own submissions")

        if submission.status not in (SubmissionStatus.DRAFT, SubmissionStatus.SUBMITTED):
            raise ValidationError("Cannot add attachments to reviewed submissions")

        attachment = SubmissionAttachment(
            submission_id=submission_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            attachment_type=attachment_type,
        )
        self.db.add(attachment)
        await self.db.flush()
        await self.db.refresh(attachment)
        return attachment

    async def get_attachment(
        self,
        submission_id: UUID,
        attachment_id: UUID,
        organization_id: UUID,
    ) -> SubmissionAttachment:
        """Get an attachment by ID with tenant isolation.

        Args:
            submission_id: Submission UUID.
            attachment_id: Attachment UUID.
            organization_id: Organization UUID for tenant isolation.

        Returns:
            SubmissionAttachment.

        Raises:
            NotFoundError: If submission or attachment not found.
        """
        # Verify submission belongs to org
        await self._get_submission(submission_id, organization_id)

        result = await self.db.execute(
            select(SubmissionAttachment).where(
                SubmissionAttachment.id == attachment_id,
                SubmissionAttachment.submission_id == submission_id,
            )
        )
        attachment = result.scalar_one_or_none()
        if not attachment:
            raise NotFoundError("Attachment", attachment_id)
        return attachment

    # =========================================================================
    # TTO Review Endpoints
    # =========================================================================

    async def list_all_submissions(
        self,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status_filter: SubmissionStatus | None = None,
    ) -> SubmissionListResponse:
        """List all submissions for the organization (TTO view).

        Args:
            organization_id: Organization UUID for tenant isolation.
            page: Page number (1-indexed).
            page_size: Number of items per page.
            status_filter: Optional status filter.

        Returns:
            Paginated list response.
        """
        query = select(ResearchSubmission).where(
            ResearchSubmission.organization_id == organization_id,
        )

        if status_filter:
            query = query.where(ResearchSubmission.status == status_filter)

        return await self._paginate_submissions(query, page, page_size)

    async def review_submission(
        self,
        submission_id: UUID,
        reviewer_id: UUID,
        organization_id: UUID,
        decision: str,
        notes: str | None = None,
    ) -> ResearchSubmission:
        """Approve or reject a submission.

        Args:
            submission_id: Submission UUID.
            reviewer_id: Reviewing user's ID.
            organization_id: Organization UUID for tenant isolation.
            decision: 'approved' or 'rejected'.
            notes: Optional review notes.

        Returns:
            Updated ResearchSubmission.

        Raises:
            NotFoundError: If submission not found.
            ValidationError: If submission cannot be reviewed.
        """
        submission = await self._get_submission(submission_id, organization_id)

        if submission.status not in (
            SubmissionStatus.SUBMITTED,
            SubmissionStatus.UNDER_REVIEW,
        ):
            raise ValidationError(
                f"Cannot review a submission in '{submission.status.value}' status"
            )

        submission.status = SubmissionStatus(decision)
        submission.reviewed_by_id = reviewer_id
        submission.review_notes = notes
        submission.review_decision = decision
        submission.reviewed_at = datetime.now(timezone.utc)

        await self.db.flush()
        return await self._get_submission_with_relations(submission_id, organization_id)

    # =========================================================================
    # AI Analysis
    # =========================================================================

    async def analyze_submission(
        self,
        submission_id: UUID,
        organization_id: UUID,
    ) -> SubmissionScore:
        """Run AI scoring analysis on a submission.

        Uses the scoring orchestrator to analyze the submission's
        commercial potential across all dimensions. Finds similar papers
        using pgvector embedding similarity for richer analysis context.

        Args:
            submission_id: Submission UUID.
            organization_id: Organization UUID for tenant isolation.

        Returns:
            Created SubmissionScore.

        Raises:
            NotFoundError: If submission not found.
            ValidationError: If submission has no abstract.
        """
        submission = await self._get_submission(submission_id, organization_id)

        if not submission.abstract:
            raise ValidationError("Submission must have an abstract for AI analysis")

        # Import lazily to avoid circular imports
        from paper_scraper.modules.scoring.dimensions.base import PaperContext
        from paper_scraper.modules.scoring.embeddings import generate_paper_embedding
        from paper_scraper.modules.scoring.orchestrator import ScoringOrchestrator

        # Find similar papers using embedding similarity
        similar_papers = await self._find_similar_papers_for_submission(
            submission=submission,
            organization_id=organization_id,
            limit=5,
        )

        # Create a paper-like context from submission
        paper_context = PaperContext(
            id=submission.id,
            title=submission.title,
            abstract=submission.abstract,
            keywords=submission.keywords,
            journal=submission.publication_venue,
            doi=submission.doi,
        )

        # Convert similar papers to contexts
        similar_contexts = [PaperContext.from_paper(p) for p in similar_papers]

        orchestrator = ScoringOrchestrator()
        result = await orchestrator.score_paper(
            paper=paper_context,
            similar_papers=similar_contexts,
        )

        # Build dimension details including similar papers info
        dimension_details = {}
        for dim_name, dim_result in result.dimension_results.items():
            dimension_details[dim_name] = {
                "score": dim_result.score,
                "confidence": dim_result.confidence,
                "reasoning": dim_result.reasoning,
                "details": dim_result.details,
            }

        # Add similar papers metadata to analysis
        similar_papers_summary = [
            {
                "id": str(p.id),
                "title": p.title[:100],
                "doi": p.doi,
            }
            for p in similar_papers
        ]

        # Save submission score
        score = SubmissionScore(
            submission_id=submission_id,
            novelty=result.novelty,
            ip_potential=result.ip_potential,
            marketability=result.marketability,
            feasibility=result.feasibility,
            commercialization=result.commercialization,
            overall_score=result.overall_score,
            overall_confidence=result.overall_confidence,
            model_version=result.model_version,
            dimension_details={
                **dimension_details,
                "_similar_papers": similar_papers_summary,
            },
            analysis_summary=self._generate_analysis_summary(result, len(similar_papers)),
        )
        self.db.add(score)
        await self.db.flush()
        await self.db.refresh(score)
        return score

    async def _find_similar_papers_for_submission(
        self,
        submission: ResearchSubmission,
        organization_id: UUID,
        limit: int = 5,
    ) -> list[Paper]:
        """Find similar papers using embedding similarity.

        Generates an embedding for the submission abstract and uses
        pgvector cosine distance to find similar papers in the library.

        Args:
            submission: The submission to analyze.
            organization_id: Organization UUID for tenant isolation.
            limit: Maximum number of similar papers to return.

        Returns:
            List of similar Paper objects.
        """
        if not submission.abstract:
            return []

        try:
            from paper_scraper.modules.scoring.embeddings import generate_paper_embedding

            # Generate embedding for submission
            embedding = await generate_paper_embedding(
                title=submission.title,
                abstract=submission.abstract,
                keywords=submission.keywords,
            )

            # Find similar papers using pgvector cosine distance
            result = await self.db.execute(
                select(Paper)
                .where(
                    Paper.organization_id == organization_id,
                    Paper.embedding.is_not(None),
                )
                .order_by(Paper.embedding.cosine_distance(embedding))
                .limit(limit)
            )
            return list(result.scalars().all())

        except Exception as e:
            logger.warning(f"Failed to find similar papers for submission: {e}")
            return []

    # =========================================================================
    # Conversion
    # =========================================================================

    async def convert_to_paper(
        self,
        submission_id: UUID,
        organization_id: UUID,
    ) -> Paper:
        """Convert an approved submission into a paper.

        Args:
            submission_id: Submission UUID.
            organization_id: Organization UUID for tenant isolation.

        Returns:
            Created Paper object.

        Raises:
            NotFoundError: If submission not found.
            ValidationError: If submission is not approved or already converted.
        """
        submission = await self._get_submission(submission_id, organization_id)

        if submission.status != SubmissionStatus.APPROVED:
            raise ValidationError(
                "Only approved submissions can be converted to papers"
            )

        if submission.converted_paper_id:
            raise ValidationError("Submission has already been converted to a paper")

        # Create paper from submission
        paper = Paper(
            organization_id=organization_id,
            doi=submission.doi,
            source=PaperSource.MANUAL,
            source_id=f"submission:{submission.id}",
            title=submission.title,
            abstract=submission.abstract,
            journal=submission.publication_venue,
            keywords=submission.keywords,
            raw_metadata={
                "source": "submission",
                "submission_id": str(submission.id),
                "research_field": submission.research_field,
                "commercial_potential": submission.commercial_potential,
            },
        )
        self.db.add(paper)
        await self.db.flush()

        # Update submission
        submission.converted_paper_id = paper.id
        submission.status = SubmissionStatus.CONVERTED

        await self.db.flush()
        return paper

    # =========================================================================
    # Private Methods
    # =========================================================================

    async def _get_submission(
        self,
        submission_id: UUID,
        organization_id: UUID,
    ) -> ResearchSubmission:
        """Get submission by ID with tenant isolation.

        Args:
            submission_id: Submission UUID.
            organization_id: Organization UUID for tenant isolation.

        Returns:
            ResearchSubmission.

        Raises:
            NotFoundError: If submission not found.
        """
        query = select(ResearchSubmission).where(
            ResearchSubmission.id == submission_id,
            ResearchSubmission.organization_id == organization_id,
        )

        result = await self.db.execute(query)
        submission = result.scalar_one_or_none()
        if not submission:
            raise NotFoundError("Submission", submission_id)
        return submission

    async def _get_submission_with_relations(
        self,
        submission_id: UUID,
        organization_id: UUID,
    ) -> ResearchSubmission:
        """Get submission with all relationships loaded.

        Args:
            submission_id: Submission UUID.
            organization_id: Organization UUID for tenant isolation.

        Returns:
            ResearchSubmission with relations.

        Raises:
            NotFoundError: If submission not found.
        """
        query = (
            select(ResearchSubmission)
            .options(
                selectinload(ResearchSubmission.submitted_by),
                selectinload(ResearchSubmission.reviewed_by),
                selectinload(ResearchSubmission.attachments),
                selectinload(ResearchSubmission.scores),
            )
            .where(
                ResearchSubmission.id == submission_id,
                ResearchSubmission.organization_id == organization_id,
            )
        )

        result = await self.db.execute(query)
        submission = result.scalar_one_or_none()
        if not submission:
            raise NotFoundError("Submission", submission_id)
        return submission

    async def _paginate_submissions(
        self,
        query: Select,
        page: int,
        page_size: int,
    ) -> SubmissionListResponse:
        """Paginate a submission query.

        Args:
            query: Base SQLAlchemy query.
            page: Page number (1-indexed).
            page_size: Items per page.

        Returns:
            Paginated list response.
        """
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate with eager loading
        query = (
            query.options(
                selectinload(ResearchSubmission.submitted_by),
                selectinload(ResearchSubmission.reviewed_by),
            )
            .order_by(ResearchSubmission.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        submissions = list(result.scalars().all())

        return SubmissionListResponse(
            items=submissions,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size if total > 0 else 0,
        )

    @staticmethod
    def _generate_analysis_summary(
        result: AggregatedScore,
        similar_papers_count: int = 0,
    ) -> str:
        """Generate a human-readable summary from scoring results.

        Args:
            result: AggregatedScore from the orchestrator.
            similar_papers_count: Number of similar papers used for context.

        Returns:
            Summary string.
        """
        summary_parts = [
            f"Overall commercial potential score: {result.overall_score:.1f}/10 "
            f"(confidence: {result.overall_confidence:.0%}).",
        ]

        # Highlight top dimensions
        dimensions = {
            "Novelty": result.novelty,
            "IP Potential": result.ip_potential,
            "Marketability": result.marketability,
            "Feasibility": result.feasibility,
            "Commercialization": result.commercialization,
        }
        top = max(dimensions, key=dimensions.get)  # type: ignore[arg-type]
        low = min(dimensions, key=dimensions.get)  # type: ignore[arg-type]

        summary_parts.append(
            f"Strongest dimension: {top} ({dimensions[top]:.1f}/10). "
            f"Area for improvement: {low} ({dimensions[low]:.1f}/10)."
        )

        if similar_papers_count > 0:
            summary_parts.append(
                f"Analysis informed by {similar_papers_count} similar papers in your library."
            )

        return " ".join(summary_parts)
