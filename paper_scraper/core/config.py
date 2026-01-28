"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Any

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    # JWT Authentication
    # ==========================================================================
    JWT_SECRET_KEY: SecretStr = SecretStr("change-me-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ==========================================================================
    # Object Storage (MinIO / S3-compatible)
    # ==========================================================================
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minio"
    S3_SECRET_KEY: SecretStr = SecretStr("minio123")
    S3_BUCKET_NAME: str = "paperscraper"
    S3_REGION: str = "us-east-1"

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

    # ==========================================================================
    # Observability
    # ==========================================================================
    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_SECRET_KEY: SecretStr | None = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"
    SENTRY_DSN: str | None = None

    # ==========================================================================
    # Rate Limiting
    # ==========================================================================
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    RATE_LIMIT_SCORING_PER_MINUTE: int = 10

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
                return json.loads(v)
            # Handle comma-separated string
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.APP_ENV == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
