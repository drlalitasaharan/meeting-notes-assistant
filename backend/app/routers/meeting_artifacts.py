import os

from fastapi import APIRouter, HTTPException
from redis import Redis
from rq import Queue
from sqlalchemy import create_engine
from sqlalchemy import text as sqltext

# Reuse the existing redis helper if present; else fallback to simple Redis()
try:
    from worker.redis_client import get_redis

    rconn: Redis = get_redis()
except Exception:
    rconn = Redis(host="redis", port=6379, db=0)

q = Queue("default", connection=rconn)

DB_URL = os.getenv("DATABASE_URL", "sqlite:////app/backend/dev.db")
engine = create_engine(DB_URL, future=True)

router = APIRouter(prefix="/v1", tags=["meetings-artifacts"])


@router.post("/meetings/{meeting_id}/process")
def process_meeting_endpoint(meeting_id: int):
    job = q.enqueue("worker.tasks_processing.process_meeting", meeting_id, job_timeout=600)
    return {"job_id": job.id, "status": job.get_status()}


@router.get("/meetings/{meeting_id}/transcript")
def get_latest_transcript(meeting_id: int):
    with engine.connect() as conn:
        row = (
            conn.execute(
                sqltext("""
                SELECT id, meeting_id, text, created_at
                FROM transcripts
                WHERE meeting_id = :m
                ORDER BY created_at DESC, id DESC
                LIMIT 1
            """),
                {"m": meeting_id},
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=404, detail="no transcript")
    return dict(row)


@router.get("/meetings/{meeting_id}/summary")
def get_latest_summary(meeting_id: int):
    with engine.connect() as conn:
        row = (
            conn.execute(
                sqltext("""
                SELECT id, meeting_id, model, text, created_at
                FROM summaries
                WHERE meeting_id = :m
                ORDER BY created_at DESC, id DESC
                LIMIT 1
            """),
                {"m": meeting_id},
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=404, detail="no summary")
    return dict(row)
