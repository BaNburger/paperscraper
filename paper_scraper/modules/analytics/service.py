"""Analytics service for team and paper metrics."""

from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.analytics.schemas import (
    DashboardSummaryResponse,
    PaperAnalyticsResponse,
    PaperImportTrends,
    ScoreDistributionBucket,
    ScoringStats,
    SourceDistribution,
    TeamOverviewResponse,
    TimeSeriesDataPoint,
    TopPaperResponse,
    UserActivityStats,
)
from paper_scraper.modules.auth.models import User
from paper_scraper.modules.papers.models import Paper
from paper_scraper.modules.papers.notes import PaperNote
from paper_scraper.modules.projects.models import Project
from paper_scraper.modules.scoring.models import PaperScore

# Standard time periods for analytics
DAYS_IN_WEEK = 7
DAYS_IN_MONTH = 30


class AnalyticsService:
    """Service for computing analytics and metrics."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize analytics service."""
        self.db = db

    async def _count_records(self, query) -> int:
        """Execute a count query and return the result."""
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_team_overview(self, organization_id: UUID) -> TeamOverviewResponse:
        """Get team overview statistics."""
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=DAYS_IN_WEEK)
        month_ago = now - timedelta(days=DAYS_IN_MONTH)

        # Count totals using helper method
        total_users = await self._count_records(
            select(func.count(User.id)).where(User.organization_id == organization_id)
        )
        total_papers = await self._count_records(
            select(func.count(Paper.id)).where(Paper.organization_id == organization_id)
        )
        total_scores = await self._count_records(
            select(func.count(PaperScore.id)).where(
                PaperScore.organization_id == organization_id
            )
        )
        total_projects = await self._count_records(
            select(func.count(Project.id)).where(
                Project.organization_id == organization_id
            )
        )

        # Active users based on note activity (Paper model lacks created_by_id)
        # TODO: Add created_by_id to Paper model for accurate tracking
        active_users_7_days = await self._count_records(
            select(func.count(func.distinct(PaperNote.user_id))).where(
                PaperNote.organization_id == organization_id,
                PaperNote.created_at >= week_ago,
            )
        )
        active_users_30_days = await self._count_records(
            select(func.count(func.distinct(PaperNote.user_id))).where(
                PaperNote.organization_id == organization_id,
                PaperNote.created_at >= month_ago,
            )
        )

        # User activity stats - fetch users and notes count in optimized queries
        users_result = await self.db.execute(
            select(User).where(User.organization_id == organization_id)
        )
        users = users_result.scalars().all()

        # Batch query for notes count per user (with tenant isolation)
        user_ids = [user.id for user in users]
        notes_by_user: dict[UUID, int] = {}
        if user_ids:
            notes_result = await self.db.execute(
                select(PaperNote.user_id, func.count(PaperNote.id).label("count"))
                .where(
                    PaperNote.user_id.in_(user_ids),
                    PaperNote.organization_id == organization_id,  # Tenant isolation
                )
                .group_by(PaperNote.user_id)
            )
            notes_by_user = {row.user_id: row.count for row in notes_result.all()}

        # Note: Paper model lacks created_by_id, so we can't track per-user paper imports.
        # Show 0 for papers_imported/papers_scored until model supports user tracking.
        # TODO: Add created_by_id to Paper model and update this query
        user_activity: list[UserActivityStats] = []
        for user in users:
            user_activity.append(
                UserActivityStats(
                    user_id=user.id,
                    email=user.email,
                    full_name=user.full_name,
                    papers_imported=0,  # Requires Paper.created_by_id field
                    papers_scored=0,  # Requires PaperScore.created_by_id field
                    notes_created=notes_by_user.get(user.id, 0),
                    last_active=user.updated_at,
                )
            )

        return TeamOverviewResponse(
            total_users=total_users,
            active_users_last_7_days=active_users_7_days,
            active_users_last_30_days=active_users_30_days,
            total_papers=total_papers,
            total_scores=total_scores,
            total_projects=total_projects,
            user_activity=user_activity,
        )

    async def get_paper_analytics(
        self, organization_id: UUID, days: int = 90
    ) -> PaperAnalyticsResponse:
        """Get paper analytics."""
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days)

        # Import trends - daily
        daily_result = await self.db.execute(
            select(
                func.date(Paper.created_at).label("date"),
                func.count(Paper.id).label("count"),
            )
            .where(
                Paper.organization_id == organization_id,
                Paper.created_at >= start_date,
            )
            .group_by(func.date(Paper.created_at))
            .order_by(func.date(Paper.created_at))
        )
        daily_data = [
            TimeSeriesDataPoint(date=row.date, count=row.count)
            for row in daily_result.all()
        ]

        # Weekly aggregation
        weekly_data = self._aggregate_to_weekly(daily_data)

        # Monthly aggregation
        monthly_data = self._aggregate_to_monthly(daily_data)

        # Source distribution
        source_result = await self.db.execute(
            select(Paper.source, func.count(Paper.id).label("count"))
            .where(Paper.organization_id == organization_id)
            .group_by(Paper.source)
        )
        source_rows = source_result.all()
        total_by_source = sum(row.count for row in source_rows)
        source_distribution = [
            SourceDistribution(
                source=row.source.value,
                count=row.count,
                percentage=round(row.count / total_by_source * 100, 1)
                if total_by_source > 0
                else 0,
            )
            for row in source_rows
        ]

        # Scoring statistics
        scoring_stats = await self._get_scoring_stats(organization_id)

        # Top papers by score
        top_papers_result = await self.db.execute(
            select(Paper, PaperScore.overall_score)
            .outerjoin(PaperScore, Paper.id == PaperScore.paper_id)
            .where(Paper.organization_id == organization_id)
            .order_by(PaperScore.overall_score.desc().nulls_last())
            .limit(10)
        )
        top_papers = [
            TopPaperResponse(
                id=row.Paper.id,
                title=row.Paper.title,
                doi=row.Paper.doi,
                source=row.Paper.source.value,
                overall_score=row.overall_score,
                created_at=row.Paper.created_at,
            )
            for row in top_papers_result.all()
        ]

        # Embedding coverage
        embedding_result = await self.db.execute(
            select(
                func.count(Paper.id).label("total"),
                func.count(Paper.embedding).label("with_embedding"),
            ).where(Paper.organization_id == organization_id)
        )
        embedding_row = embedding_result.one()
        total = embedding_row.total or 0
        with_embedding = embedding_row.with_embedding or 0
        without_embedding = total - with_embedding
        coverage = round(with_embedding / total * 100, 1) if total > 0 else 0

        return PaperAnalyticsResponse(
            import_trends=PaperImportTrends(
                daily=daily_data,
                weekly=weekly_data,
                monthly=monthly_data,
                by_source=source_distribution,
            ),
            scoring_stats=scoring_stats,
            top_papers=top_papers,
            papers_with_embeddings=with_embedding,
            papers_without_embeddings=without_embedding,
            embedding_coverage_percent=coverage,
        )

    async def _get_scoring_stats(self, organization_id: UUID) -> ScoringStats:
        """Get scoring statistics."""
        scored_papers = await self._count_records(
            select(func.count(func.distinct(PaperScore.paper_id))).where(
                PaperScore.organization_id == organization_id
            )
        )
        total_papers = await self._count_records(
            select(func.count(Paper.id)).where(Paper.organization_id == organization_id)
        )
        unscored_papers = total_papers - scored_papers

        # Average scores with labeled columns for clarity
        avg_result = await self.db.execute(
            select(
                func.avg(PaperScore.overall_score).label("overall"),
                func.avg(PaperScore.novelty).label("novelty"),
                func.avg(PaperScore.ip_potential).label("ip_potential"),
                func.avg(PaperScore.marketability).label("marketability"),
                func.avg(PaperScore.feasibility).label("feasibility"),
                func.avg(PaperScore.commercialization).label("commercialization"),
            ).where(PaperScore.organization_id == organization_id)
        )
        averages = avg_result.one()

        # Score distribution by bucket
        score_distribution = await self._get_score_distribution(organization_id)

        return ScoringStats(
            total_scored=scored_papers,
            total_unscored=unscored_papers,
            average_overall_score=self._round_score(averages.overall),
            average_novelty=self._round_score(averages.novelty),
            average_ip_potential=self._round_score(averages.ip_potential),
            average_marketability=self._round_score(averages.marketability),
            average_feasibility=self._round_score(averages.feasibility),
            average_commercialization=self._round_score(averages.commercialization),
            score_distribution=score_distribution,
        )

    async def _get_score_distribution(
        self, organization_id: UUID
    ) -> list[ScoreDistributionBucket]:
        """Get score distribution buckets for an organization."""
        bucket_ranges = {
            "0-2": (0.0, 2.0),
            "2-4": (2.0, 4.0),
            "4-6": (4.0, 6.0),
            "6-8": (6.0, 8.0),
            "8-10": (8.0, 10.0),
        }

        distribution_result = await self.db.execute(
            select(
                case(
                    (PaperScore.overall_score < 2, "0-2"),
                    (PaperScore.overall_score < 4, "2-4"),
                    (PaperScore.overall_score < 6, "4-6"),
                    (PaperScore.overall_score < 8, "6-8"),
                    else_="8-10",
                ).label("bucket"),
                func.count(PaperScore.id).label("count"),
            )
            .where(PaperScore.organization_id == organization_id)
            .group_by("bucket")
        )

        return [
            ScoreDistributionBucket(
                range_start=bucket_ranges[row.bucket][0],
                range_end=bucket_ranges[row.bucket][1],
                count=row.count,
            )
            for row in distribution_result.all()
        ]

    @staticmethod
    def _round_score(value: float | None) -> float | None:
        """Round a score to 2 decimal places, or return None if value is None."""
        return round(value, 2) if value is not None else None

    async def get_dashboard_summary(
        self, organization_id: UUID
    ) -> DashboardSummaryResponse:
        """Get dashboard summary with key metrics."""
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=DAYS_IN_WEEK)
        month_ago = now - timedelta(days=DAYS_IN_MONTH)

        # Paper counts
        total_papers = await self._count_records(
            select(func.count(Paper.id)).where(Paper.organization_id == organization_id)
        )
        papers_this_week = await self._count_records(
            select(func.count(Paper.id)).where(
                Paper.organization_id == organization_id,
                Paper.created_at >= week_ago,
            )
        )
        papers_this_month = await self._count_records(
            select(func.count(Paper.id)).where(
                Paper.organization_id == organization_id,
                Paper.created_at >= month_ago,
            )
        )

        # Scored papers and average score
        scored_result = await self.db.execute(
            select(
                func.count(func.distinct(PaperScore.paper_id)).label("count"),
                func.avg(PaperScore.overall_score).label("avg_score"),
            ).where(PaperScore.organization_id == organization_id)
        )
        scored_row = scored_result.one()
        scored_papers = scored_row.count or 0
        average_score = self._round_score(scored_row.avg_score)

        # Projects (all are considered active as no is_active field exists)
        total_projects = await self._count_records(
            select(func.count(Project.id)).where(
                Project.organization_id == organization_id
            )
        )

        # Users (all are considered active for now)
        total_users = await self._count_records(
            select(func.count(User.id)).where(User.organization_id == organization_id)
        )

        # Trends (last 30 days)
        import_trend = await self._get_daily_trend(
            Paper, organization_id, month_ago
        )
        scoring_trend = await self._get_daily_trend(
            PaperScore, organization_id, month_ago
        )

        return DashboardSummaryResponse(
            total_papers=total_papers,
            papers_this_week=papers_this_week,
            papers_this_month=papers_this_month,
            scored_papers=scored_papers,
            average_score=average_score,
            total_projects=total_projects,
            active_projects=total_projects,
            total_users=total_users,
            active_users=total_users,
            import_trend=import_trend,
            scoring_trend=scoring_trend,
        )

    async def _get_daily_trend(
        self,
        model: type[Paper] | type[PaperScore],
        organization_id: UUID,
        since: datetime,
    ) -> list[TimeSeriesDataPoint]:
        """Get daily count trend for a model since a given date."""
        result = await self.db.execute(
            select(
                func.date(model.created_at).label("date"),
                func.count(model.id).label("count"),
            )
            .where(
                model.organization_id == organization_id,
                model.created_at >= since,
            )
            .group_by(func.date(model.created_at))
            .order_by(func.date(model.created_at))
        )
        return [
            TimeSeriesDataPoint(date=row.date, count=row.count)
            for row in result.all()
        ]

    def _aggregate_to_weekly(
        self, daily_data: list[TimeSeriesDataPoint]
    ) -> list[TimeSeriesDataPoint]:
        """Aggregate daily data to weekly."""
        if not daily_data:
            return []

        weekly: dict[date, int] = {}
        for point in daily_data:
            # Get Monday of the week
            week_start = point.date - timedelta(days=point.date.weekday())
            weekly[week_start] = weekly.get(week_start, 0) + point.count

        return [
            TimeSeriesDataPoint(date=d, count=c)
            for d, c in sorted(weekly.items())
        ]

    def _aggregate_to_monthly(
        self, daily_data: list[TimeSeriesDataPoint]
    ) -> list[TimeSeriesDataPoint]:
        """Aggregate daily data to monthly."""
        if not daily_data:
            return []

        monthly: dict[date, int] = {}
        for point in daily_data:
            # Get first day of month
            month_start = point.date.replace(day=1)
            monthly[month_start] = monthly.get(month_start, 0) + point.count

        return [
            TimeSeriesDataPoint(date=d, count=c)
            for d, c in sorted(monthly.items())
        ]
