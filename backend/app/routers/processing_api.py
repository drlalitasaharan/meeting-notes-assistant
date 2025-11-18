import os
import re

from fastapi import APIRouter, HTTPException
from rq import Queue
from sqlalchemy import MetaData, Table, create_engine, desc, insert, select
from sqlalchemy.exc import SQLAlchemyError

from app.jobs.enqueue_with_metrics import enqueue_with_metrics
from worker.redis_client import get_redis

router = APIRouter()


# ---------- simple summarizer (no NLTK/HF) ----------
def _summarize_simple(text: str, sentences: int = 3) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    bullets = [
        (ln[2:].strip() if ln.startswith(("- ", "* ")) else ln)
        for ln in lines
        if ln.startswith(("- ", "* "))
    ]
    if bullets:
        return " ".join(bullets[: max(1, sentences)])
    chunks = re.split(r"(?<=[.!?])\s+", " ".join(lines))
    chunks = [c.strip() for c in chunks if c.strip()]
    return " ".join(chunks[: max(1, sentences)])


# ---------- DB helpers (no app.models dependency) ----------
def _get_engine():
    # Use env if provided; fallback to dev SQLite used in your project
    url = os.environ.get("DATABASE_URL", "sqlite+pysqlite:////app/backend/dev.db")
    return create_engine(url, future=True)


def _get_tables(engine):
    md = MetaData()
    trs = Table("transcripts", md, autoload_with=engine)
    sms = Table("summaries", md, autoload_with=engine)
    return trs, sms


@router.get("/v1/meetings/{meeting_id}/resummarize_preview")
def resummarize_preview(meeting_id: int, sentences: int = 3):
    eng = _get_engine()
    transcripts, _ = _get_tables(eng)
    with eng.begin() as conn:
        trow = (
            conn.execute(
                select(transcripts.c.text)
                .where(transcripts.c.meeting_id == meeting_id)
                .order_by(desc(transcripts.c.created_at))
                .limit(1)
            )
            .mappings()
            .first()
        )
        if not trow:
            raise HTTPException(status_code=404, detail="no transcript")
    return {"model": "simple", "preview": _summarize_simple(trow["text"], sentences=sentences)}


@router.post("/v1/meetings/{meeting_id}/resummarize")
def resummarize(meeting_id: int, sentences: int = 3):
    eng = _get_engine()
    transcripts, summaries = _get_tables(eng)
    try:
        with eng.begin() as conn:
            trow = (
                conn.execute(
                    select(transcripts.c.id, transcripts.c.text)
                    .where(transcripts.c.meeting_id == meeting_id)
                    .order_by(desc(transcripts.c.created_at))
                    .limit(1)
                )
                .mappings()
                .first()
            )
            if not trow:
                raise HTTPException(status_code=404, detail="no transcript")

            summary_text = _summarize_simple(trow["text"], sentences=sentences)

            res = conn.execute(
                insert(summaries).values(
                    meeting_id=meeting_id,
                    model="simple",
                    text=summary_text,
                )
            )
            new_id = res.inserted_primary_key[0]
            srow = (
                conn.execute(
                    select(
                        summaries.c.id,
                        summaries.c.meeting_id,
                        summaries.c.model,
                        summaries.c.text,
                        summaries.c.created_at,
                    ).where(summaries.c.id == new_id)
                )
                .mappings()
                .one()
            )
            return dict(srow)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"db error: {e.__class__.__name__}: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"logic error: {e.__class__.__name__}: {e}")


@router.get("/v1/meetings/{meeting_id}/summary")
def get_summary(meeting_id: int):
    eng = _get_engine()
    _, summaries = _get_tables(eng)
    with eng.begin() as conn:
        row = (
            conn.execute(
                select(
                    summaries.c.id,
                    summaries.c.meeting_id,
                    summaries.c.model,
                    summaries.c.text,
                    summaries.c.created_at,
                )
                .where(summaries.c.meeting_id == meeting_id)
                .order_by(desc(summaries.c.created_at))
                .limit(1)
            )
            .mappings()
            .first()
        )
        if not row:
            raise HTTPException(status_code=404, detail="no summary")
        return dict(row)


@router.get("/v1/meetings/{meeting_id}/transcript")
def get_transcript(meeting_id: int):
    eng = _get_engine()
    transcripts, _ = _get_tables(eng)
    with eng.begin() as conn:
        row = (
            conn.execute(
                select(
                    transcripts.c.id,
                    transcripts.c.meeting_id,
                    transcripts.c.text,
                    transcripts.c.created_at,
                )
                .where(transcripts.c.meeting_id == meeting_id)
                .order_by(desc(transcripts.c.created_at))
                .limit(1)
            )
            .mappings()
            .first()
        )
        if not row:
            raise HTTPException(status_code=404, detail="no transcript")
        return dict(row)


_rconn = get_redis()
_q = Queue("default", connection=_rconn)


@router.post("/v1/meetings/{meeting_id}/process", operation_id="enqueue_process_meeting_v1")
def enqueue_process_meeting(meeting_id: int) -> dict:
    # Build Queue on demand to avoid module import side effects
    try:
        q = Queue("default", connection=get_redis())
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"queue init failed: {e.__class__.__name__}: {e}"
        )
    try:
        job = enqueue_with_metrics(q, "worker.tasks_processing.process_meeting", meeting_id)
        return {"job_id": job.id, "status": job.get_status()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"enqueue failed: {e.__class__.__name__}: {e}")
