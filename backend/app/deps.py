# backend/app/deps.py
from __future__ import annotations

import os
from typing import Generator, Optional

from fastapi import Header, HTTPException, status
from sqlalchemy.orm import Session


def get_db() -> Generator[Session, None, None]:
    """
    Yield a SQLAlchemy session from the *single* canonical factory.
    Importing inside the function avoids any shadowing by legacy modules.
    """
    from app.core.db import SessionLocal as _SessionLocal  # hard-bind to core

    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _expected_key() -> str | None:
    """
    Pull the API key at request time so startup never fails if it's missing.
    Accept either API_KEY or X_API_KEY.
    """
    return os.getenv("API_KEY") or os.getenv("X_API_KEY")


async def require_api_key(
    x_api_key: Optional[str] = Header(
        default=None,
        alias="X-API-Key",  # exact header name expected from clients
        convert_underscores=False,  # do not transform to X-API-Key -> X_API_Key
    ),
) -> bool:
    """
    Header-based API key guard.

    Dev-friendly behavior:
      - If no key is configured (no env set), allow requests.
    Prod behavior:
      - Set API_KEY (or X_API_KEY) in the environment and require clients to
        send the same value in the X-API-Key header.
    """
    expected = _expected_key()
    if expected is None or x_api_key == expected:
        return True

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
    )


__all__ = ["get_db", "require_api_key"]
