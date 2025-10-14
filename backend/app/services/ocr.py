# backend/app/routers/meetings.py
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from rq.job import Job
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.jobs.pipeline import process_meeting
from app.jobs.queue import get_queue, get_redis
from packages.shared.models import Meeting, Summary, Transcript  # ensure these exist per migration

from ..deps import get_db

log = get_logger(__name__)

# NOTE: Keep routers version-agnostic; mount under /v1 in main.py.
router = APIRouter(
    prefix="/meetings",
    tags=["meetings"],
)


def _tags_list(value: str | List[str] | None) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [t for t in (value or "").split(",") if t]


# ---------- Models for responses ----------
class EnqueueResponse(BaseModel):
    job_id: str
    meeting_id: int
    status: str


class NoteItem(BaseModel):
    text: str
    created_at: str  # ISO 8601


class NotesResponse(BaseModel):
    meeting_id: int
    transcript: Optional[NoteItem] = None
    summary: Optional[NoteItem] = None


# ---------- Listing / CRUD ----------
@router.get("", response_model=dict)
def list_meetings(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    query: str | None = Query(None, description="Simple search over title/tags"),
    db: Session = Depends(get_db),
) -> dict:
    q = db.query(Meeting)

    # Simple search on title/tags if provided (case-insensitive)
    if query:
        like = f"%{query}%"
        q = q.filter(or_(Meeting.title.ilike(like), Meeting.tags.ilike(like)))

    q = q.order_by(Meeting.id.desc())
    rows = q.offset((page - 1) * limit).limit(limit).all()

    items = [
        {
            "id": m.id,
            "title": m.title,
            "tags": _tags_list(m.tags),
            "status": getattr(m, "status", None),
        }
        for m in rows
    ]

    # Tests expect: r.json()["items"]
    return {"items": items}


@router.post("", status_code=status.HTTP_200_OK)
def create_meeting(
    title: str = Query(...),
    tags: str | None = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    m = Meeting(title=title, tags=tags or "")
    db.add(m)
    db.commit()
    db.refresh(m)
    log.info("Created meeting", extra={"meeting_id": m.id})
    return {
        "id": m.id,
        "title": m.title,
        "tags": _tags_list(m.tags),
        "status": getattr(m, "status", None),
    }


@router.get("/{meeting_id}")
def get_meeting(meeting_id: int, db: Session = Depends(get_db)) -> dict:
    m = db.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {
        "id": m.id,
        "title": m.title,
        "tags": _tags_list(m.tags),
        "status": getattr(m, "status", None),
    }


@router.patch("/{meeting_id}")
def update_meeting(
    meeting_id: int,
    *,
    title: str | None = None,
    status: str | None = None,
    tags: str | None = None,  # comma-separated string
    db: Session = Depends(get_db),
) -> dict:
    m = db.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if title is not None:
        m.title = title
    if status is not None:
        m.status = status
    if tags is not None:
        m.tags = tags

    db.add(m)
    db.commit()
    db.refresh(m)

    log.info("Patched meeting", extra={"meeting_id": m.id})
    return {
        "id": m.id,
        "title": m.title,
        "tags": _tags_list(m.tags),
        "status": getattr(m, "status", None),
    }


# ---------- Async processing via RQ ----------
@router.post("/{meeting_id}/process", response_model=EnqueueResponse)
def process_meeting_enqueue(
    meeting_id: int,
    db: Session = Depends(get_db),
) -> EnqueueResponse:
    # Validate meeting exists
    m = db.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")

    q = get_queue()
    job = q.enqueue(process_meeting, meeting_id)
    log.info(
        "Enqueued meeting processing job",
        extra={"meeting_id": meeting_id, "job_id": job.id},
    )
    return EnqueueResponse(job_id=job.id, meeting_id=meeting_id, status=job.get_status())


@router.get("/jobs/{job_id}")
def job_status(job_id: str) -> dict:
    try:
        job = Job.fetch(job_id, connection=get_redis())
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job_id,
        "status": job.get_status(),
        "result": job.result,
    }


# ---------- Notes (Transcript + Summary) ----------
@router.get("/{meeting_id}/notes", response_model=NotesResponse)
def get_notes(
    meeting_id: int,
    db: Session = Depends(get_db),
) -> NotesResponse:
    # 404 if meeting doesn't exist
    m = db.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Latest transcript & summary
    t = (
        db.query(Transcript)
        .filter(Transcript.meeting_id == meeting_id)
        .order_by(desc(Transcript.created_at))
        .first()
    )
    s = (
        db.query(Summary)
        .filter(Summary.meeting_id == meeting_id)
        .order_by(desc(Summary.created_at))
        .first()
    )

    return NotesResponse(
        meeting_id=meeting_id,
        transcript=(NoteItem(text=t.text, created_at=t.created_at.isoformat()) if t else None),
        summary=(NoteItem(text=s.text, created_at=s.created_at.isoformat()) if s else None),
    )
