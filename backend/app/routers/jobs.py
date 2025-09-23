from typing import List, Optional
from fastapi import APIRouter, Query, Response
from pydantic import BaseModel

router = APIRouter(prefix="/jobs", tags=["jobs"])

class JobOut(BaseModel):
    id: int
    type: str
    status: str
    meeting_id: int | None = None
    logs: str | None = None

class JobIn(BaseModel):
    type: str
    meeting_id: int | None = None

# In-memory store (stub)
_jobs: dict[int, JobOut] = {}
_next_id = 1

@router.get("", response_model=List[JobOut])
def list_jobs():
    return list(_jobs.values())

@router.post("", response_model=JobOut)
def enqueue_job(
    body: Optional[JobIn] = None,
    type: Optional[str] = Query(default=None),
    meeting_id: Optional[int] = Query(default=None),
):
    """
    Accepts either JSON body {"type": "...", "meeting_id": N}
    OR query params ?type=...&meeting_id=...
    """
    global _next_id
    job_type = (body.type if body and body.type else type)
    job_meeting_id = (body.meeting_id if body and body.meeting_id is not None else meeting_id)
    if not job_type:
        return Response(status_code=422, content="Missing 'type' (in JSON body or query)")
    jid = _next_id; _next_id += 1
    job = JobOut(id=jid, type=job_type, status="queued", meeting_id=job_meeting_id, logs="queued\n")
    _jobs[jid] = job
    # stub: instantly complete
    job.status = "done"
    job.logs += "done\n"
    return job

@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int):
    job = _jobs.get(job_id)
    if not job:
        return Response(status_code=404, content='{"detail":"Job not found"}', media_type="application/json")
    return job

@router.get("/{job_id}/logs")
def get_job_logs(job_id: int):
    job = _jobs.get(job_id)
    logs = job.logs if job else ""
    return Response(content=logs, media_type="text/plain", status_code=200 if job else 404)

