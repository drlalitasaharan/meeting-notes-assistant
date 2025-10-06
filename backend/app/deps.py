# backend/app/deps.py
from __future__ import annotations

from fastapi import Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.packages.shared.env import settings

from .core.db import SessionLocal


def get_db() -> Session:
    """Yield a SQLAlchemy session and ensure it's closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_api_key(x_api_key: str | None = Header(default=None)) -> bool:
    """
    Simple header-based API key check.
    Reads the expected key from settings.API_KEY (loaded from .env/env vars).
    """
    if x_api_key == settings.API_KEY:
        return True
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
    )


__all__ = ["get_db", "require_api_key"]

