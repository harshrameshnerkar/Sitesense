"""
Database Engine and Session Management for SiteSense.
Supports local PostgreSQL, Neon Serverless PostgreSQL, and local SQLite fallback.
"""

import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from services.core.config import get_settings

logger = logging.getLogger("sitesense.database")
settings = get_settings()

db_url = settings.DATABASE_URL
engine = None

# 1. Attempt connection with configured DATABASE_URL (PostgreSQL / Neon)
try:
    if "postgresql" in db_url:
        # PostgreSQL / Neon configuration
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            connect_args={"connect_timeout": 3}
        )
        # Verify connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(f"Connected to PostgreSQL database: {db_url.split('@')[-1] if '@' in db_url else 'local'}")
except Exception as e:
    logger.warning(f"Could not connect to configured PostgreSQL ({db_url}): {e}")
    if settings.DATABASE_FALLBACK_SQLITE:
        fallback_url = "sqlite:///./sitesense.db"
        logger.info(f"Falling back to SQLite: {fallback_url}")
        engine = create_engine(
            fallback_url,
            connect_args={"check_same_thread": False}
        )
    else:
        raise e

# 2. If engine was not initialized yet (e.g. non-postgres URL configured)
if engine is None:
    if "sqlite" in db_url:
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False}
        )
    else:
        engine = create_engine(db_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields an active database session and closes it on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

