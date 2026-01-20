"""
Database Base Configuration
SQLAlchemy setup and session management with Neon PostgreSQL support
"""
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool, QueuePool
from app.config import settings
from app.utils.logger import logger
import os

# Database URL handling
DATABASE_URL = settings.database_url

# Fix Neon PostgreSQL URL format (replace postgres:// with postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SSL mode for Neon (required)
if "neon" in DATABASE_URL.lower() and "sslmode" not in DATABASE_URL:
    separator = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL = f"{DATABASE_URL}{separator}sslmode=require"

# Create engine based on database type
try:
    if DATABASE_URL.startswith("sqlite"):
        # SQLite - for local development
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=settings.log_level.upper() == "DEBUG"
        )
        logger.info("Using SQLite database for development")
    else:
        # PostgreSQL - for production (Neon)
        engine = create_engine(
            DATABASE_URL,
            poolclass=QueuePool,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            pool_recycle=settings.database_pool_recycle,
            pool_pre_ping=True,  # Connection health check
            echo=settings.log_level.upper() == "DEBUG"
        )
        logger.info("Using PostgreSQL database for production")

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception as e:
    import sys, traceback
    print(f"CRITICAL ERROR during database initialization: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    # Don't exit here, let the app try to start so we see the logs on Vercel
    SessionLocal = None
    Base = declarative_base()
    engine = None


def get_db():
    """
    Dependency for getting database session
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables
    Call this on application startup
    """
    # Import all models to register them with Base
    from app.models import user, portfolio
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def check_db_connection() -> bool:
    """
    Check database connection health
    
    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False
