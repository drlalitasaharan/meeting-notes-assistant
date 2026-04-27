from __future__ import annotations

import logging
import os
import tempfile
from typing import Any

from rq import get_current_job
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db import SessionLocal
from app.models.meeting import Meeting
from app.models.meeting_notes import MeetingNotes
from app.services.action_cleanup_pass import apply_deterministic_action_cleanup
from app.services.action_item_postprocess import clean_action_items
from app.services.media import load_audio_for_meeting
from app.services.note_strategies.factory import get_notes_strategy
from app.services.notes import generate_meeting_notes
from app.services.notes_postprocess import normalize_canonical_notes
from app.services.notes_quality_pass import (
    _pilot_rc1_precision_cleanup_result,
    apply_focused_30min_quality_pass,
)
from app.services.ocr import extract_slide_text_for_meeting
from app.services.transcription import get_transcriber

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

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_audio_path = tmp.name

        try:
            transcription = get_transcriber().transcribe(tmp_audio_path)
        finally:
            try:
                os.remove(tmp_audio_path)
            except OSError:
                pass

        # 4a) Optional slide OCR enrichment
        log.info("process_meeting: running slide OCR", extra=log_extra)
        slide_text = extract_slide_text_for_meeting(
            db=db,
            meeting_id=meeting.id,
        )

        # 5) Generate notes
        log.info("process_meeting: generating notes", extra=log_extra)

        notes_strategy_name = getattr(settings, "NOTES_STRATEGY", "local_summary")

        raw_transcript_payload = transcription.to_dict()
        if slide_text:
            raw_transcript_payload["slide_text"] = slide_text

        if notes_strategy_name == "local_rules":
            notes_dict = generate_meeting_notes(raw_transcript_payload)
        else:
            transcript_text = transcription.text
            notes_result = get_notes_strategy().generate(transcript_text, slide_text or "")
            notes_dict = notes_result.to_api_dict()
            notes_dict = normalize_canonical_notes(notes_dict)
            notes_dict = apply_focused_30min_quality_pass(notes_dict, transcript_text)

        cleaned_action_items = clean_action_items(notes_dict.get("action_items") or [])
        action_item_objects = notes_dict.get("action_item_objects") or []

        if not cleaned_action_items and action_item_objects:
            rebuilt: list[str] = []
            for item in action_item_objects:
                owner = str(item.get("owner") or "").strip()
                task = str(item.get("task") or "").strip()
                due_date = str(item.get("due_date") or "").strip()

                if not task:
                    continue

                line = f"{owner} - {task}" if owner else task
                if due_date:
                    line += f" (due: {due_date})"
                rebuilt.append(line)

            cleaned_action_items = clean_action_items(rebuilt)

        cleaned_action_items, action_item_objects = apply_deterministic_action_cleanup(
            cleaned_action_items,
            action_item_objects,
        )

        summary_text = str(notes_dict.get("summary") or "")
        summary_slots = notes_dict.get("summary_slots") or None
        key_points = notes_dict.get("key_points") or []
        decisions = notes_dict.get("decisions") or []
        decision_objects = notes_dict.get("decision_objects") or []

        precision_payload: dict[str, Any] = {
            "summary": summary_text,
            "summary_slots": summary_slots,
            "key_points": key_points,
            "action_items": cleaned_action_items,
            "action_item_objects": action_item_objects,
            "decisions": decisions,
            "decision_objects": decision_objects,
        }
        precision_payload = _pilot_rc1_precision_cleanup_result(precision_payload)

        cleaned_action_items = precision_payload.get("action_items") or []
        action_item_objects = precision_payload.get("action_item_objects") or []
        decisions = precision_payload.get("decisions") or []
        decision_objects = precision_payload.get("decision_objects") or []

        # 6) Persist MeetingNotes row
        normalized_notes = normalize_canonical_notes(
            {
                "summary": summary_text,
                "key_points": key_points,
                "action_items": cleaned_action_items,
                "summary_slots": summary_slots,
                "decisions": decisions,
                "action_item_objects": action_item_objects,
                "decision_objects": decision_objects,
            }
        )

        notes_row = MeetingNotes(
            meeting_id=meeting.id,
            raw_transcript=raw_transcript_payload,
            summary=normalized_notes["summary"],
            summary_slots=normalized_notes["summary_slots"],
            key_points=normalized_notes["key_points"],
            action_items=normalized_notes["action_items"],
            action_item_objects=normalized_notes["action_item_objects"],
            decisions=normalized_notes["decisions"],
            decision_objects=normalized_notes["decision_objects"],
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
            extra={**log_extra, "summary_preview": summary_text[:80]},
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
