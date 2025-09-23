from fastapi import FastAPI, Depends
from .deps import require_api_key
from .routers import meetings, slides, jobs
from ..packages.shared.models import Base
from .db import engine

app = FastAPI(title="Meeting Notes Assistant API")

@app.on_event("startup")
def _create_all():
    Base.metadata.create_all(bind=engine)


@app.get("/healthz")
def healthz():
    return {"ok": True}
app.include_router(meetings.router, dependencies=[Depends(require_api_key)], prefix="/v1")
app.include_router(slides.router,   dependencies=[Depends(require_api_key)], prefix="/v1")
app.include_router(jobs.router,     dependencies=[Depends(require_api_key)], prefix="/v1")
