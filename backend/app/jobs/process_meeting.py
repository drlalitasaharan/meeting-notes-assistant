from __future__ import annotations

import logging
from typing import Any

from rq import get_current_job
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.meeting import Meeting
from app.models.meeting_notes import MeetingNotes
from app.services.media import load_audio_for_meeting
from app.services.notes import generate_meeting_notes
from app.services.transcription import transcribe_audio

log = logging.getLogger(__name__)


def process_meeting(meeting_id: str) -> None:
    """
    Golden-path meeting processing job (DB + notes persistence).

    Current v0 behaviour:
      - Loads Meeting from DB
      - Marks status PROCESSING -> DONE / ERROR
      - Uses stub media/transcription/LLM helpers
      - Persists a MeetingNotes row with structured notes

    Storage and real transcription/LLM are still stubbed and will be wired next.
    """
    job = get_current_job()
    job_id = job.id if job is not None else None
    log_extra: dict[str, Any] = {"meeting_id": meeting_id, "job_id": job_id}

    log.info("process_meeting: job started", extra=log_extra)

    db: Session | None = None
    try:
        db = SessionLocal()

        # 1) Load meeting
        meeting = db.get(Meeting, meeting_id)
        if meeting is None:
            log.error("process_meeting: meeting not found", extra=log_extra)
            return

        # 2) Mark as PROCESSING (if status field exists)
        if hasattr(meeting, "status"):
            meeting.status = "PROCESSING"
        if hasattr(meeting, "last_error"):
            setattr(meeting, "last_error", None)

        db.commit()
        db.refresh(meeting)

        # 3) Media → audio (still stubbed)
        fake_video_bytes = b"stub-video"  # later: fetch from MinIO using raw_media_path
        log.info("process_meeting: loading audio", extra=log_extra)
        audio_bytes = load_audio_for_meeting(meeting_id, fake_video_bytes)

        # 4) Transcription
        log.info("process_meeting: transcribing audio", extra=log_extra)
        transcript = transcribe_audio(audio_bytes)

        # 5) LLM summarization
        log.info("process_meeting: generating notes", extra=log_extra)
        notes_dict = generate_meeting_notes(transcript)

        # 6) Persist MeetingNotes row
        notes_row = MeetingNotes(
            meeting_id=str(meeting.id),
            raw_transcript=transcript,
            summary=notes_dict.get("summary") or "",
            key_points=notes_dict.get("key_points") or [],
            action_items=notes_dict.get("action_items") or [],
            model_version=notes_dict.get("model_version"),
        )
        db.add(notes_row)

        # 7) Mark meeting as DONE
        if hasattr(meeting, "status"):
            meeting.status = "DONE"
        if hasattr(meeting, "last_error"):
            setattr(meeting, "last_error", None)

        db.commit()

        log.info(
            "process_meeting: finished",
            extra={**log_extra, "summary_preview": notes_dict.get("summary", "")[:80]},
        )
    except Exception as exc:
        log.exception("process_meeting: error", extra=log_extra)

        if db is not None:
            try:
                db.rollback()
                meeting = db.get(Meeting, meeting_id)
                if meeting is not None and hasattr(meeting, "status"):
                    meeting.status = "ERROR"
                    if hasattr(meeting, "last_error"):
                        msg = str(exc)
                        setattr(meeting, "last_error", msg[:250])
                    db.commit()
            except Exception:
                db.rollback()

        # Re-raise so callers / RQ can see failure
        raise
    finally:
        if db is not None:
            db.close()
