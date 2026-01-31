"""Analytics service for team and paper metrics."""

from datetime import date, datetime, timedelta
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


class AnalyticsService:
    """Service for computing analytics and metrics."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize analytics service."""
        self.db = db

    async def get_team_overview(self, organization_id: UUID) -> TeamOverviewResponse:
        """Get team overview statistics."""
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Total users
        total_users_result = await self.db.execute(
            select(func.count(User.id)).where(User.organization_id == organization_id)
        )
        total_users = total_users_result.scalar() or 0

        # Active users in last 7 days (based on paper imports)
        active_7_result = await self.db.execute(
            select(func.count(func.distinct(Paper.organization_id))).where(
                Paper.organization_id == organization_id,
                Paper.created_at >= week_ago,
            )
        )
        active_7 = min(active_7_result.scalar() or 0, total_users)

        # Active users in last 30 days
        active_30_result = await self.db.execute(
            select(func.count(func.distinct(Paper.organization_id))).where(
                Paper.organization_id == organization_id,
                Paper.created_at >= month_ago,
            )
        )
        active_30 = min(active_30_result.scalar() or 0, total_users)

        # Total papers
        papers_result = await self.db.execute(
            select(func.count(Paper.id)).where(Paper.organization_id == organization_id)
        )
        total_papers = papers_result.scalar() or 0

        # Total scores
        scores_result = await self.db.execute(
            select(func.count(PaperScore.id)).where(
                PaperScore.organization_id == organization_id
            )
        )
        total_scores = scores_result.scalar() or 0

        # Total projects
        projects_result = await self.db.execute(
            select(func.count(Project.id)).where(
                Project.organization_id == organization_id
            )
        )
        total_projects = projects_result.scalar() or 0

        # User activity stats
        users_result = await self.db.execute(
            select(User).where(User.organization_id == organization_id)
        )
        users = users_result.scalars().all()

        user_activity: list[UserActivityStats] = []
        for user in users:
            # Papers imported by this user (approximate - by org)
            papers_count = total_papers  # In multi-user scenario, track by user

            # Scores generated
            scores_count = total_scores  # In multi-user scenario, track by user

            # Notes created
            notes_result = await self.db.execute(
                select(func.count(PaperNote.id)).where(PaperNote.user_id == user.id)
            )
            notes_count = notes_result.scalar() or 0

            user_activity.append(
                UserActivityStats(
                    user_id=user.id,
                    email=user.email,
                    full_name=user.full_name,
                    papers_imported=papers_count,
                    papers_scored=scores_count,
                    notes_created=notes_count,
                    last_active=user.updated_at,
                )
            )

        return TeamOverviewResponse(
            total_users=total_users,
            active_users_last_7_days=active_7 if active_7 > 0 else 1,
            active_users_last_30_days=active_30 if active_30 > 0 else 1,
            total_papers=total_papers,
            total_scores=total_scores,
            total_projects=total_projects,
            user_activity=user_activity,
        )

    async def get_paper_analytics(
        self, organization_id: UUID, days: int = 90
    ) -> PaperAnalyticsResponse:
        """Get paper analytics."""
        now = datetime.utcnow()
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
        # Count scored and unscored papers
        scored_result = await self.db.execute(
            select(func.count(func.distinct(PaperScore.paper_id))).where(
                PaperScore.organization_id == organization_id
            )
        )
        scored = scored_result.scalar() or 0

        total_result = await self.db.execute(
            select(func.count(Paper.id)).where(Paper.organization_id == organization_id)
        )
        total = total_result.scalar() or 0
        unscored = total - scored

        # Average scores (latest score per paper)
        avg_result = await self.db.execute(
            select(
                func.avg(PaperScore.overall_score),
                func.avg(PaperScore.novelty),
                func.avg(PaperScore.ip_potential),
                func.avg(PaperScore.marketability),
                func.avg(PaperScore.feasibility),
                func.avg(PaperScore.commercialization),
            ).where(PaperScore.organization_id == organization_id)
        )
        avg_row = avg_result.one()

        # Score distribution
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
        distribution_rows = distribution_result.all()

        bucket_map = {"0-2": (0, 2), "2-4": (2, 4), "4-6": (4, 6), "6-8": (6, 8), "8-10": (8, 10)}
        score_distribution = [
            ScoreDistributionBucket(
                range_start=bucket_map.get(row.bucket, (0, 2))[0],
                range_end=bucket_map.get(row.bucket, (0, 2))[1],
                count=row.count,
            )
            for row in distribution_rows
        ]

        return ScoringStats(
            total_scored=scored,
            total_unscored=unscored,
            average_overall_score=round(avg_row[0], 2) if avg_row[0] else None,
            average_novelty=round(avg_row[1], 2) if avg_row[1] else None,
            average_ip_potential=round(avg_row[2], 2) if avg_row[2] else None,
            average_marketability=round(avg_row[3], 2) if avg_row[3] else None,
            average_feasibility=round(avg_row[4], 2) if avg_row[4] else None,
            average_commercialization=round(avg_row[5], 2) if avg_row[5] else None,
            score_distribution=score_distribution,
        )

    async def get_dashboard_summary(
        self, organization_id: UUID
    ) -> DashboardSummaryResponse:
        """Get dashboard summary with key metrics."""
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Paper counts
        total_papers_result = await self.db.execute(
            select(func.count(Paper.id)).where(Paper.organization_id == organization_id)
        )
        total_papers = total_papers_result.scalar() or 0

        week_papers_result = await self.db.execute(
            select(func.count(Paper.id)).where(
                Paper.organization_id == organization_id,
                Paper.created_at >= week_ago,
            )
        )
        papers_this_week = week_papers_result.scalar() or 0

        month_papers_result = await self.db.execute(
            select(func.count(Paper.id)).where(
                Paper.organization_id == organization_id,
                Paper.created_at >= month_ago,
            )
        )
        papers_this_month = month_papers_result.scalar() or 0

        # Scored papers
        scored_result = await self.db.execute(
            select(
                func.count(func.distinct(PaperScore.paper_id)),
                func.avg(PaperScore.overall_score),
            ).where(PaperScore.organization_id == organization_id)
        )
        scored_row = scored_result.one()
        scored_papers = scored_row[0] or 0
        average_score = round(scored_row[1], 2) if scored_row[1] else None

        # Projects
        projects_result = await self.db.execute(
            select(
                func.count(Project.id).filter(Project.organization_id == organization_id),
                func.count(Project.id).filter(
                    Project.organization_id == organization_id,
                    Project.is_active == True,  # noqa: E712
                ),
            )
        )
        project_row = projects_result.one()
        total_projects = project_row[0] or 0
        active_projects = project_row[1] or 0

        # Users
        users_result = await self.db.execute(
            select(func.count(User.id)).where(User.organization_id == organization_id)
        )
        total_users = users_result.scalar() or 0

        # Import trend (last 30 days)
        trend_result = await self.db.execute(
            select(
                func.date(Paper.created_at).label("date"),
                func.count(Paper.id).label("count"),
            )
            .where(
                Paper.organization_id == organization_id,
                Paper.created_at >= month_ago,
            )
            .group_by(func.date(Paper.created_at))
            .order_by(func.date(Paper.created_at))
        )
        import_trend = [
            TimeSeriesDataPoint(date=row.date, count=row.count)
            for row in trend_result.all()
        ]

        # Scoring trend (last 30 days)
        scoring_trend_result = await self.db.execute(
            select(
                func.date(PaperScore.created_at).label("date"),
                func.count(PaperScore.id).label("count"),
            )
            .where(
                PaperScore.organization_id == organization_id,
                PaperScore.created_at >= month_ago,
            )
            .group_by(func.date(PaperScore.created_at))
            .order_by(func.date(PaperScore.created_at))
        )
        scoring_trend = [
            TimeSeriesDataPoint(date=row.date, count=row.count)
            for row in scoring_trend_result.all()
        ]

        return DashboardSummaryResponse(
            total_papers=total_papers,
            papers_this_week=papers_this_week,
            papers_this_month=papers_this_month,
            scored_papers=scored_papers,
            average_score=average_score,
            total_projects=total_projects,
            active_projects=active_projects,
            total_users=total_users,
            active_users=total_users,  # All users considered active for now
            import_trend=import_trend,
            scoring_trend=scoring_trend,
        )

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
