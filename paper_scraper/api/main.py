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

from paper_scraper.api.middleware import SecurityHeadersMiddleware, SlowAPIMiddleware, limiter
from paper_scraper.api.v1.router import api_router
from paper_scraper.core.config import settings
from paper_scraper.core.database import engine as db_engine
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

    # Critical security check: Ensure JWT secret is changed in production
    if settings.is_production:
        jwt_secret = settings.JWT_SECRET_KEY.get_secret_value()
        if jwt_secret == "change-me-in-production":
            raise RuntimeError(
                "CRITICAL: JWT_SECRET_KEY must be changed in production! "
                "Set a secure random value via environment variable."
            )

    # Use the shared engine from database module (avoid duplicate initialization)
    app.state.db_engine = db_engine
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

# Security Headers
app.add_middleware(SecurityHeadersMiddleware)


# =============================================================================
# Exception Handlers
# =============================================================================


def _build_error_content(exc: PaperScraperException) -> dict:
    """Build error response content, hiding details in production."""
    content = {
        "error": exc.code,
        "message": exc.message,
    }
    if hasattr(exc, "field") and exc.field:
        content["field"] = exc.field
    if settings.DEBUG:
        content["details"] = exc.details
    return content


def _create_exception_handler(
    status_code: int,
    headers: dict[str, str] | None = None,
):
    """Create an exception handler for a given status code."""
    async def handler(request: Request, exc: PaperScraperException) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content=_build_error_content(exc),
            headers=headers,
        )
    return handler


# Register exception handlers
app.add_exception_handler(
    NotFoundError,
    _create_exception_handler(status.HTTP_404_NOT_FOUND),
)
app.add_exception_handler(
    UnauthorizedError,
    _create_exception_handler(
        status.HTTP_401_UNAUTHORIZED,
        headers={"WWW-Authenticate": "Bearer"},
    ),
)
app.add_exception_handler(
    ForbiddenError,
    _create_exception_handler(status.HTTP_403_FORBIDDEN),
)
app.add_exception_handler(
    ValidationError,
    _create_exception_handler(status.HTTP_422_UNPROCESSABLE_ENTITY),
)
app.add_exception_handler(
    DuplicateError,
    _create_exception_handler(status.HTTP_409_CONFLICT),
)
app.add_exception_handler(
    RateLimitError,
    _create_exception_handler(status.HTTP_429_TOO_MANY_REQUESTS),
)
app.add_exception_handler(
    PaperScraperException,
    _create_exception_handler(status.HTTP_500_INTERNAL_SERVER_ERROR),
)


# =============================================================================
# Routes
# =============================================================================


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Basic health check endpoint (liveness probe)."""
    return {"status": "healthy", "service": settings.APP_NAME}


@app.get("/health/live", tags=["Health"])
async def liveness_check() -> dict[str, str]:
    """Liveness probe - checks if the application is running."""
    return {"status": "alive"}


@app.get("/health/ready", tags=["Health"])
async def readiness_check(request: Request) -> JSONResponse:
    """Readiness probe - checks if the application can serve traffic."""
    checks = {
        "database": "unknown",
        "redis": "unknown",
    }
    overall_healthy = True

    # Check database
    try:
        from sqlalchemy import text
        from paper_scraper.core.database import async_session_factory

        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)[:100]}"
        overall_healthy = False

    # Check Redis
    try:
        if hasattr(request.app.state, "redis") and request.app.state.redis:
            await request.app.state.redis.ping()
            checks["redis"] = "healthy"
        else:
            checks["redis"] = "not configured"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)[:100]}"
        overall_healthy = False

    status_code = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if overall_healthy else "not ready",
            "service": settings.APP_NAME,
            "checks": checks,
        },
    )


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
