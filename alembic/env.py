"""Alembic migration environment configuration."""

from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from sqlalchemy.engine import Connection

from alembic import context
from paper_scraper.core.config import settings
from paper_scraper.core.database import Base

# Import all models here to ensure they're registered with Base.metadata
from paper_scraper.modules.auth.models import Organization, User  # noqa: F401
from paper_scraper.modules.papers.models import Author, Paper, PaperAuthor  # noqa: F401

# Import additional models
try:
    from paper_scraper.modules.papers.notes import PaperNote  # noqa: F401
except ImportError:
    pass

try:
    from paper_scraper.modules.scoring.models import (  # noqa: F401
        GlobalScoreCache,
        PaperScore,
        ScoringJob,
    )
except ImportError:
    pass

try:
    from paper_scraper.modules.projects.models import (  # noqa: F401
        Project,
        ProjectCluster,
        ProjectClusterPaper,
        ProjectPaper,
    )
except ImportError:
    pass

try:
    from paper_scraper.modules.authors.models import AuthorContact  # noqa: F401
except ImportError:
    pass

try:
    from paper_scraper.modules.audit.models import AuditLog  # noqa: F401
except ImportError:
    pass

try:
    from paper_scraper.modules.saved_searches.models import SavedSearch  # noqa: F401
except ImportError:
    pass

try:
    from paper_scraper.modules.alerts.models import Alert, AlertResult  # noqa: F401
except ImportError:
    pass

try:
    from paper_scraper.modules.groups.models import GroupMember, ResearcherGroup  # noqa: F401
except ImportError:
    pass

try:
    from paper_scraper.modules.transfer.models import (  # noqa: F401
        ConversationMessage,
        ConversationResource,
        MessageTemplate,
        StageChange,
        TransferConversation,
    )
except ImportError:
    pass

try:
    from paper_scraper.modules.submissions.models import (  # noqa: F401
        ResearchSubmission,
        SubmissionAttachment,
        SubmissionScore,
    )
except ImportError:
    pass

try:
    from paper_scraper.modules.model_settings.models import (  # noqa: F401
        ModelConfiguration,
        ModelUsage,
    )
except ImportError:
    pass

try:
    from paper_scraper.modules.developer.models import (  # noqa: F401
        APIKey,
        RepositorySource,
        Webhook,
    )
except ImportError:
    pass

try:
    from paper_scraper.modules.reports.models import ScheduledReport  # noqa: F401
except ImportError:
    pass

try:
    from paper_scraper.modules.compliance.models import (  # noqa: F401
        RetentionLog,
        RetentionPolicy,
    )
except ImportError:
    pass

try:
    from paper_scraper.modules.search.models import SearchActivity  # noqa: F401
except ImportError:
    pass

try:
    from paper_scraper.modules.notifications.models import Notification  # noqa: F401
except ImportError:
    pass

try:
    from paper_scraper.modules.ingestion.models import (  # noqa: F401
        IngestCheckpoint,
        IngestRun,
        SourceRecord,
    )
except ImportError:
    pass

try:
    from paper_scraper.modules.integrations.models import IntegrationConnector  # noqa: F401
except ImportError:
    pass

try:
    from paper_scraper.modules.papers.context_models import PaperContextSnapshot  # noqa: F401
except ImportError:
    pass

try:
    from paper_scraper.modules.trends.models import (  # noqa: F401
        TrendPaper,
        TrendSnapshot,
        TrendTopic,
    )
except ImportError:
    pass

try:
    from paper_scraper.modules.discovery.models import DiscoveryRun  # noqa: F401
except ImportError:
    pass

# Alembic Config object
config = context.config

# Override sqlalchemy.url with our settings
# IMPORTANT: Use sync URL for Alembic migrations (not asyncpg)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine.
    Calls to context.execute() here emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with sync engine.

    Uses the sync DATABASE_URL_SYNC instead of async to avoid
    issues with asyncpg driver in Alembic migrations.
    """
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
