from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from rq.job import Job
from rq.registry import (
    DeferredJobRegistry,
    FailedJobRegistry,
    FinishedJobRegistry,
    ScheduledJobRegistry,
    StartedJobRegistry,
)

from app.jobs.queue import get_queue, get_redis

router = APIRouter(prefix="/v1", tags=["jobs"])


class JobCreate(BaseModel):
    type: str
    payload: dict | None = None


@router.post("/jobs")
def create_job(body: JobCreate):
    if body.type != "demo":
        raise HTTPException(status_code=400, detail="unsupported type")
    app_job_id = str(uuid4())
    q = get_queue()
    job = q.enqueue("worker.tasks.demo_job", kwargs={"job_id": app_job_id, "payload": body.payload})
    job.meta = job.meta or {}
    job.meta["app_job_id"] = app_job_id
    job.save_meta()
    return {"id": app_job_id, "rq_id": job.id, "status": "queued"}


@router.get("/jobs/{job_id}")
def read_job(job_id: str):
    r = get_redis()
    q = get_queue()

    ids = set(q.get_job_ids())
    for Reg in (
        StartedJobRegistry,
        FinishedJobRegistry,
        FailedJobRegistry,
        ScheduledJobRegistry,
        DeferredJobRegistry,
    ):
        try:
            ids.update(Reg(q.name, connection=r).get_job_ids())
        except Exception:
            pass

    status, artifact = "queued", None
    for jid in ids:
        try:
            j = Job.fetch(jid, connection=r)
            if (j.kwargs or {}).get("job_id") == job_id or (j.meta or {}).get(
                "app_job_id"
            ) == job_id:
                status = j.get_status(refresh=True)
                artifact = (j.meta or {}).get("artifact_url") or getattr(j, "result", None)
                break
        except Exception:
            pass

    return {"id": job_id, "status": status, "artifact_url": artifact}
