from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.meeting import Meeting

PROCESSING_LABELS = {
    "uploaded": "Upload received",
    "validating_media": "Checking the recording",
    "processing_audio": "Preparing audio",
    "transcribing": "Transcribing audio",
    "generating_notes": "Generating notes",
    "finalizing": "Finalizing notes",
    "completed": "Notes ready",
    "failed": "Processing failed",
}

TIMING_KEYS = {
    "upload_received_at",
    "media_validation_started_at",
    "media_validation_completed_at",
    "audio_conversion_started_at",
    "audio_conversion_completed_at",
    "transcription_started_at",
    "transcription_completed_at",
    "notes_generation_started_at",
    "notes_generation_completed_at",
    "processing_completed_at",
    "processing_failed_at",
}

GENERIC_PROCESSING_ERROR = (
    "We could not process this recording. Please check the file format and try again."
)
TIMEOUT_PROCESSING_ERROR = (
    "Processing took longer than expected. Please try again or contact support."
)
TRANSCRIPTION_PROCESSING_ERROR = "Transcription failed. Please try a shorter or clearer recording."


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return utc_now().isoformat()


def progress_label(stage: str | None) -> str:
    return PROCESSING_LABELS.get((stage or "").strip().lower(), "Processing")


def _timings(meeting: Meeting) -> dict[str, Any]:
    existing = getattr(meeting, "processing_timings", None)
    return dict(existing) if isinstance(existing, dict) else {}


def mark_stage(
    meeting: Meeting,
    stage: str,
    *,
    status: str | None = None,
    started_key: str | None = None,
    completed_key: str | None = None,
    clear_error: bool = False,
) -> Meeting:
    """Update processing metadata without assuming a fresh ORM instance.

    The function is idempotent: repeated calls set the same stage and only
    fill timing keys that are absent, so retries keep their first boundary
    timestamp while still moving the current stage forward.
    """

    normalized_stage = stage.strip().lower()
    meeting.processing_stage = normalized_stage

    if status is not None:
        meeting.status = status

    if clear_error:
        meeting.last_error = None
        meeting.processing_error_code = None
        meeting.processing_error_message = None
        meeting.processing_diagnostics = None

    timings = _timings(meeting)
    for key in (started_key, completed_key):
        if key and key in TIMING_KEYS and not timings.get(key):
            timings[key] = _iso_now()
    meeting.processing_timings = timings
    return meeting


def begin_attempt(meeting: Meeting) -> Meeting:
    meeting.processing_attempts = int(getattr(meeting, "processing_attempts", 0) or 0) + 1
    return mark_stage(
        meeting,
        "validating_media",
        status="PROCESSING",
        started_key="media_validation_started_at",
        clear_error=True,
    )


def mark_uploaded(meeting: Meeting) -> Meeting:
    return mark_stage(
        meeting,
        "uploaded",
        status="PROCESSING",
        started_key="upload_received_at",
        completed_key="media_validation_completed_at",
        clear_error=True,
    )


def mark_completed(meeting: Meeting) -> Meeting:
    return mark_stage(
        meeting,
        "completed",
        status="DONE",
        completed_key="processing_completed_at",
        clear_error=True,
    )


def safe_error_for_exception(exc: BaseException, stage: str | None = None) -> tuple[str, str]:
    text = str(exc).lower()
    normalized_stage = (stage or "").lower()

    if "timeout" in text or "timed out" in text or "job timeout" in text:
        return "processing_timeout", TIMEOUT_PROCESSING_ERROR

    if normalized_stage == "transcribing" or "transcrib" in text:
        return "transcription_failed", TRANSCRIPTION_PROCESSING_ERROR

    return "processing_failed", GENERIC_PROCESSING_ERROR


def sanitize_diagnostic(exc: BaseException) -> str:
    diagnostic = f"{exc.__class__.__name__}: {str(exc)}"
    diagnostic = re.sub(
        r"(?i)(api[_-]?key|token|secret|password)=\S+", r"\1=[redacted]", diagnostic
    )
    diagnostic = re.sub(r"(?i)bearer\s+[a-z0-9._~+/=-]+", "Bearer [redacted]", diagnostic)
    diagnostic = re.sub(r"/(?:Users|private|tmp|var|opt|home)/[^\s,;:]+", "[path]", diagnostic)
    diagnostic = re.sub(r"[A-Za-z]:\\[^\s,;:]+", "[path]", diagnostic)
    return diagnostic[:1000]


def mark_failed(
    meeting: Meeting,
    exc: BaseException,
    *,
    stage: str | None = None,
) -> Meeting:
    error_code, safe_message = safe_error_for_exception(exc, stage)
    mark_stage(
        meeting,
        "failed",
        status="ERROR",
        completed_key="processing_failed_at",
    )
    meeting.last_error = safe_message[:250]
    meeting.processing_error_code = error_code
    meeting.processing_error_message = safe_message
    meeting.processing_diagnostics = sanitize_diagnostic(exc)
    return meeting


def serialize_progress(meeting: Meeting) -> dict[str, Any]:
    stage = getattr(meeting, "processing_stage", None)
    return {
        "processing_stage": stage,
        "processing_progress_label": progress_label(stage),
        "processing_error_message": getattr(meeting, "processing_error_message", None),
    }


def serialize_admin_processing(meeting: Meeting) -> dict[str, Any]:
    timings = _timings(meeting)
    started = timings.get("upload_received_at") or timings.get("media_validation_started_at")
    finished = timings.get("processing_completed_at") or timings.get("processing_failed_at")
    return {
        **serialize_progress(meeting),
        "processing_error_code": getattr(meeting, "processing_error_code", None),
        "processing_diagnostics": getattr(meeting, "processing_diagnostics", None),
        "processing_attempts": int(getattr(meeting, "processing_attempts", 0) or 0),
        "processing_timings": timings,
        "processing_started_at": started,
        "processing_finished_at": finished,
        "processing_total_seconds": _total_seconds(started, finished),
    }


def _total_seconds(started: Any, finished: Any) -> float | None:
    if not isinstance(started, str) or not isinstance(finished, str):
        return None
    try:
        start_dt = datetime.fromisoformat(started)
        finish_dt = datetime.fromisoformat(finished)
    except ValueError:
        return None
    return round((finish_dt - start_dt).total_seconds(), 3)


def commit_stage(db: Session, meeting: Meeting, stage: str, **kwargs: Any) -> Meeting:
    mark_stage(meeting, stage, **kwargs)
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting
