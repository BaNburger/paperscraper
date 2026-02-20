"""Application configuration using Pydantic Settings."""

import logging
from functools import lru_cache
from typing import Any

from arq.connections import RedisSettings
from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================================================================
    # Application
    # ==========================================================================
    APP_NAME: str = "PaperScraper"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # ==========================================================================
    # Database (PostgreSQL + pgvector)
    # NOTE: These have development defaults. In production, set DATABASE_URL
    # via environment variable with proper credentials.
    # ==========================================================================
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/paperscraper"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/paperscraper"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # ==========================================================================
    # Redis (arq job queue + caching)
    # ==========================================================================
    REDIS_URL: str = "redis://localhost:6379/0"

    # ==========================================================================
    # Qdrant (Vector search engine)
    # ==========================================================================
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION_PREFIX: str = ""  # Prefix for collection names (e.g., "test_")

    # ==========================================================================
    # Typesense (Full-text search engine)
    # ==========================================================================
    TYPESENSE_URL: str = "http://localhost:8108"
    TYPESENSE_API_KEY: str = "paperscraper_dev_key"
    TYPESENSE_COLLECTION_PREFIX: str = ""  # Prefix for collection names (e.g., "test_")

    # ==========================================================================
    # JWT Authentication
    # IMPORTANT: JWT_SECRET_KEY MUST be set in production!
    # Generate with: openssl rand -hex 32
    # ==========================================================================
    JWT_SECRET_KEY: SecretStr = SecretStr("")  # Required - no default
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Cookie-based browser auth
    AUTH_ACCESS_COOKIE_NAME: str = "ps_access_token"
    AUTH_REFRESH_COOKIE_NAME: str = "ps_refresh_token"
    AUTH_CSRF_COOKIE_NAME: str = "ps_csrf_token"
    AUTH_COOKIE_DOMAIN: str | None = None
    AUTH_COOKIE_PATH: str = "/"
    AUTH_COOKIE_SAMESITE: str = "lax"  # lax, strict, none
    AUTH_COOKIE_SECURE: bool = False
    CSRF_HEADER_NAME: str = "X-CSRF-Token"

    # ==========================================================================
    # Object Storage (MinIO / S3-compatible)
    # NOTE: S3_ACCESS_KEY and S3_SECRET_KEY MUST be set via environment
    # ==========================================================================
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = ""  # Required - no default
    S3_SECRET_KEY: SecretStr = SecretStr("")  # Required - no default
    S3_BUCKET_NAME: str = "paperscraper"
    S3_REGION: str = "us-east-1"

    # Model/API key encryption at rest (Fernet URL-safe base64 32-byte key)
    MODEL_KEY_ENCRYPTION_KEY: SecretStr | None = None

    # ==========================================================================
    # LLM Configuration (Provider-agnostic)
    # ==========================================================================
    LLM_PROVIDER: str = "openai"  # openai, anthropic, ollama, azure
    LLM_MODEL: str = "gpt-5-mini"  # Default model (can be overridden per-org)
    LLM_EMBEDDING_MODEL: str = "text-embedding-3-small"  # For vector embeddings
    LLM_TEMPERATURE: float = 0.3  # Default temperature for scoring
    LLM_MAX_TOKENS: int = 4096  # Max tokens for responses

    # OpenAI
    OPENAI_API_KEY: SecretStr = SecretStr("")
    OPENAI_ORG_ID: str | None = None

    # Anthropic
    ANTHROPIC_API_KEY: SecretStr | None = None

    # Azure OpenAI
    AZURE_OPENAI_API_KEY: SecretStr | None = None
    AZURE_OPENAI_ENDPOINT: str | None = None
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    AZURE_OPENAI_DEPLOYMENT: str | None = None

    # Google Gemini
    GOOGLE_API_KEY: SecretStr | None = None

    # Ollama (local/self-hosted)
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # ==========================================================================
    # External APIs (Open Data Sources)
    # ==========================================================================
    # OpenAlex - Primary paper/author metadata (free, no key required)
    OPENALEX_EMAIL: str = "noreply@example.com"  # Polite pool access
    OPENALEX_BASE_URL: str = "https://api.openalex.org"

    # EPO OPS - Patent data (free tier: 4GB/week)
    EPO_OPS_KEY: str | None = None
    EPO_OPS_SECRET: SecretStr | None = None
    EPO_OPS_BASE_URL: str = "https://ops.epo.org/3.2"

    # arXiv - Preprints (free, no key required)
    ARXIV_BASE_URL: str = "http://export.arxiv.org/api"

    # PubMed/NCBI - Biomedical literature
    PUBMED_API_KEY: str | None = None
    PUBMED_BASE_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    # Crossref - DOI resolution (free, polite pool with email)
    CROSSREF_EMAIL: str = "noreply@example.com"
    CROSSREF_BASE_URL: str = "https://api.crossref.org"

    # Semantic Scholar - Citations & influence
    SEMANTIC_SCHOLAR_API_KEY: str | None = None
    SEMANTIC_SCHOLAR_BASE_URL: str = "https://api.semanticscholar.org/graph/v1"

    # GitHub API (optional token for higher rate limits: 60/hr → 5000/hr)
    GITHUB_API_TOKEN: SecretStr | None = None
    GITHUB_API_BASE_URL: str = "https://api.github.com"

    # ORCID Public API (free, no auth required)
    ORCID_API_BASE_URL: str = "https://pub.orcid.org/v3.0"

    # ==========================================================================
    # Observability
    # ==========================================================================
    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_SECRET_KEY: SecretStr | None = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"
    SENTRY_DSN: str | None = None
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # ==========================================================================
    # Rate Limiting
    # ==========================================================================
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    RATE_LIMIT_SCORING_PER_MINUTE: int = 10
    RATE_LIMIT_ENABLED: bool = True  # Set to False to disable rate limiting (for testing)

    # ==========================================================================
    # Email (Resend)
    # ==========================================================================
    RESEND_API_KEY: str | None = None
    EMAIL_FROM_ADDRESS: str = "Paper Scraper <noreply@paperscraper.app>"

    # Token expiry settings (for email verification, password reset, invitations)
    EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    TEAM_INVITATION_TOKEN_EXPIRE_DAYS: int = 7  # 7 days

    # ==========================================================================
    # Frontend
    # ==========================================================================
    FRONTEND_URL: str = "http://localhost:3000"

    # ==========================================================================
    # Feature Flags (Library V2 / Zotero)
    # ==========================================================================
    LIBRARY_V2_ENABLED: bool = False
    ZOTERO_SYNC_ENABLED: bool = False
    LIBRARY_INBOUND_SYNC_ENABLED: bool = False

    # ==========================================================================
    # CORS
    # ==========================================================================
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            # Handle JSON-like string
            if v.startswith("["):
                import json

                loaded = json.loads(v)
                if isinstance(loaded, list):
                    return [str(origin) for origin in loaded]
                raise ValueError("CORS_ORIGINS JSON value must be a list")
            # Handle comma-separated string
            return [origin.strip() for origin in v.split(",")]
        if isinstance(v, list):
            return [str(origin) for origin in v]
        return ["http://localhost:3000", "http://localhost:5173"]

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        """Validate that required secrets are set in production/staging."""
        jwt_secret = self.JWT_SECRET_KEY.get_secret_value()

        if self.APP_ENV in ("production", "staging"):
            errors = self._validate_production_config(jwt_secret)

            if self.APP_ENV == "production" and self.DEBUG:
                logger.warning("DEBUG is True in production - forcing to False for security")
                object.__setattr__(self, "DEBUG", False)

            if errors:
                raise ValueError(
                    "Production configuration validation failed:\n- " + "\n- ".join(errors)
                )

        elif self.APP_ENV == "development" and not jwt_secret:
            raise ValueError(
                "JWT_SECRET_KEY must be set even in development. "
                "Add JWT_SECRET_KEY to your .env file. "
                "Generate with: openssl rand -hex 32"
            )

        # Enforce secure cookies outside development unless explicitly configured.
        if self.APP_ENV in ("production", "staging") and not self.AUTH_COOKIE_SECURE:
            logger.warning(
                "AUTH_COOKIE_SECURE is False in %s; forcing secure cookies.",
                self.APP_ENV,
            )
            object.__setattr__(self, "AUTH_COOKIE_SECURE", True)

        # Normalize SameSite values.
        same_site = self.AUTH_COOKIE_SAMESITE.lower()
        if same_site not in ("lax", "strict", "none"):
            raise ValueError("AUTH_COOKIE_SAMESITE must be one of: lax, strict, none")
        object.__setattr__(self, "AUTH_COOKIE_SAMESITE", same_site)

        return self

    def _validate_production_config(self, jwt_secret: str) -> list[str]:
        """Validate production configuration and return list of errors."""
        import re

        errors: list[str] = []

        # JWT Secret validation
        if self._is_weak_secret(jwt_secret, re):
            errors.append(
                "JWT_SECRET_KEY must be at least 32 characters and not contain "
                "common patterns like 'dev', 'test', 'secret'. "
                "Generate with: openssl rand -hex 32"
            )
        elif jwt_secret and len(jwt_secret) < 32:
            errors.append(
                f"JWT_SECRET_KEY is too short ({len(jwt_secret)} chars). "
                "Minimum 32 characters required for adequate security."
            )

        # S3 credentials
        if not self.S3_ACCESS_KEY:
            errors.append("S3_ACCESS_KEY must be set")
        if not self.S3_SECRET_KEY.get_secret_value():
            errors.append("S3_SECRET_KEY must be set")

        # Database URL should not contain default credentials
        if "postgres:postgres@" in self.DATABASE_URL:
            errors.append(
                "DATABASE_URL appears to use default credentials. "
                "Use secure credentials in production."
            )

        # CORS origins should not include localhost in production
        if self.APP_ENV == "production":
            localhost_origins = [
                o for o in self.CORS_ORIGINS if "localhost" in o or "127.0.0.1" in o
            ]
            if localhost_origins:
                errors.append(
                    f"CORS_ORIGINS contains localhost URLs which should not "
                    f"be allowed in production: {localhost_origins}"
                )

        return errors

    @staticmethod
    def _is_weak_secret(secret: str, re_module: Any) -> bool:
        """Check if a secret matches weak patterns."""
        if not secret:
            return True

        weak_patterns = [
            r"^(dev|test|secret|password|changeme|change-me|default)",
            r"^.{0,15}$",  # Too short (less than 16 chars)
        ]
        return any(
            re_module.match(pattern, secret, re_module.IGNORECASE) for pattern in weak_patterns
        )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.APP_ENV == "development"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.APP_ENV == "staging"

    @property
    def arq_redis_settings(self) -> RedisSettings:
        """Get arq Redis settings from REDIS_URL.

        Parses the REDIS_URL and returns a RedisSettings object
        compatible with arq's create_pool function.

        Returns:
            RedisSettings object for arq connection pool.
        """
        from urllib.parse import urlparse

        parsed = urlparse(self.REDIS_URL)
        return RedisSettings(
            host=parsed.hostname or "localhost",
            port=parsed.port or 6379,
            database=int(parsed.path.lstrip("/") or 0) if parsed.path else 0,
            password=parsed.password,
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
