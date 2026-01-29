"""API v1 router aggregating all module routers."""

from fastapi import APIRouter

from paper_scraper.modules.auth.router import router as auth_router
from paper_scraper.modules.papers.router import router as papers_router
from paper_scraper.modules.projects.router import router as projects_router
from paper_scraper.modules.scoring.router import router as scoring_router
from paper_scraper.modules.search.router import router as search_router

api_router = APIRouter()

# Include module routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(papers_router, prefix="/papers", tags=["Papers"])
api_router.include_router(scoring_router, prefix="/scoring", tags=["Scoring"])
api_router.include_router(projects_router, prefix="/projects", tags=["Projects"])
api_router.include_router(search_router, prefix="/search", tags=["Search"])
