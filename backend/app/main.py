from fastapi import FastAPI, HTTPException

from app.routers import jobs, meetings, slides

app = FastAPI(title="Meeting Notes Assistant")


def _health_payload() -> dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Primary health endpoints
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


# Routers already declare their own prefixes (e.g. /v1/meetings),
# so we include them without an extra prefix here.
app.include_router(meetings.router)
app.include_router(slides.router)
app.include_router(jobs.router)


# ---------------------------------------------------------------------------
# Defensive catch-all for health checks
# ---------------------------------------------------------------------------

_HEALTH_PATHS = {
    "health",
    "healthz",
    "api/health",
    "api/healthz",
    "v1/health",
    "v1/healthz",
    "api/v1/health",
    "api/v1/healthz",
}


@app.api_route(
    "/{full_path:path}",
    methods=["GET", "HEAD", "POST"],
    include_in_schema=False,
)
def health_alias_catch_all(full_path: str) -> dict[str, str]:
    """
    Fallback handler so CI or infra hitting slightly different health URLs
    still get a 2xx JSON payload, while non-health paths still 404.

    Normalises leading/trailing slashes so that /healthz/, /api/healthz/, etc.
    behave like their slash-less variants and also accepts any URL whose final
    segment looks like "health" or "healthz".
    """
    normalized = full_path.strip("/")

    # Exact matches like "healthz", "api/healthz", "api/v1/healthz", ...
    if normalized in _HEALTH_PATHS:
        return _health_payload()

    # Also accept things like "/foo/healthz" or "/foo/bar/health"
    segments = [segment for segment in normalized.split("/") if segment]
    if segments and segments[-1].lower() in {"health", "healthz"}:
        return _health_payload()

    raise HTTPException(status_code=404, detail="Not Found")
