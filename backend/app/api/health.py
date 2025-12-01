from __future__ import annotations

from fastapi import APIRouter

try:
    from sqlalchemy import text
    from sqlalchemy.exc import SQLAlchemyError

    from app.db import SessionLocal  # type: ignore
except Exception:  # noqa: BLE001
    SessionLocal = None  # type: ignore
    SQLAlchemyError = Exception  # type: ignore
    text = None  # type: ignore

try:
    # Queue helpers live under app.jobs.queue
    from app.jobs.queue import get_redis  # type: ignore
except Exception:  # noqa: BLE001
    get_redis = None  # type: ignore

try:
    from app.storage import health_check as storage_health_check
except Exception:  # noqa: BLE001

    def storage_health_check() -> dict:  # type: ignore
        return {"status": "skipped", "detail": "storage health check not wired"}


router = APIRouter(tags=["health"])


def _check_db() -> dict:
    if SessionLocal is None or text is None:
        return {"status": "skipped", "detail": "DB session not configured"}

    try:
        with SessionLocal() as session:  # type: ignore
            session.execute(text("SELECT 1"))  # type: ignore
        return {"status": "ok"}
    except SQLAlchemyError as exc:  # type: ignore
        return {"status": "error", "detail": str(exc)}


def _check_redis() -> dict:
    if get_redis is None:
        return {"status": "skipped", "detail": "Redis not configured"}

    try:
        redis = get_redis()
        ping = getattr(redis, "ping", None)
        if callable(ping):
            ping()
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "detail": str(exc)}


@router.get("/healthz", include_in_schema=False)
def healthz() -> dict:
    """
    Combined liveness/readiness endpoint.

    - DB: simple SELECT 1
    - Redis: PING (or skipped if not wired)
    - Storage: storage.health_check()
    """
    db = _check_db()
    redis = _check_redis()
    storage = storage_health_check()

    checks = {
        "db": db,
        "redis": redis,
        "storage": storage,
    }

    overall = "ok" if all(c["status"] != "error" for c in checks.values()) else "error"

    return {"status": overall, "checks": checks}
