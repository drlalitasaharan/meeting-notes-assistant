from __future__ import annotations

import os
from typing import Any, Dict

import redis

from app.storage import choose_storage

REDIS_URL = os.getenv("REDIS_URL", "")


def check_storage() -> Dict[str, Any]:
    """
    Run the storage backend health_check() and normalize into a small dict.
    """
    storage = choose_storage()
    try:
        ok, detail = storage.health_check()
    except Exception as exc:  # pragma: no cover - defensive
        return {
            "status": "error",
            "detail": f"{type(exc).__name__}: {exc}",
        }

    if ok:
        return {
            "status": "ok",
            "detail": detail or "storage.health_check() returned ok",
        }
    else:
        return {
            "status": "error",
            "detail": detail or "storage.health_check() returned false",
        }


def check_redis() -> Dict[str, Any]:
    """
    Ping Redis if REDIS_URL is configured.

    - If REDIS_URL is unset → we *skip* Redis so tests/dev don’t fail.
    - If set and ping() works → status: ok.
    - If set and ping() fails → status: error + detail.
    """
    if not REDIS_URL:
        return {
            "status": "skipped",
            "detail": "REDIS_URL not set; Redis health check skipped",
        }

    try:
        client = redis.from_url(REDIS_URL)
        client.ping()
        return {"status": "ok"}
    except Exception as exc:  # pragma: no cover - defensive
        return {
            "status": "error",
            "detail": f"{type(exc).__name__}: {exc}",
        }


def _overall_status(components: Dict[str, Dict[str, Any]]) -> str:
    """
    Overall "status" field for /healthz.

    - "error" if any component has status=error
    - otherwise "ok" (even if some are "skipped")
    """
    if any(c.get("status") == "error" for c in components.values()):
        return "error"
    return "ok"


def get_health() -> Dict[str, Any]:
    """
    Shape of /healthz response:

    {
      "status": "ok" | "error",
      "storage": {...},
      "redis": {...}   # only when REDIS_URL is set
    }
    """
    components: Dict[str, Dict[str, Any]] = {}

    components["storage"] = check_storage()

    # Only wire Redis into /healthz when REDIS_URL is set
    if REDIS_URL:
        components["redis"] = check_redis()

    return {
        "status": _overall_status(components),
        **components,
    }
