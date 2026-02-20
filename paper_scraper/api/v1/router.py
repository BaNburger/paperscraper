"""API v1 router aggregating all module routers."""

from fastapi import APIRouter

from paper_scraper.modules.alerts.router import router as alerts_router
from paper_scraper.modules.catalog.router import router as catalog_router
from paper_scraper.modules.analytics.router import router as analytics_router
from paper_scraper.modules.audit.router import router as audit_router
from paper_scraper.modules.auth.router import router as auth_router
from paper_scraper.modules.authors.router import router as authors_router
from paper_scraper.modules.badges.router import router as badges_router
from paper_scraper.modules.compliance.router import router as compliance_router
from paper_scraper.modules.developer.router import router as developer_router
from paper_scraper.modules.discovery.router import router as discovery_router
from paper_scraper.modules.export.router import router as export_router
from paper_scraper.modules.groups.router import router as groups_router
from paper_scraper.modules.ingestion.router import router as ingestion_router
from paper_scraper.modules.integrations.router import router as integrations_router
from paper_scraper.modules.knowledge.router import router as knowledge_router
from paper_scraper.modules.library.router import router as library_router
from paper_scraper.modules.model_settings.router import router as model_settings_router
from paper_scraper.modules.notifications.router import router as notifications_router
from paper_scraper.modules.papers.router import router as papers_router
from paper_scraper.modules.projects.router import router as projects_router
from paper_scraper.modules.reports.router import router as reports_router
from paper_scraper.modules.saved_searches.router import router as saved_searches_router
from paper_scraper.modules.scoring.router import router as scoring_router
from paper_scraper.modules.search.router import router as search_router
from paper_scraper.modules.submissions.router import router as submissions_router
from paper_scraper.modules.transfer.router import router as transfer_router
from paper_scraper.modules.trends.router import router as trends_router

api_router = APIRouter()

# Include module routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(authors_router, prefix="/authors", tags=["Authors"])
api_router.include_router(papers_router, prefix="/papers", tags=["Papers"])
api_router.include_router(scoring_router, prefix="/scoring", tags=["Scoring"])
api_router.include_router(projects_router, prefix="/projects", tags=["Projects"])
api_router.include_router(search_router, prefix="/search", tags=["Search"])
api_router.include_router(saved_searches_router, prefix="/saved-searches", tags=["Saved Searches"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(audit_router, prefix="/audit", tags=["Audit"])
api_router.include_router(export_router, prefix="/export", tags=["Export"])
api_router.include_router(groups_router, prefix="/groups", tags=["Groups"])
api_router.include_router(transfer_router, prefix="/transfer", tags=["Transfer"])
api_router.include_router(submissions_router, prefix="/submissions", tags=["Submissions"])
api_router.include_router(badges_router, prefix="/badges", tags=["Badges"])
api_router.include_router(knowledge_router, prefix="/knowledge", tags=["Knowledge"])
api_router.include_router(model_settings_router, prefix="/settings", tags=["Model Settings"])
api_router.include_router(developer_router, prefix="/developer", tags=["Developer"])
api_router.include_router(reports_router, prefix="/reports", tags=["Reports"])
api_router.include_router(compliance_router, prefix="/compliance", tags=["Compliance"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(ingestion_router, prefix="/ingestion", tags=["Ingestion"])
api_router.include_router(integrations_router, prefix="/integrations", tags=["Integrations"])
api_router.include_router(library_router, prefix="/library", tags=["Library"])
api_router.include_router(trends_router, prefix="/trends", tags=["Trends"])
api_router.include_router(discovery_router, prefix="/discovery", tags=["Discovery"])
api_router.include_router(catalog_router, prefix="/catalog", tags=["Catalog"])
