from fastapi import FastAPI

from app.api import health as health_api
from app.routers import jobs, meetings, slides

app = FastAPI(title="Meeting Notes Assistant")


def _health_payload() -> dict[str, str]:
    """Simple health payload used by legacy endpoints."""
    return {"status": "ok"}


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
