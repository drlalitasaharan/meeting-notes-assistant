# backend/app/core/db.py
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    # When running in the full monorepo / production image
    from packages.shared.env import get_settings  # type: ignore[import]
except ImportError:  # pragma: no cover - fallback for CI/dev
    # When running just the backend (like in this repo/CI), use local settings
    from app.core.settings import get_settings


def _build_engine():
    url = get_settings().DATABASE_URL
    common_kwargs = {
        "future": True,
        "pool_pre_ping": True,
        "pool_recycle": 1800,  # keep pool fresh
    }
    if url.startswith("sqlite"):
        # Required for SQLite with multi-threaded FastAPI
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            **common_kwargs,
        )
    return create_engine(url, **common_kwargs)


engine = _build_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)

__all__ = ["SessionLocal", "engine"]


# Simple FastAPI-style DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
