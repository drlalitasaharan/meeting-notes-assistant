from fastapi import FastAPI, HTTPException

from app.routers import jobs, meetings, slides

app = FastAPI(title="Meeting Notes Assistant")


def _health_payload() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/healthz", include_in_schema=False)
def healthz() -> dict[str, str]:
    """Primary health endpoint (local/dev/CI)."""
    return _health_payload()


@app.get("/api/healthz", include_in_schema=False)
def api_healthz() -> dict[str, str]:
    """Alias for CI or reverse proxies that expect /api/healthz."""
    return _health_payload()


@app.get("/v1/healthz", include_in_schema=False)
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
    "healthz",
    "health",
    "api/healthz",
    "api/health",
    "v1/healthz",
    "v1/health",
    "api/v1/healthz",
    "api/v1/health",
}


@app.get("/{full_path:path}", include_in_schema=False)
def health_alias_catch_all(full_path: str) -> dict[str, str]:
    """
    Fallback handler so CI or infra hitting slightly different health URLs
    still get a 200 JSON payload.
    """
    if full_path in _HEALTH_PATHS:
        return _health_payload()
    raise HTTPException(status_code=404, detail="Not Found")
