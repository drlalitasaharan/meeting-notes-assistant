# backend/app/core/db.py
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.packages.shared.env import settings

# Use a dev-friendly default (e.g., sqlite) if not overridden via env/.env
DATABASE_URL = settings.DATABASE_URL

_common_engine_kwargs = {
    "future": True,
    "pool_pre_ping": True,
}

if DATABASE_URL.startswith("sqlite"):
    # Needed for SQLite when used across threads (e.g., with FastAPI TestClient)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        **_common_engine_kwargs,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        **_common_engine_kwargs,
    )

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

__all__ = ["SessionLocal", "engine"]

