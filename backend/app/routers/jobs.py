from __future__ import annotations
from typing import Optional, List
from datetime import datetime
import time

from fastapi import APIRouter, Query, Response, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ...packages.shared.models import Job

router = APIRouter(prefix="/jobs", tags=["jobs"])

class JobOut(BaseModel):
    id: int
    type: str
    status: str
    meeting_id: int | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    logs: str | None = None
    class Config:
        from_attributes = True

class JobIn(BaseModel):
    type: str
    meeting_id: int | None = None

@router.get("", response_model=List[JobOut])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(Job).order_by(Job.id.desc()).all()

def _append_logs(db: Session, job: Job, line: str) -> None:
    job.logs = (job.logs or "") + line
    db.add(job); db.commit()

def _run_job_logic(db: Session, job_id: int) -> None:
    job = db.get(Job, job_id)
    if not job:
        return
    job.status = "running"
    job.started_at = datetime.utcnow()
    db.add(job); db.commit()
    try:
        for step in ("fetch slides\n", "extract text\n", "summarize\n"):
            _append_logs(db, job, step)
            time.sleep(0.2)
        job.status = "done"
        job.finished_at = datetime.utcnow()
        _append_logs(db, job, "done\n")
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.finished_at = datetime.utcnow()
        _append_logs(db, job, f"error: {e}\n")

@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def enqueue_job(
    background: BackgroundTasks,
    body: Optional[JobIn] = None,
    type: Optional[str] = Query(default=None),
    meeting_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    job_type = (body.type if body and body.type else type)
    job_meeting_id = (body.meeting_id if body and body.meeting_id is not None else meeting_id)
    if not job_type:
        raise HTTPException(status_code=422, detail="Missing 'type' (in JSON body or query)")

    job = Job(type=job_type, meeting_id=job_meeting_id, status="queued", logs="queued\n")
    db.add(job); db.commit(); db.refresh(job)
    background.add_task(_run_job_logic, db, job.id)
    return job

@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/{job_id}/logs")
def get_job_logs(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        return Response(status_code=404, content="Job not found", media_type="text/plain")
    return Response(content=(job.logs or ""), media_type="text/plain", status_code=200)
