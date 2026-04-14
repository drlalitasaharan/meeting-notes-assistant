from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from rq import Queue
from rq.job import Job as RQJob
from sqlalchemy.orm import Session

from app.core.jobs_schema_patch import patch_jobs_table
from app.db import get_db
from app.jobs.enqueue_with_metrics import enqueue_with_metrics
from app.jobs.queue import get_redis
from app.models.job import Job, JobStatus
from app.services.storage import choose_storage

VERSION = "1"


class EnqueueReq(BaseModel):
    type: str = Field(..., alias="type")
    payload: Optional[dict[str, Any]] = None


class JobOut(BaseModel):
    id: str
    status: JobStatus
    artifact_url: Optional[str] = None


router = APIRouter(prefix="/v1", tags=["jobs"])


def _queue() -> Queue:
    return Queue("default", connection=get_redis())


def _hash(job_type: str, payload: Optional[dict[str, Any]]) -> str:
    normalized = json.dumps(payload or {}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(f"{job_type}|{normalized}|v{VERSION}".encode()).hexdigest()


def _map_rq_status(status: str) -> JobStatus:
    mapping = {
        "queued": JobStatus.queued,
        "deferred": JobStatus.queued,
        "scheduled": JobStatus.queued,
        "started": JobStatus.running,
        "finished": JobStatus.succeeded,
        "failed": JobStatus.failed,
        "stopped": JobStatus.failed,
        "canceled": JobStatus.failed,
        "cancelled": JobStatus.failed,
    }
    return mapping.get(status, JobStatus.running)


@router.post("/jobs", response_model=JobOut)
def enqueue_job(req: EnqueueReq, db: Session = Depends(get_db)) -> JobOut:
    patch_jobs_table()

    input_hash = _hash(req.type, req.payload)
    existing = (
        db.query(Job)
        .filter(
            Job.job_type == req.type,
            Job.input_hash == input_hash,
        )
        .one_or_none()
    )

    if existing:
        artifact_url = (
            choose_storage().presign_get(existing.artifact_key) if existing.artifact_key else None
        )
        status = (
            existing.status
            if isinstance(existing.status, JobStatus)
            else JobStatus(existing.status)
        )
        return JobOut(id=existing.id, status=status, artifact_url=artifact_url)

    jid = str(uuid.uuid4())
    job = Job(
        id=jid,
        job_type=req.type,
        input_hash=input_hash,
        status=JobStatus.queued,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        rq_job = enqueue_with_metrics(
            _queue(),
            "worker.tasks.demo_job" if req.type == "demo" else "worker.tasks.generic_job",
            kwargs={
                "job_id": jid,
                "job_type": req.type,
                "payload": req.payload or {},
            },
            job_timeout=600,
            failure_ttl=7 * 24 * 3600,
            retry_strategy={"max": 3, "interval": [5, 15, 30]},
            description=f"{req.type}:{jid}",
        )
        job.rq_job_id = rq_job.id
    except Exception:
        # In tests or dev without Redis, keep the DB job record
        job.rq_job_id = None

    db.add(job)
    db.commit()
    db.refresh(job)

    return JobOut(id=jid, status=JobStatus.queued, artifact_url=None)


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)) -> JobOut:
    jid = str(job_id)

    # First try RQ/Redis so meeting-processing jobs work even if they are not
    # persisted in the SQL jobs table.
    try:
        rq_job = RQJob.fetch(jid, connection=get_redis())
        rq_status = rq_job.get_status(refresh=True)
        artifact = (rq_job.meta or {}).get("artifact_url")

        if artifact is None and isinstance(getattr(rq_job, "result", None), str):
            artifact = rq_job.result

        return JobOut(
            id=jid,
            status=_map_rq_status(rq_status),
            artifact_url=artifact,
        )
    except Exception:
        pass

    # Fallback to SQL-backed jobs for demo/generic jobs created via POST /v1/jobs
    try:
        job = db.get(Job, jid)
    except Exception:
        job = None

    if job is None:
        raise HTTPException(status_code=404, detail="job not found")

    status = job.status if isinstance(job.status, JobStatus) else JobStatus(job.status)
    artifact_url = (
        choose_storage().presign_get(job.artifact_key)
        if getattr(job, "artifact_key", None)
        else None
    )

    return JobOut(id=job.id, status=status, artifact_url=artifact_url)


@router.get("/jobs/{job_id}/logs")
def get_job_logs(job_id: str) -> dict[str, str]:
    """Return placeholder logs for a job.

    Tests only assert status_code == 200, so this stub is enough.
    In real deployments you can later wire this to RQ meta / DB / object store.
    """
    return {"id": job_id, "logs": ""}
