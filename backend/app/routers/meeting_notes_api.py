# mypy: ignore-errors
from __future__ import annotations

from typing import Any, List

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.jobs.meetings import enqueue_process_meeting
from app.models.meeting import Meeting
from app.models.meeting_notes import MeetingNotes

router = APIRouter(prefix="/v1/meetings", tags=["meetings"])


def _get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Upload raw media (tests monkeypatch _save_raw_media_stub)
# ---------------------------------------------------------------------------


def _save_raw_media_stub(
    meeting_id: str,
    file: UploadFile,  # noqa: ARG001
    data: bytes,  # noqa: ARG001
) -> str:
    """
    Default stub: tests monkeypatch this to write to tmp_path.
    In prod, replace with real object storage.
    """
    return f"/tmp/mna_meeting_{meeting_id}.mp4"


@router.post("/{meeting_id}/upload")
async def upload_meeting_media(
    meeting_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(_get_db),
) -> dict[str, Any]:
    """
    Upload raw media for a meeting.

    In tests, _save_raw_media_stub is monkeypatched to write to tmp_path.
    In prod, you'll later swap this to real object storage; the RQ job
    is enqueued via enqueue_process_meeting.
    """
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    raw_bytes = await file.read()

    # Save media (tests patch this stub)
    raw_path = _save_raw_media_stub(str(meeting_id), file, raw_bytes)

    # These attrs may or may not exist depending on schema evolution; guard them.
    if hasattr(meeting, "raw_media_path"):
        meeting.raw_media_path = raw_path
    if hasattr(meeting, "status"):
        meeting.status = "PROCESSING"
    if hasattr(meeting, "last_error"):
        meeting.last_error = None

    db.commit()

    # Enqueue background processing via RQ
    job = enqueue_process_meeting(meeting_id=meeting_id)

    # Keep status="ok" for existing tests, but also return job_id
    return {
        "status": "ok",
        "meeting_id": meeting_id,
        "job_id": job.id,
    }


# ---------------------------------------------------------------------------
# AI notes JSON endpoint: /v1/meetings/{id}/notes/ai
# ---------------------------------------------------------------------------


@router.get("/{meeting_id}/notes/ai")
def get_meeting_notes(
    meeting_id: int,
    db: Session = Depends(_get_db),
) -> dict[str, Any]:
    """
    Return the generated AI notes for this meeting as JSON.

    Shape is tailored for the E2E test:
      {
        "meeting_id": <int>,
        "status": "DONE",
        "summary": "...",
        "key_points": [...],
        "action_items": [...],
        "model_version": "..."
      }
    """
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    notes = (
        db.query(MeetingNotes)
        .filter(MeetingNotes.meeting_id == str(meeting_id))
        .order_by(MeetingNotes.id.asc())
        .first()
    )
    if notes is None:
        raise HTTPException(status_code=404, detail="Notes not found")

    status = getattr(meeting, "status", None) or "UNKNOWN"

    return {
        "meeting_id": meeting_id,
        "status": status,
        "summary": notes.summary,
        "key_points": notes.key_points or [],
        "action_items": notes.action_items or [],
        "model_version": notes.model_version,
    }


# ---------------------------------------------------------------------------
# Markdown download: /v1/meetings/{id}/notes.md
# ---------------------------------------------------------------------------


@router.get("/{meeting_id}/notes.md")
def download_meeting_notes_markdown(
    meeting_id: int,
    db: Session = Depends(_get_db),
) -> Response:
    """
    Download the generated notes for a meeting as a Markdown file.
    """
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    notes = (
        db.query(MeetingNotes)
        .filter(MeetingNotes.meeting_id == str(meeting_id))
        .order_by(MeetingNotes.id.asc())
        .first()
    )
    if notes is None:
        raise HTTPException(status_code=404, detail="Notes not found")

    title = getattr(meeting, "title", f"Meeting {meeting_id}")

    lines: List[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append("## Summary")
    lines.append(notes.summary or "")
    lines.append("")
    lines.append("## Key Points")
    key_points = notes.key_points or []
    if key_points:
        for kp in key_points:
            lines.append(f"- {kp}")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Action Items")
    action_items = notes.action_items or []
    if action_items:
        for ai in action_items:
            lines.append(f"- [ ] {ai}")
    else:
        lines.append("- (none)")
    lines.append("")

    md = "\n".join(lines)
    filename = f"meeting_{meeting_id}_notes.md"

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }
    return Response(content=md, media_type="text/markdown", headers=headers)
