from fastapi import FastAPI

from app.routers import jobs, meetings, slides

app = FastAPI(title="Meeting Notes Assistant")


@app.get("/healthz", include_in_schema=False)
def healthz() -> dict[str, str]:
    """Simple health endpoint for CI smoke checks."""
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    """Optional root endpoint for quick manual checks."""
    return {"status": "ok"}


# NOTE:
# Routers already declare their own prefixes (e.g. /v1/meetings, /v1/jobs),
# so we include them *without* an extra prefix here.
app.include_router(meetings.router)
app.include_router(slides.router)
app.include_router(jobs.router)
