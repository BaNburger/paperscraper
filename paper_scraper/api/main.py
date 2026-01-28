"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from paper_scraper.api.v1.router import api_router
from paper_scraper.core.config import settings
from paper_scraper.core.exceptions import (
    DuplicateError,
    ForbiddenError,
    NotFoundError,
    PaperScraperException,
    RateLimitError,
    UnauthorizedError,
    ValidationError,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    # TODO: Initialize database connection pool
    # TODO: Initialize Redis connection
    # TODO: Create MinIO bucket if not exists
    yield
    # Shutdown
    # TODO: Close database connections
    # TODO: Close Redis connection


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered SaaS platform for automated analysis of scientific publications",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# =============================================================================
# Middleware
# =============================================================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Exception Handlers
# =============================================================================


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Handle NotFoundError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(UnauthorizedError)
async def unauthorized_handler(request: Request, exc: UnauthorizedError) -> JSONResponse:
    """Handle UnauthorizedError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(ForbiddenError)
async def forbidden_handler(request: Request, exc: ForbiddenError) -> JSONResponse:
    """Handle ForbiddenError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle ValidationError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": exc.code,
            "message": exc.message,
            "field": exc.field,
            "details": exc.details,
        },
    )


@app.exception_handler(DuplicateError)
async def duplicate_handler(request: Request, exc: DuplicateError) -> JSONResponse:
    """Handle DuplicateError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(RateLimitError)
async def rate_limit_handler(request: Request, exc: RateLimitError) -> JSONResponse:
    """Handle RateLimitError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(PaperScraperException)
async def paper_scraper_handler(
    request: Request, exc: PaperScraperException
) -> JSONResponse:
    """Handle generic PaperScraperException."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
    )


# =============================================================================
# Routes
# =============================================================================


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint for container orchestration."""
    return {"status": "healthy", "service": settings.APP_NAME}


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Root endpoint with API info."""
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "docs": "/docs" if settings.DEBUG else "disabled",
    }


# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
