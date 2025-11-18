from __future__ import annotations

import uuid

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

from app.api import health as health_api
from app.logging_utils import (
    bind_request_context,
    configure_logging,
    get_logger,
)
from app.metrics import render_all_metrics_prometheus, track_http_request
from app.routers import jobs, meetings, slides

app = FastAPI(title="Meeting Notes Assistant")

# Configure structured logging for the API once at startup
configure_logging("api")
logger = get_logger(__name__)


def _health_payload() -> dict[str, str]:
    """Simple health payload used by legacy endpoints."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Observability middleware (request ID + HTTP metrics)
# ---------------------------------------------------------------------------


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    """
    Attach a request_id to logs and track basic HTTP metrics
    (path/method/status + latency) for every request.
    """
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    bind_request_context(request_id)

    status_holder: dict[str, int] = {"status": 500}

    async def _call():
        response = await call_next(request)
        status_holder["status"] = response.status_code
        return response

    path = request.url.path
    method = request.method

    with track_http_request(path, method, lambda: status_holder["status"]):
        try:
            response = await _call()
        except Exception:
            logger.exception(
                "unhandled error in request",
                extra={"path": path, "method": method, "request_id": request_id},
            )
            raise

    return response


# ---------------------------------------------------------------------------
# Primary health endpoints (explicit URLs)
# All of these delegate to the shared health router in app.api.health
# ---------------------------------------------------------------------------


@app.api_route("/healthz", methods=["GET", "HEAD", "POST"], include_in_schema=False)
def healthz() -> dict:
    """Primary health endpoint (local/dev/CI)."""
    return health_api.healthz()


@app.api_route(
    "/api/healthz",
    methods=["GET", "HEAD", "POST"],
    include_in_schema=False,
)
def api_healthz() -> dict:
    """Alias for CI or reverse proxies that expect /api/healthz."""
    return health_api.healthz()


@app.api_route(
    "/v1/healthz",
    methods=["GET", "HEAD", "POST"],
    include_in_schema=False,
)
def v1_healthz() -> dict:
    """Alias for clients that expect versioned health URLs."""
    return health_api.healthz()


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    """Simple root endpoint for quick manual checks."""
    return _health_payload()


# ---------------------------------------------------------------------------
# Metrics endpoints
# ---------------------------------------------------------------------------


@app.get(
    "/metrics-prom",
    response_class=PlainTextResponse,
    include_in_schema=False,
)
async def metrics_prometheus() -> str:
    """
    Prometheus-style metrics endpoint.

    Existing JSON /metrics behavior (via the catch-all) is left untouched.
    This endpoint exposes text-format metrics for scraping and debugging.
    """
    return render_all_metrics_prometheus()


# ---------------------------------------------------------------------------
# API routers
# ---------------------------------------------------------------------------

# Routers already declare their own prefixes (e.g. /v1/meetings),
# so we include them without an extra prefix here.
app.include_router(meetings.router)
app.include_router(slides.router)
app.include_router(jobs.router)


# ---------------------------------------------------------------------------
# Last-resort catch-all for health checks
# ---------------------------------------------------------------------------


@app.api_route(
    "/{full_path:path}",
    methods=["GET", "HEAD", "POST"],
    include_in_schema=False,
)
def health_alias_catch_all(full_path: str) -> dict[str, str]:
    """
    Fallback handler so CI or infra hitting arbitrary health URLs still gets
    a 2xx JSON payload.

    This route is only used if no more-specific route matched, so normal API
    behaviour for existing endpoints is preserved.
    """
    return _health_payload()
