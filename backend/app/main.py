# backend/app/main.py

from fastapi import FastAPI, Depends

from .deps import require_api_key
from .routers import meetings, slides, jobs
from ..packages.shared.models import Base
from .db import engine

app = FastAPI(title="Meeting Notes Assistant API")


# Ensure tables/columns exist for fresh SQLite DBs (e.g., CI/dev)
@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/healthz")
def healthz():
    return {"ok": True}


# Mount versioned API and protect with API key
app.include_router(
    meetings.router,
    prefix="/v1",
    dependencies=[Depends(require_api_key)],
)
app.include_router(
    slides.router,
    prefix="/v1",
    dependencies=[Depends(require_api_key)],
)
app.include_router(
    jobs.router,
    prefix="/v1",
    dependencies=[Depends(require_api_key)],
)

