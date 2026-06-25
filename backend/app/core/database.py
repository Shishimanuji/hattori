"""Database connection and session management"""
from sqlalchemy import create_engine, event, String, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from sqlalchemy.types import TypeDecorator, JSON
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create custom JSONB type that works with SQLite
class JSONB(TypeDecorator):
    """JSONB type that works with SQLite by falling back to JSON"""
    impl = JSON
    cache_ok = True

# Patch for SQLite compatibility
import sqlalchemy.dialects.postgresql
sqlalchemy.dialects.postgresql.JSONB = JSONB

# Create database engine
if settings.database_url.startswith("sqlite"):
    engine = create_engine(
        settings.database_url,
        echo=settings.database_echo,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        settings.database_url,
        echo=settings.database_echo,
        poolclass=NullPool,  # Use NullPool for now, can be changed in production
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for models
Base = declarative_base()


def get_db() -> Session:
    """
    Dependency for FastAPI to provide database session to routes.
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> bool:
    """
    Initialize database connection and verify connectivity.
    Returns True if successful, False if connection fails.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False


def create_all_tables() -> None:
    """Create all tables defined in models"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise
