# mypy: ignore-errors
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, List

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.jobs.meetings import enqueue_process_meeting
from app.models.meeting import Meeting
from app.models.meeting_notes import MeetingNotes

router = APIRouter(prefix="/v1/meetings", tags=["meetings"])

UPLOAD_DIR = Path("/app/backend/storage/uploads")


def _get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _save_raw_media_stub(
    meeting_id: str,
    file: UploadFile,
    data: bytes,
) -> str:
    """
    Local dev implementation: persist uploaded media on disk so the worker
    can read it later.
    """
    suffix = Path(file.filename or "").suffix or ".mp4"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    out_path = UPLOAD_DIR / f"meeting_{meeting_id}{suffix}"
    out_path.write_bytes(data)
    return str(out_path)


def _render_action_item_md(item: Any) -> str:
    if isinstance(item, str):
        return f"- [ ] {item}"

    if isinstance(item, dict):
        owner = item.get("owner") or "Unassigned"
        task = item.get("task") or ""
        due_date = item.get("due_date") or item.get("due")
        status = item.get("status")
        priority = item.get("priority")

        meta: list[str] = []
        if due_date:
            meta.append(f"due: {due_date}")
        if status:
            meta.append(f"status: {status}")
        if priority:
            meta.append(f"priority: {priority}")

        suffix = f" _({', '.join(meta)})_" if meta else ""
        return f"- [ ] **{owner}** — {task}{suffix}"

    return f"- [ ] {str(item)}"


@router.post("/{meeting_id}/upload")
async def upload_meeting_media(
    meeting_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(_get_db),
) -> dict[str, Any]:
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    raw_bytes = await file.read()
    raw_path = _save_raw_media_stub(str(meeting_id), file, raw_bytes)

    meeting.raw_media_path = raw_path
    meeting.status = "PROCESSING"
    meeting.last_error = None

    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    job = enqueue_process_meeting(meeting_id=meeting_id)

    return {
        "status": "ok",
        "meeting_id": meeting_id,
        "job_id": job.id,
        "raw_media_path": meeting.raw_media_path,
    }


@router.get("/{meeting_id}/notes/ai")
def get_meeting_notes(
    meeting_id: int,
    db: Session = Depends(_get_db),
) -> dict[str, Any]:
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    notes = (
        db.query(MeetingNotes)
        .filter(MeetingNotes.meeting_id == meeting_id)
        .order_by(MeetingNotes.id.desc())
        .first()
    )
    if notes is None:
        raise HTTPException(status_code=404, detail="Notes not found")

    status = getattr(meeting, "status", None) or "UNKNOWN"

    return {
        "meeting_id": meeting_id,
        "status": status,
        "summary": notes.summary,
        "summary_slots": notes.summary_slots or None,
        "key_points": notes.key_points or [],
        "decisions": notes.decisions or [],
        "decision_objects": notes.decision_objects or [],
        "action_items": notes.action_items or [],
        "action_item_objects": notes.action_item_objects or [],
        "model_version": notes.model_version,
    }


def _clean_publishable_markdown_text(text: str) -> str:
    """Apply final lightweight cleanup before markdown export."""
    if not text:
        return text

    cleaned = text

    replacements = {
        "I'd us to": "I'd like us to",
        "I’d us to": "I’d like us to",
    }
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)

    # Remove accidental spaces before punctuation in publishable notes.
    cleaned = re.sub(r"[ \t]+([,.;:!?])", r"\1", cleaned)

    return cleaned


@router.get("/{meeting_id}/notes.md")
def download_meeting_notes_markdown(
    meeting_id: int,
    db: Session = Depends(_get_db),
) -> Response:
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    notes = (
        db.query(MeetingNotes)
        .filter(MeetingNotes.meeting_id == meeting_id)
        .order_by(MeetingNotes.id.desc())
        .first()
    )
    if notes is None:
        raise HTTPException(status_code=404, detail="Notes not found")

    title = getattr(meeting, "title", f"Meeting {meeting_id}")
    summary_slots = notes.summary_slots or {}

    lines: List[str] = []
    lines.append(f"# {title}")
    lines.append("")

    if summary_slots:
        purpose = summary_slots.get("purpose") or ""
        outcome = summary_slots.get("outcome") or ""
        risks = summary_slots.get("risks") or []
        next_steps = summary_slots.get("next_steps") or []

        lines.append("## Purpose")
        lines.append(purpose or "(none)")
        lines.append("")

        lines.append("## Outcome")
        lines.append(outcome or (notes.summary or "(none)"))
        lines.append("")

        lines.append("## Risks")
        if risks:
            for item in risks:
                lines.append(f"- {item}")
        else:
            lines.append("- (none)")
        lines.append("")

        lines.append("## Next Steps")
        if next_steps:
            for item in next_steps:
                lines.append(f"- {item}")
        else:
            lines.append("- (none)")
        lines.append("")
    else:
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

    lines.append("## Decisions")
    decisions = notes.decisions or []
    if decisions:
        for decision in decisions:
            lines.append(f"- {decision}")
    else:
        lines.append("- (none)")
    lines.append("")

    lines.append("## Action Items")
    action_item_objects = notes.action_item_objects or []
    action_items = notes.action_items or []

    if action_item_objects:
        for item in action_item_objects:
            lines.append(_render_action_item_md(item))
    elif action_items:
        for ai in action_items:
            lines.append(f"- [ ] {ai}")
    else:
        lines.append("- (none)")
    lines.append("")

    md = _clean_publishable_markdown_text("\n".join(lines))
    filename = f"meeting_{meeting_id}_notes.md"

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }
    return Response(content=md, media_type="text/markdown", headers=headers)
