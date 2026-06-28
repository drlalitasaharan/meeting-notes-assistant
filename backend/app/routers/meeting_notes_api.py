# mypy: ignore-errors
from __future__ import annotations

import ast
import os
import re
from pathlib import Path
from typing import Any, List, Literal

import boto3
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.deps import get_current_user
from app.jobs.meetings import enqueue_process_meeting
from app.models.meeting import Meeting
from app.models.meeting_notes import MeetingNotes
from app.models.user import User
from app.services.media_metadata import probe_media_duration_seconds
from app.services.processing_observability import mark_stage, mark_uploaded, serialize_progress
from app.services.usage_limits import (
    enforce_free_trial_duration_limit,
    enforce_free_trial_upload_limit,
    record_upload_ledger_entry,
)

router = APIRouter(prefix="/v1/meetings", tags=["meetings"])


class MeetingNotesSectionUpdate(BaseModel):
    section: Literal["summary", "key_points", "action_items"]
    value: str | list[str]


UPLOAD_DIR = Path("/app/backend/storage/uploads")
SUPPORTED_EXTENSIONS = {
    ".flac",
    ".m4a",
    ".mp3",
    ".mp4",
    ".wav",
    ".webm",
    ".ogg",
    ".oga",
    ".mpeg",
    ".mpga",
}
MAX_UPLOAD_BYTES = 24 * 1024 * 1024


def _get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _s3_bucket() -> str | None:
    return (
        os.getenv("S3_BUCKET")
        or os.getenv("AWS_S3_BUCKET")
        or os.getenv("S3_BUCKET_NAME")
        or os.getenv("OBJECT_BUCKET")
    )


def _s3_region() -> str | None:
    return os.getenv("S3_REGION") or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")


def _s3_client():
    kwargs: dict[str, Any] = {}

    region = _s3_region()
    if region:
        kwargs["region_name"] = region

    endpoint = os.getenv("S3_ENDPOINT") or os.getenv("AWS_ENDPOINT_URL")
    if endpoint:
        kwargs["endpoint_url"] = endpoint

    access_key = os.getenv("S3_ACCESS_KEY") or os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("S3_SECRET_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY")
    if access_key and secret_key:
        kwargs["aws_access_key_id"] = access_key
        kwargs["aws_secret_access_key"] = secret_key

    return boto3.client("s3", **kwargs)


def _use_s3_storage() -> bool:
    return os.getenv("STORAGE_BACKEND", "").lower() == "s3" and bool(_s3_bucket())


def _save_raw_media(
    meeting_id: str,
    file: UploadFile,
    data: bytes,
) -> str:
    """
    Persist uploaded media.

    In production, store the media in S3 so both the web service and worker
    can access the same object. In local development, fall back to disk.
    """
    suffix = Path(file.filename or "").suffix or ".mp4"

    if _use_s3_storage():
        bucket = _s3_bucket()
        if not bucket:
            raise RuntimeError("S3 storage requested but no S3 bucket is configured")

        key = f"raw_media/meeting_{meeting_id}{suffix}"
        _s3_client().put_object(
            Bucket=bucket,
            Key=key,
            Body=data,
            ContentType=file.content_type or "application/octet-stream",
        )
        return f"s3://{bucket}/{key}"

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    out_path = UPLOAD_DIR / f"meeting_{meeting_id}{suffix}"
    out_path.write_bytes(data)
    return str(out_path)


def _render_action_item_md(item: Any) -> str:
    if isinstance(item, str):
        stripped = item.strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            try:
                parsed = ast.literal_eval(stripped)
            except (SyntaxError, ValueError):
                parsed = None
            if isinstance(parsed, dict):
                return _render_action_item_md(parsed)
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
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    meeting = db.get(Meeting, meeting_id)
    if meeting is None or meeting.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Meeting not found")

    enforce_free_trial_upload_limit(
        db=db,
        current_user=current_user,
        meeting=meeting,
    )

    raw_bytes = await file.read()
    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail="This file is too large for hosted transcription. Please upload a file under 24 MB or use compressed m4a/mp3.",
        )

    extension = Path(file.filename or "").suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload MP3, MP4, M4A, WAV, WEBM, OGG, or FLAC.",
        )

    mark_stage(
        meeting,
        "validating_media",
        status="PROCESSING",
        started_key="upload_received_at",
        clear_error=True,
    )

    media_duration_seconds = probe_media_duration_seconds(
        raw_bytes,
        suffix=extension or ".bin",
    )
    enforce_free_trial_duration_limit(
        db=db,
        current_user=current_user,
        duration_seconds=media_duration_seconds,
    )

    try:
        raw_path = _save_raw_media(str(meeting_id), file, raw_bytes)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="We couldn't process this file. Please try a shorter recording or upload a supported audio/video format.",
        )

    record_upload_ledger_entry(
        db=db,
        current_user=current_user,
        meeting=meeting,
        original_filename=file.filename,
        file_size_bytes=len(raw_bytes),
        content_type=file.content_type,
        storage_key=raw_path,
    )

    meeting.raw_media_path = raw_path
    meeting.media_duration_seconds = media_duration_seconds
    meeting.media_size_bytes = len(raw_bytes)
    meeting.media_content_type = file.content_type
    meeting.media_filename = file.filename
    mark_uploaded(meeting)

    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    job = enqueue_process_meeting(meeting_id=meeting_id)

    return {
        "status": "ok",
        "meeting_id": meeting_id,
        "job_id": job.id,
        "raw_media_path": meeting.raw_media_path,
        "media_duration_seconds": meeting.media_duration_seconds,
        "media_size_bytes": meeting.media_size_bytes,
        **serialize_progress(meeting),
    }


def _clean_client_facing_json_text(value: Any) -> str:
    cleaned = str(value or "")

    replacements = {
        "I'd us to": "I'd like us to",
        "I’d us to": "I’d like us to",
        "reviewrecommended": "review recommended",
        "tomake": "to make",
        "a gen.ai": "Acjen AI",
    }
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)

    cleaned = re.sub(r"[ \t]+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _clean_client_facing_json_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []

    cleaned_values: list[str] = []
    seen: set[str] = set()

    for item in values:
        cleaned = _clean_client_facing_json_text(item).strip(" .")
        if not cleaned:
            continue

        key = cleaned.lower()
        if key in seen:
            continue

        seen.add(key)
        cleaned_values.append(cleaned)

    return cleaned_values


def _clean_client_facing_json_slots(summary_slots: Any) -> dict[str, Any] | None:
    if not isinstance(summary_slots, dict):
        return None

    cleaned_slots = dict(summary_slots)

    for key in ("purpose", "outcome"):
        value = cleaned_slots.get(key)
        if isinstance(value, str):
            cleaned_slots[key] = _clean_client_facing_json_text(value)

    for key in ("risks", "next_steps"):
        values = cleaned_slots.get(key)
        if isinstance(values, list):
            cleaned_slots[key] = [
                _clean_client_facing_json_text(item)
                for item in values
                if _clean_client_facing_json_text(item)
            ]

    return cleaned_slots


def _client_facing_summary_from_slots(
    summary: Any,
    summary_slots: dict[str, Any] | None,
) -> str | None:
    cleaned_summary = _clean_client_facing_json_text(summary)

    if isinstance(summary_slots, dict):
        edited_summary = _clean_client_facing_json_text(summary_slots.get("edited_summary"))
        if edited_summary:
            return edited_summary

        purpose = _clean_client_facing_json_text(summary_slots.get("purpose"))
        outcome = _clean_client_facing_json_text(summary_slots.get("outcome"))

        parts = [part.strip(" .") for part in (purpose, outcome) if part.strip()]
        if parts:
            rebuilt = ". ".join(dict.fromkeys(parts))
            return _clean_client_facing_json_text(rebuilt)

    return cleaned_summary or None


PUBLISHABLE_ACTION_VERBS = (
    "add",
    "assign",
    "call",
    "check",
    "circulate",
    "complete",
    "confirm",
    "contact",
    "create",
    "deliver",
    "deploy",
    "document",
    "draft",
    "email",
    "finish",
    "finalize",
    "fix",
    "follow up",
    "keep",
    "package",
    "prepare",
    "publish",
    "redeploy",
    "review",
    "run",
    "save",
    "schedule",
    "send",
    "share",
    "test",
    "update",
    "upload",
    "validate",
    "verify",
    "write",
)

PUBLISHABLE_ACTION_VERB_PATTERN = "|".join(re.escape(verb) for verb in PUBLISHABLE_ACTION_VERBS)


def _is_v3_generated_notes(notes: MeetingNotes) -> bool:
    return "v3" in str(getattr(notes, "model_version", "") or "").lower()


def _clean_publishable_action_task(value: Any) -> str:
    text = str(value or "").strip()
    text = re.sub(r"^\s*[-*]?\s*\[[ xX]\]\s*", "", text)
    text = re.sub(r"\s+_?\(status:.*$", "", text, flags=re.I).strip()
    text = text.strip(" -–—")
    return _clean_publishable_markdown_text(text)


def _split_publishable_action_item(value: Any) -> tuple[str, str]:
    text = _clean_publishable_action_task(value)

    owner_match = re.match(
        r"^(?P<owner>[A-Z][A-Za-z .'-]{1,60})\s*(?:—|-|:)\s*(?P<task>.+)$",
        text,
    )
    if owner_match:
        return owner_match.group("owner").strip(), _clean_publishable_action_task(
            owner_match.group("task")
        )

    return "Team", text


def _looks_like_publishable_context_not_action(task: str) -> bool:
    cleaned = _clean_publishable_action_task(task)
    lowered = cleaned.lower()

    if not lowered:
        return True

    if lowered.startswith(
        (
            "i'd like us to",
            "i’d like us to",
            "i'd us to",
            "i’d us to",
            "i would like us to",
            "we'd like to",
            "we would like to",
            "the main purpose",
            "the purpose",
            "today's purpose",
            "the team aligned",
            "team aligned",
            "if we say",
            "if we position",
            "that's ",
            "that is ",
            "this week's priority is",
            "this weeks priority is",
            "the priority is",
            "the first pilot audience",
            "the live demo will use",
            "the demo will use",
            "a short demo video",
            "a simple landing page",
            "even if you already know",
            "sixth,",
        )
    ):
        return True

    if re.search(
        r"\b(clear decision on the target audience|main purpose of today|"
        r"designed for consultants|team aligned on|finalized plan for the demo flow|"
        r"concrete owners for the follow-up|this week'?s priority is|"
        r"would be enough to start|makes the demo feel|will use a short and clean file)\b",
        lowered,
    ):
        return True

    if lowered.startswith(("we can ", "we need to ", "we should ", "we will ")):
        return True

    if re.match(r"^(?:the|this|that|it|there)\b", lowered) and re.search(
        r"\b(will be|will use|will remain|will include|is to|is|are|aligned|designed)\b",
        lowered,
    ):
        return True

    return False


def _is_publishable_action_task(task: str) -> bool:
    cleaned = _clean_publishable_action_task(task)
    lowered = cleaned.lower()

    if _looks_like_publishable_context_not_action(cleaned):
        return False

    if re.match(rf"^(?:also\s+)?(?:please\s+)?(?:{PUBLISHABLE_ACTION_VERB_PATTERN})\b", lowered):
        return True

    if re.match(
        rf"^(?:i\s+will|i'll)\s+(?:{PUBLISHABLE_ACTION_VERB_PATTERN})\b",
        lowered,
    ):
        return True

    if re.match(
        rf"^[a-z][a-z .'-]{{1,50}}\s+"
        rf"(?:will|should|needs to|need to|must|has to)\s+"
        rf"(?:{PUBLISHABLE_ACTION_VERB_PATTERN})\b",
        lowered,
    ):
        return True

    return False


def _publishable_action_payload(
    notes: MeetingNotes,
    summary_slots: dict[str, Any],
) -> dict[str, Any]:
    """Final user-visible action guardrail for frontend and Markdown output."""

    if not _is_v3_generated_notes(notes):
        return {
            "summary_slots": summary_slots,
            "action_items": notes.action_items or [],
            "action_item_objects": notes.action_item_objects or [],
        }

    action_objects: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in notes.action_item_objects or []:
        if not isinstance(item, dict):
            continue

        owner = str(item.get("owner") or "Team").strip() or "Team"
        task = _clean_publishable_action_task(
            item.get("task") or item.get("action") or item.get("text") or ""
        )
        if not _is_publishable_action_task(task):
            continue

        key = re.sub(r"\W+", " ", task.lower()).strip()
        if not key or key in seen:
            continue

        seen.add(key)
        action_objects.append(
            {
                **item,
                "owner": owner,
                "task": task,
                "text": f"{owner}: {task}",
                "status": item.get("status") or "open",
                "priority": item.get("priority") or "medium",
            }
        )

    for item in notes.action_items or []:
        owner, task = _split_publishable_action_item(item)
        if not _is_publishable_action_task(task):
            continue

        key = re.sub(r"\W+", " ", task.lower()).strip()
        if not key or key in seen:
            continue

        seen.add(key)
        action_objects.append(
            {
                "owner": owner,
                "task": task,
                "text": f"{owner}: {task}",
                "status": "open",
                "priority": "medium",
            }
        )

    action_items = [
        f"{item.get('owner') or 'Team'} — {item.get('task')}"
        for item in action_objects
        if str(item.get("task") or "").strip()
    ]

    publishable_slots = dict(summary_slots or {})
    publishable_slots["next_steps"] = [
        str(item.get("task") or "").rstrip(".") + "."
        for item in action_objects[:5]
        if str(item.get("task") or "").strip()
    ]

    return {
        "summary_slots": publishable_slots,
        "action_items": action_items,
        "action_item_objects": action_objects,
    }


def _qev3d_key_points_publishable_enabled() -> bool:
    return str(os.getenv("MEETIQ_QEV3D_SECTION_SEPARATION", "")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _publishable_key_point_text_key(text: str) -> str:
    return re.sub(r"\W+", " ", _clean_client_facing_json_text(text).lower()).strip()


def _publishable_key_point_item_text(item: Any) -> str:
    if isinstance(item, dict):
        return _clean_client_facing_json_text(
            item.get("text")
            or item.get("summary")
            or item.get("point")
            or item.get("description")
            or ""
        )
    return _clean_client_facing_json_text(item)


def _publishable_key_point_overlaps_text(text: str, other: Any) -> bool:
    text_key = _publishable_key_point_text_key(text)
    other_key = _publishable_key_point_text_key(str(other or ""))

    if not text_key or not other_key:
        return False

    if text_key == other_key:
        return True

    if len(text_key) >= 24 and len(other_key) >= 24:
        return text_key in other_key or other_key in text_key

    return False


def _publishable_key_point_overlaps_items(text: str, items: Any) -> bool:
    if not isinstance(items, list):
        return False

    return any(
        _publishable_key_point_overlaps_text(text, _publishable_key_point_item_text(item))
        for item in items
    )


def _normalize_publishable_key_point(text: str) -> str:
    cleaned = _clean_client_facing_json_text(text)
    lowered = cleaned.lower()

    if "preserve that processed meeting as the backup demo asset" in lowered:
        return "Preserve one processed meeting as a backup demo asset before the live demo."

    return cleaned


def _looks_like_key_point_section_overlap(
    text: str,
    *,
    summary_slots: dict[str, Any],
    decisions: Any,
    actions: dict[str, Any],
) -> bool:
    cleaned = _clean_client_facing_json_text(text)
    lowered = cleaned.lower()

    if not cleaned:
        return True

    if lowered.startswith(
        (
            "i'd like us to",
            "i’d like us to",
            "i would like us to",
            "we'd like to",
            "we would like to",
            "the main purpose",
            "the purpose",
            "today's purpose",
            "the team aligned",
            "team aligned",
            "if we say",
            "if we position",
            "the first pilot audience",
            "the live demo will use",
            "the demo will use",
            "this week's priority is",
            "this weeks priority is",
            "the priority is",
        )
    ):
        return True

    if re.search(
        r"\b(clear decision on the target audience|main purpose of today|"
        r"designed for consultants|team aligned on|finalized plan for the demo flow|"
        r"concrete owners for the follow-up|this week'?s priority is|"
        r"will use a short and clean file)\b",
        lowered,
    ):
        return True

    if _publishable_key_point_overlaps_text(cleaned, summary_slots.get("purpose") or ""):
        return True

    if _publishable_key_point_overlaps_text(cleaned, summary_slots.get("outcome") or ""):
        return True

    if _publishable_key_point_overlaps_items(cleaned, decisions):
        return True

    if _publishable_key_point_overlaps_items(cleaned, actions.get("action_item_objects")):
        return True

    if _publishable_key_point_overlaps_items(cleaned, actions.get("action_items")):
        return True

    return False


def _publishable_key_points_payload(
    notes: MeetingNotes,
    summary_slots: dict[str, Any],
    publishable_actions: dict[str, Any],
    *,
    limit: int = 6,
) -> list[str]:
    """Final user-visible Key Points guardrail for frontend and Markdown output."""

    raw_key_points = _clean_client_facing_json_list(notes.key_points)

    if not _is_v3_generated_notes(notes) or not _qev3d_key_points_publishable_enabled():
        return raw_key_points

    output: list[str] = []
    seen: set[str] = set()

    decisions = []
    if isinstance(notes.decision_objects, list) and notes.decision_objects:
        decisions = notes.decision_objects
    elif isinstance(notes.decisions, list):
        decisions = notes.decisions

    for item in raw_key_points:
        candidate = _normalize_publishable_key_point(item)
        if not candidate:
            continue

        if _looks_like_key_point_section_overlap(
            candidate,
            summary_slots=summary_slots or {},
            decisions=decisions,
            actions=publishable_actions,
        ):
            continue

        key = _publishable_key_point_text_key(candidate)
        if not key or key in seen:
            continue

        seen.add(key)
        output.append(candidate)

        if len(output) >= limit:
            break

    return output


@router.get("/{meeting_id}/notes/ai")
def get_meeting_notes(
    meeting_id: int,
    db: Session = Depends(_get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    meeting = db.get(Meeting, meeting_id)
    if meeting is None or meeting.user_id != current_user.id:
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
    summary_slots = _clean_client_facing_json_slots(notes.summary_slots)
    publishable_actions = _publishable_action_payload(notes, summary_slots)
    summary_slots = publishable_actions["summary_slots"]
    publishable_key_points = _publishable_key_points_payload(
        notes,
        summary_slots,
        publishable_actions,
    )

    return {
        "meeting_id": meeting_id,
        "status": status,
        **serialize_progress(meeting),
        "summary": _client_facing_summary_from_slots(notes.summary, summary_slots),
        "summary_slots": summary_slots,
        "key_points": publishable_key_points,
        "decisions": notes.decisions or [],
        "decision_objects": notes.decision_objects or [],
        "action_items": publishable_actions["action_items"],
        "action_item_objects": publishable_actions["action_item_objects"],
        "model_version": notes.model_version,
    }


@router.patch("/{meeting_id}/notes/ai")
def update_meeting_notes_section(
    meeting_id: int,
    payload: MeetingNotesSectionUpdate,
    db: Session = Depends(_get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    meeting = db.get(Meeting, meeting_id)
    if meeting is None or meeting.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Meeting not found")

    notes = (
        db.query(MeetingNotes)
        .filter(MeetingNotes.meeting_id == meeting_id)
        .order_by(MeetingNotes.id.desc())
        .first()
    )
    if notes is None:
        raise HTTPException(status_code=404, detail="Notes not found")

    if payload.section == "summary":
        if not isinstance(payload.value, str):
            raise HTTPException(
                status_code=422,
                detail="Summary must be text",
            )

        summary = payload.value.strip()
        if not summary:
            raise HTTPException(
                status_code=422,
                detail="Summary cannot be empty",
            )

        notes.summary = summary

        # Preserve the generated Purpose and Outcome. Store the user's
        # revised Summary separately in the existing JSON field.
        summary_slots = dict(notes.summary_slots) if isinstance(notes.summary_slots, dict) else {}
        summary_slots["edited_summary"] = summary
        notes.summary_slots = summary_slots

    elif payload.section == "key_points":
        if not isinstance(payload.value, list):
            raise HTTPException(
                status_code=422,
                detail="Key points must be a list",
            )

        notes.key_points = [
            item.strip() for item in payload.value if isinstance(item, str) and item.strip()
        ]

    elif payload.section == "action_items":
        if not isinstance(payload.value, list):
            raise HTTPException(
                status_code=422,
                detail="Action items must be a list",
            )

        notes.action_items = [
            item.strip() for item in payload.value if isinstance(item, str) and item.strip()
        ]

        # Markdown prefers action_item_objects when present. Clear the old
        # generated objects so edited action_items become the source of truth.
        notes.action_item_objects = []

    db.add(notes)
    db.commit()
    db.refresh(notes)

    return get_meeting_notes(
        meeting_id=meeting_id,
        db=db,
        current_user=current_user,
    )


def _clean_publishable_markdown_text(text: str) -> str:
    """Apply final lightweight cleanup before markdown export."""
    if not text:
        return text

    cleaned = text

    replacements = {
        "I'd us to": "I'd like us to",
        "I’d us to": "I’d like us to",
        "reviewrecommended": "review recommended",
        "tomake": "to make",
        "a gen.ai": "Acjen AI",
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
    current_user: User = Depends(get_current_user),
) -> Response:
    meeting = db.get(Meeting, meeting_id)
    if meeting is None or meeting.user_id != current_user.id:
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
    publishable_actions = _publishable_action_payload(notes, notes.summary_slots or {})
    summary_slots = publishable_actions["summary_slots"]
    publishable_key_points = _publishable_key_points_payload(
        notes,
        summary_slots,
        publishable_actions,
    )

    lines: List[str] = []
    lines.append(f"# {title}")
    lines.append("")

    if summary_slots:
        edited_summary = _clean_client_facing_json_text(summary_slots.get("edited_summary"))
        purpose = summary_slots.get("purpose") or ""
        outcome = summary_slots.get("outcome") or ""
        risks = summary_slots.get("risks") or []
        next_steps = summary_slots.get("next_steps") or []

        if edited_summary:
            lines.append("## Summary")
            lines.append(edited_summary)
            lines.append("")

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
    key_points = publishable_key_points
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
    action_item_objects = publishable_actions["action_item_objects"]
    action_items = publishable_actions["action_items"]

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
