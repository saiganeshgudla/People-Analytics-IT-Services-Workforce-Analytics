"""
backend/app/core/database.py
──────────────────────────────
SQLAlchemy async engine and session factory.
Falls back to SQLite for local development without PostgreSQL.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from backend.app.core.config import get_settings

log = logging.getLogger(__name__)
settings = get_settings()


class Base(DeclarativeBase):
    pass


def get_engine():
    """Create database engine, falling back to SQLite if PG unavailable."""
    try:
        engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            echo=settings.debug,
        )
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        log.info(f"✅ Connected to PostgreSQL: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")
        return engine
    except Exception as e:
        log.warning(f"PostgreSQL unavailable ({e}). Falling back to SQLite.")
        sqlite_path = Path("data/peoplelens.db")
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(f"sqlite:///{sqlite_path}", echo=settings.debug)
        return engine


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """FastAPI dependency: yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
