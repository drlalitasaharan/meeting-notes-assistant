# backend/app/deps.py
from __future__ import annotations

import os
from typing import Generator, Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.auth import decode_access_token


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


def get_current_user(
    authorization: Optional[str] = Header(
        default=None,
        alias="Authorization",
        convert_underscores=False,
    ),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
        )

    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )

    user = db.get(User, int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    return user


def _configured_admin_emails() -> set[str]:
    """
    Return normalized admin email addresses.

    The value is read at request time so environment changes do not require
    importing this module again during tests or local development.
    """
    raw_value = os.getenv("ADMIN_EMAILS", "")
    return {email.strip().lower() for email in raw_value.split(",") if email.strip()}


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Require the authenticated user's email to be explicitly allowlisted.

    Access fails closed when ADMIN_EMAILS is unset or empty.
    """
    admin_emails = _configured_admin_emails()
    current_email = current_user.email.strip().lower()

    if not admin_emails or current_email not in admin_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )

    return current_user


__all__ = [
    "get_db",
    "require_api_key",
    "get_current_user",
    "require_admin",
]
