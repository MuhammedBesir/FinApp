"""
Alembic Migration Environment Configuration
Handles database migrations for Trading Bot
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context
import os
import sys

# Add the parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.config import settings
from app.models.base import Base

# Import all models to register them with Base.metadata
from app.models.user import User, UserProfile
from app.models.portfolio import Portfolio, PortfolioTransaction, Watchlist

# Alembic Config object
config = context.config

# Setup logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def get_database_url():
    """Get database URL from environment or settings"""
    url = os.getenv("DATABASE_URL", settings.database_url)
    
    # Fix postgres:// to postgresql:// for SQLAlchemy 2.0+
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    
    # Add SSL for Neon
    if "neon" in url.lower() and "sslmode" not in url:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}sslmode=require"
    
    return url


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This configures the context with just a URL
    and not an Engine, which means we can't actually
    access the database but can generate SQL scripts.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    Creates an Engine and associates a connection with the context.
    """
    url = get_database_url()
    
    # Configure engine for PostgreSQL or SQLite
    if url.startswith("sqlite"):
        connectable = create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=pool.StaticPool,
        )
    else:
        connectable = create_engine(
            url,
            poolclass=pool.NullPool,  # Use NullPool for migrations
        )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
