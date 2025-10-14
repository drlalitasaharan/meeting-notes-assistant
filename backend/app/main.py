from fastapi import FastAPI, HTTPException
from rq import Queue
from rq.job import Job

# NEW router that contains /v1/meetings, /process, /notes, /transcript, /summary
from app.routers import notes_api
from worker.redis_client import get_redis

try:
    from app.routers import processing_api
except Exception as e:
    import logging

    logging.error("processing_api import failed: %s", e)
    processing_api = None

app = FastAPI()

# include our modern router
app.include_router(notes_api.router)


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
