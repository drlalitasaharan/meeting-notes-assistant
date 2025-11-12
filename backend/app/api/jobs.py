from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from rq.job import Job

from app.jobs import get_queue

router = APIRouter()  # no prefix here


class SubmitJobRequest(BaseModel):
    type: str = Field("demo")
    payload: Dict[str, Any] = {}


@router.post("", status_code=202)
def submit_job(req: SubmitJobRequest):
    if req.type != "demo":
        raise HTTPException(status_code=400, detail="Unsupported job type; use 'demo'")
    job = get_queue().enqueue("app.jobs.demo.run", req.payload, job_timeout=300)
    return {"job_id": job.get_id()}


@router.get("/{job_id}")
def get_job(job_id: str):
    try:
        job = Job.fetch(job_id, connection=get_queue().connection)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")
    status = job.get_status()
    out = {"job_id": job_id, "status": status}
    if status == "finished":
        out["result"] = job.result
    if status == "failed":
        out["error"] = str(job.exc_info or "unknown error")
    return out
