"""API v1 router aggregating all module routers."""

from fastapi import APIRouter

from paper_scraper.modules.auth.router import router as auth_router

api_router = APIRouter()

# Include module routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# Future routers will be added here:
# api_router.include_router(papers_router, prefix="/papers", tags=["Papers"])
# api_router.include_router(projects_router, prefix="/projects", tags=["Projects"])
# api_router.include_router(search_router, prefix="/search", tags=["Search"])
