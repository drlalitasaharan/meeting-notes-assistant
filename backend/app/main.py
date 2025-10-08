# backend/app/main.py
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..packages.shared.models import Base
from .db import engine
from .deps import require_api_key
from .routers import jobs, meetings, slides


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Initialize application resources.

    - Ensures tables/columns exist for fresh SQLite DBs in CI/dev.
    """
    Base.metadata.create_all(bind=engine)
    yield


app: FastAPI = FastAPI(title="Meeting Notes Assistant API", lifespan=lifespan)

# --- CORS (permissive; tighten in prod) ---
# In production, replace ["*"] with explicit origins, e.g.:
# ["http://localhost:8501", "https://your-frontend.example"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# -----------------------------------------


@app.get("/healthz", include_in_schema=False)
def healthz() -> dict[str, bool]:
    return {"ok": True}


# Versioned API: routers use local prefixes ("/meetings", "/jobs", etc.).
# We add "/v1" exactly once here and attach the API-key guard globally.
v1_dependencies = [Depends(require_api_key)]

app.include_router(meetings.router, prefix="/v1", dependencies=v1_dependencies)
app.include_router(slides.router,   prefix="/v1", dependencies=v1_dependencies)
app.include_router(jobs.router,     prefix="/v1", dependencies=v1_dependencies)

