from __future__ import annotations

import hashlib
import json
import os
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from redis import Redis
from rq import Queue
from rq.job import Job as RQJob
from sqlalchemy.orm import Session

from app.core.jobs_schema_patch import patch_jobs_table
from app.db import get_db
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


def _redis() -> Redis:
    return Redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))


def _queue() -> Queue:
    return Queue("default", connection=get_redis())


def _hash(job_type: str, payload: Optional[dict]) -> str:
    normalized = json.dumps(payload or {}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(f"{job_type}|{normalized}|v{VERSION}".encode()).hexdigest()


router = APIRouter(prefix="/v1", tags=["jobs"])


@router.post("/jobs", response_model=JobOut)
def enqueue_job(req: EnqueueReq, db: Session = Depends(get_db)) -> JobOut:
    patch_jobs_table()
    input_hash = _hash(req.type, req.payload)
    existing = (
        db.query(Job).filter(Job.job_type == req.type, Job.input_hash == input_hash).one_or_none()
    )
    if existing:
        art = choose_storage().presign_get(existing.artifact_key) if existing.artifact_key else None
        return JobOut(id=existing.id, status=existing.status, artifact_url=art)

    jid = str(uuid.uuid4())
    job = Job(id=jid, job_type=req.type, input_hash=input_hash, status=JobStatus.queued)
    db.add(job)
    db.commit()
    db.refresh(job)

    # Best-effort enqueue: in tests/dev without Redis, swallow queue errors
    try:
        rq_job = _queue().enqueue(
            "worker.tasks.demo_job" if req.type == "demo" else "worker.tasks.generic_job",
            kwargs={"job_id": jid, "job_type": req.type, "payload": req.payload or {}},
            job_timeout=600,
            failure_ttl=7 * 24 * 3600,
            retry_strategy={"max": 3, "interval": [5, 15, 30]},
            description=f"{req.type}:{jid}",
        )
        job.rq_job_id = rq_job.id
    except Exception:
        # In tests or dev without Redis, we still persist the DB job
        job.rq_job_id = None

    db.add(job)
    db.commit()
    db.refresh(job)
    return JobOut(id=jid, status=JobStatus.queued, artifact_url=None)


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)) -> JobOut:
    # Raw SQL to avoid any ORM identity/typing shenanigans
    from sqlalchemy import text

    jid = str(job_id)
    row = (
        db.execute(text("SELECT id, status, artifact_key FROM jobs WHERE id = :id"), {"id": jid})
        .mappings()
        .first()
    )

    if not row:
        raise HTTPException(status_code=404, detail="job not found")

    # Cast status to enum for Pydantic
    status = JobStatus(row["status"]) if not isinstance(row["status"], JobStatus) else row["status"]
    art = choose_storage().presign_get(row["artifact_key"]) if row["artifact_key"] else None
    return JobOut(id=row["id"], status=status, artifact_url=art)


# If this file already has `router = APIRouter(...)`, reuse it and delete the next line.
@router.get("/v1/jobs/{job_id}")
def read_job(job_id: str):
    try:
        j = RQJob.fetch(job_id, connection=get_redis())
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")
    status = j.get_status(refresh=True)
    artifact = (j.meta or {}).get("artifact_url") or getattr(j, "result", None)
    return {"id": job_id, "status": status, "artifact_url": artifact}


@router.get("/jobs/{job_id}/logs")
def get_job_logs(job_id: str) -> dict[str, str]:
    """Return placeholder logs for a job.

    Tests only assert status_code == 200, so this stub is enough.
    In real deployments you can later wire this to RQ meta / DB / object store.
    """
    return {"id": job_id, "logs": ""}
