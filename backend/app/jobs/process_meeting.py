from __future__ import annotations

import logging
import os
from typing import Any

from rq import get_current_job
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db import SessionLocal
from app.models.meeting import Meeting
from app.models.meeting_notes import MeetingNotes
from app.services.media import load_audio_for_meeting
from app.services.note_strategies.factory import get_notes_strategy
from app.services.notes import generate_meeting_notes
from app.services.ocr import extract_slide_text_for_meeting
from app.services.transcription import transcribe_audio

log = logging.getLogger(__name__)


def process_meeting(meeting_id: str) -> None:
    """
    Golden-path meeting processing job.

    Current behaviour:
      - Loads Meeting from DB
      - Marks status PROCESSING -> DONE / ERROR
      - Reads the real uploaded media from meeting.raw_media_path
      - Extracts audio bytes via app.services.media.load_audio_for_meeting
      - Transcribes audio locally
      - Optionally enriches transcript with slide OCR
      - Generates notes
      - Persists a MeetingNotes row
    """
    job = get_current_job()
    job_id = job.id if job is not None else None
    log_extra: dict[str, Any] = {"meeting_id": meeting_id, "job_id": job_id}

    log.info("process_meeting: job started", extra=log_extra)

    db: Session | None = None
    try:
        db = SessionLocal()

        meeting_pk = int(meeting_id)

        # 1) Load meeting
        meeting = db.get(Meeting, meeting_pk)
        if meeting is None:
            raise RuntimeError(f"Meeting {meeting_id} not found in worker database")

        # 2) Mark as PROCESSING
        if hasattr(meeting, "status"):
            meeting.status = "PROCESSING"
        if hasattr(meeting, "last_error"):
            meeting.last_error = None

        db.commit()
        db.refresh(meeting)

        # 3) Read real uploaded media from saved path
        raw_media_path = getattr(meeting, "raw_media_path", None)
        if not raw_media_path:
            raise RuntimeError(f"Meeting {meeting.id} has no raw_media_path")

        if not os.path.exists(raw_media_path):
            raise RuntimeError(
                f"Raw media file not found for meeting {meeting.id}: {raw_media_path}"
            )

        log.info(
            "process_meeting: loading audio",
            extra={**log_extra, "raw_media_path": raw_media_path},
        )

        with open(raw_media_path, "rb") as f:
            media_bytes = f.read()

        audio_bytes = load_audio_for_meeting(str(meeting.id), media_bytes)

        # 4) Transcription
        log.info("process_meeting: transcribing audio", extra=log_extra)
        transcript = transcribe_audio(audio_bytes)

        # 4a) Optional slide OCR enrichment
        log.info("process_meeting: running slide OCR", extra=log_extra)
        slide_text = extract_slide_text_for_meeting(
            db=db,
            meeting_id=meeting.id,
        )

        if slide_text:
            if not isinstance(transcript, dict):
                transcript = dict(transcript)  # type: ignore[arg-type]
            transcript["slide_text"] = slide_text  # type: ignore[index]

        # 5) Generate notes
        log.info("process_meeting: generating notes", extra=log_extra)

        notes_strategy_name = getattr(settings, "NOTES_STRATEGY", "local_summary")

        if notes_strategy_name == "local_rules":
            notes_dict = generate_meeting_notes(transcript)
        else:
            transcript_text = str(transcript.get("text", "") or "")
            slide_text = str(transcript.get("slide_text", "") or "")
            notes_result = get_notes_strategy().generate(transcript_text, slide_text)
            notes_dict = notes_result.to_api_dict()

        # 6) Persist MeetingNotes row
        notes_row = MeetingNotes(
            meeting_id=meeting.id,
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
            meeting.last_error = None

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

                try:
                    meeting_pk = int(meeting_id)
                except ValueError:
                    meeting_pk = None

                if meeting_pk is not None:
                    meeting = db.get(Meeting, meeting_pk)
                    if meeting is not None:
                        if hasattr(meeting, "status"):
                            meeting.status = "ERROR"
                        if hasattr(meeting, "last_error"):
                            meeting.last_error = str(exc)[:250]
                        db.commit()
            except Exception:
                db.rollback()

        raise

    finally:
        if db is not None:
            db.close()
