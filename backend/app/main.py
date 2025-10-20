from types import ModuleType

from fastapi import FastAPI, HTTPException
from rq import Queue
from rq.job import Job

from app.routers import meeting_artifacts, notes_api
from worker.redis_client import get_redis

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

# include our modern router
app.include_router(notes_api.router)
app.include_router(meeting_artifacts.router)


# small health endpoint (was missing on your last run)
@app.get("/healthz")
def healthz():
    return {"ok": True}


# minimal job status endpoint (so your polling works)
_rconn = get_redis()
_q = Queue("default", connection=_rconn)


@app.get("/v1/jobs/{job_id}")
def job_status(job_id: str):
    try:
        j = Job.fetch(job_id, connection=_rconn)
    except Exception:
        raise HTTPException(status_code=404, detail="job not found")
    return {
        "id": j.id,
        "func": j.func_name,
        "status": j.get_status(),
        "result": j.result,
    }


if processing_api:
    app.include_router(processing_api.router)
