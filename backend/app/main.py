import importlib
import logging
import os

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.api import api as api_router
from app.routers import meeting_artifacts
from app.routers.health import router as health_router
from app.routers.openapi_force import router as openapi_router
from app.routers.rq_jobs import router as rq_router

app = FastAPI()


# --- auto-include optional routers (safe if missing) ---------------------------


def _try_include(modpath: str, attr: str = "router") -> None:
    """Best-effort include for optional routers.

    If the module or attribute is missing (or raises on import),
    we just skip it. This keeps dev/test flexible.
    """
    try:
        mod = importlib.import_module(modpath)
        router = getattr(mod, attr)
    except Exception:
        return
    app.include_router(router)


for mod in [
    "app.routers.jobs",
    "app.routers.meetings",
    "app.routers.slides",
    "app.routers.metrics",
    "app.routers.dev",
]:
    _try_include(mod)

# --- core routers that should always be present --------------------------------

app.include_router(health_router)
app.include_router(openapi_router)
app.include_router(rq_router)

# Conditionally include notes_api:
# - Respect SKIP_NOTES_API env var (1/true/yes -> skip)
# - If import fails (e.g. DB reflection issues), log and move on.
if os.getenv("SKIP_NOTES_API", "0").lower() not in ("1", "true", "yes"):
    try:
        from app.routers import notes_api

        app.include_router(notes_api.router)
    except Exception as exc:  # pragma: no cover - defensive
        logging.error("notes_api import failed: %s", exc)

# Meeting artifacts router (static-ish assets, links, etc.)
app.include_router(meeting_artifacts.router)


# --- health & metrics ----------------------------------------------------------


@app.get("/healthz")
def healthz() -> dict:
    """Simple liveness endpoint used by Docker, Traefik, CI, etc."""
    return {"status": "ok"}


# Mount versioned API once (/v1/…)
app.include_router(api_router)

# Expose Prometheus metrics at /metrics (not in OpenAPI schema)
Instrumentator().instrument(app).expose(
    app,
    endpoint="/metrics",
    include_in_schema=False,
)
