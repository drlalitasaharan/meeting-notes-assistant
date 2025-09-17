# app/routers/meetings.py
from typing import Optional, List
from uuid import uuid4
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Form, Request

from pydantic import BaseModel

from app.core.logger import get_logger
from app.core.db import SessionLocal
from packages.shared.models import Meeting, Transcript, Summary, Slide
from packages.shared.minio_client import presign_put, RAW_BUCKET

# Slides bucket utilities for presigned GET + existence checks
# (This is your Phase-1 slides UI support; separate from RAW uploads above)
from app.services import minio_client as slides_minio

log = get_logger(__name__)
router = APIRouter(prefix="/v1", tags=["meetings"])


# --------- Schemas ---------
class MeetingOut(BaseModel):
    id: str
    title: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    slides_attached: bool = False
    transcript_available: bool = False


class ListMeetingsResponse(BaseModel):
    items: List[MeetingOut]
    total: int


def _set_if_has(obj, field: str, value):
    if hasattr(obj, field):
        setattr(obj, field, value)


# --------- Create (start) meeting ---------
@router.post("/meetings/start")
async def start_meeting(request: Request, title: Optional[str] = Form(None)):
    """
    Issues a presigned PUT (to RAW_BUCKET) for the client to upload audio/video.
    Accepts either:
      - form-data: title=<str>
      - JSON: { "title": "..."} or { "name": "..." }
    """
    if title is None:
        try:
            body = await request.json()
            if isinstance(body, dict):
                title = body.get("title") or body.get("name")
        except Exception:
            title = None

    meeting_id = str(uuid4())
    key = f"raw/{meeting_id}.bin"

    try:
        url = presign_put(key, expires=3600, bucket=RAW_BUCKET)
    except Exception as e:
        log.error("Failed to presign upload URL", extra={"err": str(e)})
        raise HTTPException(
            status_code=500,
            detail={"error": "presign_failed", "message": "Could not create upload URL", "details": None},
        )

    with SessionLocal() as db:
        db.add(Meeting(id=meeting_id, title=title, storage_key=key, status="upload_url_issued"))
        db.commit()

    log.info("Issued upload URL", extra={"meeting_id": meeting_id, "key": key, "bucket": RAW_BUCKET})
    return {"meetingId": meeting_id, "uploadUrl": url, "s3Key": key}


# --------- List meetings (DB-backed) ---------
@router.get("/meetings", response_model=ListMeetingsResponse)
def list_meetings(q: Optional[str] = None, limit: int = 50, offset: int = 0):
    """
    Returns meetings enriched with:
      - slides_attached: True if Slide records exist (DB) OR if slides are found in slides bucket
      - transcript_available: True if a Transcript row with non-empty text exists
    """
    with SessionLocal() as db:
        query = db.query(Meeting)
        if q:
            query = query.filter(Meeting.title.ilike(f"%{q}%"))

        # Prefer created_at if your model has it, otherwise id
        try:
            query = query.order_by(Meeting.created_at.desc())  # type: ignore[attr-defined]
        except Exception:
            query = query.order_by(Meeting.id.desc())

        total = query.count()
        items = query.limit(limit).offset(offset).all()

        out: List[MeetingOut] = []
        for m in items:
            # Transcript availability (cheap DB check)
            t = db.query(Transcript).filter_by(meeting_id=m.id).first()
            transcript_available = bool(getattr(t, "text", None)) if t else False

            # Slides indicator: check DB Slide table first; if none, also peek bucket
            slides_in_db = db.query(Slide).filter_by(meeting_id=m.id).limit(1).all()
            slides_attached = len(slides_in_db) > 0
            if not slides_attached:
                # fallback to object storage check (handles cases without Slide rows)
                try:
                    slides_attached = slides_minio.slides_exist(m.id)
                except Exception as e:
                    log.warning("slides_exist check failed", extra={"meeting_id": m.id, "err": str(e)})
                    slides_attached = False

            created_at_val = getattr(m, "created_at", None)
            created_at_iso = created_at_val.isoformat() if isinstance(created_at_val, datetime) else created_at_val

            out.append(
                MeetingOut(
                    id=m.id,
                    title=m.title,
                    status=m.status,
                    created_at=created_at_iso,
                    slides_attached=slides_attached,
                    transcript_available=transcript_available,
                )
            )

        log.info(
            "Listed meetings",
            extra={"count": len(out), "total": total, "q": q, "offset": offset, "limit": limit},
        )
        return ListMeetingsResponse(items=out, total=total)


# --------- Get one meeting (plus transcript/summary/slides) ---------
@router.get("/meetings/{meeting_id}")
def get_meeting(meeting_id: str):
    with SessionLocal() as db:
        m = db.get(Meeting, meeting_id)
        if not m:
            raise HTTPException(
                status_code=404,
                detail={"error": "meeting_not_found", "message": f"Meeting '{meeting_id}' was not found.", "details": None},
            )

        t = db.query(Transcript).filter_by(meeting_id=meeting_id).first()
        s = db.query(Summary).filter_by(meeting_id=meeting_id).first()
        slides = db.query(Slide).filter_by(meeting_id=meeting_id).all()

        log.debug("Fetched meeting", extra={"meeting_id": meeting_id})
        return {
            "meeting": {
                "id": m.id,
                "title": m.title,
                "status": m.status,
                "storage_key": m.storage_key,
            },
            "transcript": (t and {"text": getattr(t, "text", None)}) or None,
            "summary": (
                s
                and {
                    "highlights": getattr(s, "highlights", None),
                    "decisions": getattr(s, "decisions", None),
                    "actions": getattr(s, "actions", None),
                    "risks": getattr(s, "risks", None),
                    "raw": getattr(s, "raw_md", None),
                }
            )
            or None,
            "slides": [{"page": sl.page, "key": sl.storage_key, "ocr_text": sl.ocr_text} for sl in slides] if slides else [],
            "status": m.status,
            "created_at": getattr(m, "created_at", None),
        }


# --------- Process meeting (demo) ---------
@router.post("/meetings/{meeting_id}/process")
def process_meeting(meeting_id: str):
    """
    Demo: mark meeting as processed and upsert transcript/summary.
    Fills common NOT NULL fields for Summary if present (provider/language and JSON lists).
    """
    with SessionLocal() as db:
        m = db.get(Meeting, meeting_id)
        if not m:
            raise HTTPException(
                status_code=404,
                detail={"error": "meeting_not_found", "message": f"Meeting '{meeting_id}' was not found.", "details": None},
            )

        warnings: List[str] = []

        # ---------- Transcript upsert ----------
        try:
            t = db.query(Transcript).filter_by(meeting_id=meeting_id).first()
            if not t:
                kwargs = {"meeting_id": meeting_id}
                if hasattr(Transcript, "id"):
                    kwargs["id"] = str(uuid4())
                _t = Transcript(**kwargs)
                _set_if_has(_t, "provider", "demo")
                _set_if_has(_t, "language", "en")
                _set_if_has(_t, "text", "(demo) transcript goes here")
                db.add(_t)
            else:
                if getattr(t, "provider", None) in (None, ""):
                    _set_if_has(t, "provider", "demo")
                if getattr(t, "language", None) in (None, ""):
                    _set_if_has(t, "language", "en")
                _set_if_has(t, "text", "(demo) transcript goes here")
            db.flush()
        except Exception as e:
            db.rollback()
            warnings.append(f"transcript_upsert_failed: {e.__class__.__name__}")
            log.warning("Transcript upsert failed", exc_info=True, extra={"meeting_id": meeting_id})

        # ---------- Summary upsert (safe defaults for NOT NULLs) ----------
        try:
            demo_md = "## (demo) summary\n\n- highlight 1\n- highlight 2\n- decision A\n- action X\n- risk R"
            s = db.query(Summary).filter_by(meeting_id=meeting_id).first()

            if not s:
                kwargs = {"meeting_id": meeting_id}
                if hasattr(Summary, "id"):
                    kwargs["id"] = str(uuid4())
                if hasattr(Summary, "provider"):
                    kwargs["provider"] = "demo"
                if hasattr(Summary, "language"):
                    kwargs["language"] = "en"
                # JSON-ish fields commonly NOT NULL in schemas
                if hasattr(Summary, "highlights"):
                    kwargs["highlights"] = []
                if hasattr(Summary, "decisions"):
                    kwargs["decisions"] = []
                if hasattr(Summary, "actions"):
                    kwargs["actions"] = []
                if hasattr(Summary, "risks"):
                    kwargs["risks"] = []

                s = Summary(**kwargs)
                db.add(s)

            # Always set/update markdown body if present
            _set_if_has(s, "raw_md", demo_md)
            db.flush()
        except Exception as e:
            db.rollback()
            warnings.append(f"summary_upsert_failed: {e.__class__.__name__}")
            log.warning("Summary upsert failed", exc_info=True, extra={"meeting_id": meeting_id})

        # ---------- Commit status ----------
        try:
            m.status = "processed"
            db.commit()
        except Exception:
            db.rollback()
            log.exception("Commit failed after updates", extra={"meeting_id": meeting_id})
            raise HTTPException(
                status_code=500,
                detail={"error": "processing_failed", "message": "Failed to save meeting updates.", "details": None},
            )

        resp = {"ok": True, "meetingId": meeting_id, "status": "processed"}
        if warnings:
            resp["warnings"] = warnings
        log.info("Processed meeting", extra={"meeting_id": meeting_id, "warnings": warnings or "none"})
        return resp


# --------- Slides: presigned download for first slide (Phase-1 helper) ---------
@router.get("/meetings/{meeting_id}/download/slides")
def download_first_slide(meeting_id: str):
    """
    Convenience endpoint for Phase-1 UI:
    Returns a presigned GET URL for the *first* slide found for the meeting.
    If you manage multiple slide files per meeting, switch to a filename-aware
    endpoint later or use app/routers/slides.py for richer operations.
    """
    # Prefer bucket check (handles objects even if Slide rows are missing)
    try:
        url = slides_minio.presigned_first_slide_get(meeting_id, expiry_seconds=3600)
        if not url:
            raise HTTPException(status_code=404, detail="No slides attached")
        return {"url": url, "expires_in": 3600}
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Failed to create slides presigned URL", extra={"meeting_id": meeting_id, "err": str(e)})
        raise HTTPException(
            status_code=500,
            detail={"error": "presign_failed", "message": "Could not create slides download URL", "details": None},
        )

