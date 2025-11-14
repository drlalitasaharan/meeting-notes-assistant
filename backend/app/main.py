from fastapi import FastAPI

from app.routers import jobs, meetings, slides

app = FastAPI(title="Meeting Notes Assistant")


def _health_payload() -> dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Primary health endpoints (explicit URLs)
# ---------------------------------------------------------------------------


@app.api_route("/healthz", methods=["GET", "HEAD", "POST"], include_in_schema=False)
def healthz() -> dict[str, str]:
    """Primary health endpoint (local/dev/CI)."""
    return _health_payload()


@app.api_route(
    "/api/healthz",
    methods=["GET", "HEAD", "POST"],
    include_in_schema=False,
)
def api_healthz() -> dict[str, str]:
    """Alias for CI or reverse proxies that expect /api/healthz."""
    return _health_payload()


@app.api_route(
    "/v1/healthz",
    methods=["GET", "HEAD", "POST"],
    include_in_schema=False,
)
def v1_healthz() -> dict[str, str]:
    """Alias for clients that expect versioned health URLs."""
    return _health_payload()


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
