"""Analytics service for team and paper metrics."""

from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.analytics.schemas import (
    BenchmarkMetric,
    BenchmarkResponse,
    DashboardSummaryResponse,
    FunnelResponse,
    FunnelStage,
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
from paper_scraper.modules.auth.models import Organization, User
from paper_scraper.modules.papers.models import Paper
from paper_scraper.modules.papers.notes import PaperNote
from paper_scraper.modules.projects.models import Project
from paper_scraper.modules.scoring.models import PaperScore
from paper_scraper.modules.transfer.models import TransferConversation, TransferStage

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

        # Active users based on paper imports and note activity
        active_users_7_days = await self._count_records(
            select(func.count(func.distinct(Paper.created_by_id))).where(
                Paper.organization_id == organization_id,
                Paper.created_at >= week_ago,
                Paper.created_by_id.is_not(None),
            )
        )
        active_users_30_days = await self._count_records(
            select(func.count(func.distinct(Paper.created_by_id))).where(
                Paper.organization_id == organization_id,
                Paper.created_at >= month_ago,
                Paper.created_by_id.is_not(None),
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
        papers_by_user: dict[UUID, int] = {}
        if user_ids:
            notes_result = await self.db.execute(
                select(PaperNote.user_id, func.count(PaperNote.id).label("count"))
                .where(
                    PaperNote.user_id.in_(user_ids),
                    PaperNote.organization_id == organization_id,
                )
                .group_by(PaperNote.user_id)
            )
            notes_by_user = {row.user_id: row.count for row in notes_result.all()}

            # Papers imported per user (using created_by_id)
            papers_result = await self.db.execute(
                select(Paper.created_by_id, func.count(Paper.id).label("count"))
                .where(
                    Paper.created_by_id.in_(user_ids),
                    Paper.organization_id == organization_id,
                )
                .group_by(Paper.created_by_id)
            )
            papers_by_user = {row.created_by_id: row.count for row in papers_result.all()}

        user_activity: list[UserActivityStats] = []
        for user in users:
            user_activity.append(
                UserActivityStats(
                    user_id=user.id,
                    email=user.email,
                    full_name=user.full_name,
                    papers_imported=papers_by_user.get(user.id, 0),
                    papers_scored=0,
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

    async def get_funnel_analytics(
        self,
        organization_id: UUID,
        project_id: UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> FunnelResponse:
        """Get innovation funnel analytics.

        Tracks papers through the stages:
        Imported -> Screened -> Scored -> In Pipeline -> Contacted -> Transferred

        Args:
            organization_id: Organization to analyze.
            project_id: Optional project filter.
            start_date: Optional start date filter.
            end_date: Optional end date filter.

        Returns:
            FunnelResponse with stage counts and conversion rates.
        """
        now = datetime.now(timezone.utc)

        # Base paper query with optional date filter
        paper_filters = [Paper.organization_id == organization_id]
        if start_date:
            paper_filters.append(Paper.created_at >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            paper_filters.append(Paper.created_at <= datetime.combine(end_date, datetime.max.time()))

        # 1. Total papers imported
        total_imported = await self._count_records(
            select(func.count(Paper.id)).where(*paper_filters)
        )

        # 2. Papers with scores (screened/evaluated)
        scored_query = (
            select(func.count(func.distinct(PaperScore.paper_id)))
            .select_from(PaperScore)
            .join(Paper, Paper.id == PaperScore.paper_id)
            .where(PaperScore.organization_id == organization_id)
        )
        if start_date:
            scored_query = scored_query.where(PaperScore.created_at >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            scored_query = scored_query.where(PaperScore.created_at <= datetime.combine(end_date, datetime.max.time()))
        total_scored = await self._count_records(scored_query)

        # 3. Papers in research groups (via project_papers junction table)
        from paper_scraper.modules.projects.models import ProjectPaper

        pipeline_query = (
            select(func.count(func.distinct(ProjectPaper.paper_id)))
        )
        if project_id:
            pipeline_query = pipeline_query.where(ProjectPaper.project_id == project_id)
        else:
            pipeline_query = pipeline_query.join(
                Project, Project.id == ProjectPaper.project_id
            ).where(Project.organization_id == organization_id)
        total_in_pipeline = await self._count_records(pipeline_query)

        # 4. Contacted papers (from transfer conversations)
        total_contacted = await self._count_records(
            select(func.count(func.distinct(TransferConversation.paper_id))).where(
                TransferConversation.organization_id == organization_id,
            )
        )

        # 5. Transferred (conversations closed_won)
        transferred_query = select(func.count(TransferConversation.id)).where(
            TransferConversation.organization_id == organization_id,
            TransferConversation.stage == TransferStage.CLOSED_WON,
        )
        if start_date:
            transferred_query = transferred_query.where(
                TransferConversation.created_at >= datetime.combine(start_date, datetime.min.time())
            )
        if end_date:
            transferred_query = transferred_query.where(
                TransferConversation.created_at <= datetime.combine(end_date, datetime.max.time())
            )
        total_transferred = await self._count_records(transferred_query)

        # Build funnel stages
        stages = [
            FunnelStage(
                stage="imported",
                label="Papers Imported",
                count=total_imported,
                percentage=100.0 if total_imported > 0 else 0.0,
            ),
            FunnelStage(
                stage="scored",
                label="Scored",
                count=total_scored,
                percentage=round(total_scored / total_imported * 100, 1) if total_imported > 0 else 0.0,
            ),
            FunnelStage(
                stage="in_pipeline",
                label="In Pipeline",
                count=total_in_pipeline,
                percentage=round(total_in_pipeline / total_imported * 100, 1) if total_imported > 0 else 0.0,
            ),
            FunnelStage(
                stage="contacted",
                label="Contacted",
                count=total_contacted,
                percentage=round(total_contacted / total_imported * 100, 1) if total_imported > 0 else 0.0,
            ),
            FunnelStage(
                stage="transferred",
                label="Transferred",
                count=total_transferred,
                percentage=round(total_transferred / total_imported * 100, 1) if total_imported > 0 else 0.0,
            ),
        ]

        # Calculate conversion rates between stages
        conversion_rates = {
            "imported_to_scored": round(total_scored / total_imported * 100, 1) if total_imported > 0 else 0.0,
            "scored_to_pipeline": round(total_in_pipeline / total_scored * 100, 1) if total_scored > 0 else 0.0,
            "pipeline_to_contacted": round(total_contacted / total_in_pipeline * 100, 1) if total_in_pipeline > 0 else 0.0,
            "contacted_to_transferred": round(total_transferred / total_contacted * 100, 1) if total_contacted > 0 else 0.0,
            "overall": round(total_transferred / total_imported * 100, 1) if total_imported > 0 else 0.0,
        }

        return FunnelResponse(
            stages=stages,
            total_papers=total_imported,
            conversion_rates=conversion_rates,
            period_start=start_date,
            period_end=end_date,
            project_id=project_id,
        )

    async def get_benchmarks(self, organization_id: UUID) -> BenchmarkResponse:
        """Get benchmark comparisons against aggregated platform metrics.

        Compares the organization's metrics against anonymized averages
        from all organizations.

        Args:
            organization_id: Organization to analyze.

        Returns:
            BenchmarkResponse with comparison metrics.
        """
        now = datetime.now(timezone.utc)
        month_ago = now - timedelta(days=DAYS_IN_MONTH)

        # Count all organizations for benchmark data
        total_orgs = await self._count_records(select(func.count(Organization.id)))

        # Org metrics
        org_papers_this_month = await self._count_records(
            select(func.count(Paper.id)).where(
                Paper.organization_id == organization_id,
                Paper.created_at >= month_ago,
            )
        )
        org_total_papers = await self._count_records(
            select(func.count(Paper.id)).where(Paper.organization_id == organization_id)
        )
        org_scored_papers = await self._count_records(
            select(func.count(func.distinct(PaperScore.paper_id))).where(
                PaperScore.organization_id == organization_id
            )
        )
        org_scoring_rate = round(org_scored_papers / org_total_papers * 100, 1) if org_total_papers > 0 else 0.0

        # Org pipeline conversion (papers in transfer conversations)
        org_contacted = await self._count_records(
            select(func.count(func.distinct(TransferConversation.paper_id)))
            .where(TransferConversation.organization_id == organization_id)
        )
        org_conversion_rate = round(org_contacted / org_total_papers * 100, 1) if org_total_papers > 0 else 0.0

        # Platform-wide benchmarks (average per org)
        platform_papers_month_result = await self.db.execute(
            select(func.count(Paper.id) / func.nullif(func.count(func.distinct(Paper.organization_id)), 0))
            .where(Paper.created_at >= month_ago)
        )
        platform_papers_month = float(platform_papers_month_result.scalar() or 0)

        platform_scoring_result = await self.db.execute(
            select(
                func.count(func.distinct(PaperScore.paper_id)).label("scored"),
                func.count(func.distinct(Paper.id)).label("total"),
            )
            .select_from(Paper)
            .outerjoin(PaperScore, Paper.id == PaperScore.paper_id)
        )
        platform_row = platform_scoring_result.one()
        platform_scoring_rate = round(platform_row.scored / platform_row.total * 100, 1) if platform_row.total > 0 else 0.0

        # Platform conversion rate (papers in any transfer conversation)
        platform_contacted_result = await self.db.execute(
            select(func.count(func.distinct(TransferConversation.paper_id)))
        )
        platform_contacted = platform_contacted_result.scalar() or 0
        platform_total_papers = await self._count_records(select(func.count(Paper.id)))
        platform_conversion_rate = round(platform_contacted / platform_total_papers * 100, 1) if platform_total_papers > 0 else 0.0

        # Build metrics list
        metrics = [
            BenchmarkMetric(
                metric="papers_per_month",
                label="Papers per Month",
                org_value=float(org_papers_this_month),
                benchmark_value=round(platform_papers_month, 1),
                higher_is_better=True,
            ),
            BenchmarkMetric(
                metric="scoring_velocity",
                label="Scoring Rate",
                org_value=org_scoring_rate,
                benchmark_value=platform_scoring_rate,
                unit="%",
                higher_is_better=True,
            ),
            BenchmarkMetric(
                metric="pipeline_conversion",
                label="Pipeline Conversion",
                org_value=org_conversion_rate,
                benchmark_value=platform_conversion_rate,
                unit="%",
                higher_is_better=True,
            ),
        ]

        # Calculate org percentile (simple ranking)
        # Count organizations that have fewer papers than the current org
        paper_counts_subquery = (
            select(
                Paper.organization_id.label("org_id"),
                func.count(Paper.id).label("paper_count")
            )
            .group_by(Paper.organization_id)
            .subquery()
        )
        orgs_with_fewer_result = await self.db.execute(
            select(func.count(paper_counts_subquery.c.org_id)).where(
                paper_counts_subquery.c.paper_count < org_total_papers
            )
        )
        orgs_with_fewer_papers = orgs_with_fewer_result.scalar() or 0
        org_percentile = round(orgs_with_fewer_papers / total_orgs * 100, 1) if total_orgs > 0 else 50.0

        return BenchmarkResponse(
            metrics=metrics,
            org_percentile=org_percentile,
            benchmark_data_points=total_orgs,
        )
