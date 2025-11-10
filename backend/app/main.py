import importlib
import os
from types import ModuleType

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.api import api as api_router
from app.routers.health import router as health_router
from app.routers.openapi_force import router as openapi_router
from app.routers.rq_jobs import router as rq_router

if not os.getenv("SKIP_NOTES_API"):
    from app.routers import notes_api
from app.routers import meeting_artifacts

processing_api: ModuleType | None = None
try:
    from app.routers import processing_api as _processing_api

    processing_api = _processing_api
except Exception as e:
    import logging

    logging.error("processing_api import failed: %s", e)


# NEW router that contains /v1/meetings, /process, /notes, /transcript, /summary

try:
    pass
except Exception as e:
    import logging

    logging.error("processing_api import failed: %s", e)
    from typing import Any, cast

    processing_api = cast(Any, None)

    logging.error("processing_api import failed: %s", e)
    processing_api = None

    logging.error("processing_api import failed: %s", e)

app = FastAPI()
# --- auto-include routers if present ---


def _try_include(modpath: str, attr: str = "router"):
    try:
        mod = importlib.import_module(modpath)
        app.include_router(getattr(mod, attr))
    except Exception:
        pass  # module/attr missing is fine in dev


for mod in [
    "app.routers.openapi_force",
    "app.routers.health",
    "app.routers.rq_jobs",
    "app.routers.jobs",
    "app.routers.meetings",
    "app.routers.slides",
    "app.routers.metrics",
    "app.routers.dev",
]:
    _try_include(mod)
# --- end auto-include ---

app.include_router(health_router)
app.include_router(openapi_router)
app.include_router(rq_router)

# include our modern router
if os.getenv("SKIP_NOTES_API", "0").lower() not in ("1", "true", "yes"):
    from app.routers import notes_api

    app.include_router(notes_api.router)
app.include_router(meeting_artifacts.router)


# small health endpoint (was missing on your last run)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


# Mount versioned API once
app.include_router(api_router)
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
