"""FastAPI application entry point with Sentry integration and lifecycle management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import redis.asyncio as aioredis
import sentry_sdk
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sqlalchemy.ext.asyncio import create_async_engine

from paper_scraper.api.middleware import SlowAPIMiddleware, limiter
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
from paper_scraper.core.logging import get_logger, setup_logging

# Setup structured logging
setup_logging()
logger = get_logger(__name__)

# Initialize Sentry error tracking
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% of transactions
        profiles_sample_rate=0.1,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler with proper resource management."""
    # Startup
    logger.info("Starting Paper Scraper API...")

    # Initialize database connection pool
    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
    )
    app.state.db_engine = engine
    logger.info("Database connection pool initialized")

    # Initialize Redis connection pool
    app.state.redis = aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )
    try:
        await app.state.redis.ping()
        logger.info("Redis connected")
    except Exception as e:
        logger.warning(f"Redis connection failed (rate limiting may not work): {e}")

    yield

    # Shutdown
    logger.info("Shutting down Paper Scraper API...")

    # Close Redis connection
    if hasattr(app.state, "redis") and app.state.redis:
        await app.state.redis.close()
        logger.info("Redis connection closed")

    # Dispose database engine
    if hasattr(app.state, "db_engine") and app.state.db_engine:
        await app.state.db_engine.dispose()
        logger.info("Database connection pool disposed")

    logger.info("Cleanup complete")


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

# Rate Limiting
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


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
