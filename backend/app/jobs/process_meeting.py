from __future__ import annotations

import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import boto3
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
from app.services.notes_pipeline.consistency import apply_risk_action_owner_consistency
from app.services.notes_postprocess import normalize_canonical_notes
from app.services.notes_quality_pass import (
    _pilot_rc1_precision_cleanup_result,
    apply_focused_30min_quality_pass,
)
from app.services.ocr import extract_slide_text_for_meeting
from app.services.persisted_action_contract import (
    _finalize_persisted_action_contract,
    align_action_items_with_objects,
)
from app.services.processing_observability import (
    begin_attempt,
    commit_stage,
    mark_completed,
    mark_failed,
)
from app.services.quality_engine_v2 import (
    resolve_notes_engine_mode_for_user,
    run_quality_engine_v2,
)
from app.services.transcription import get_transcriber

log = logging.getLogger(__name__)


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


def _media_suffix(raw_media_path: str) -> str:
    suffix = Path(raw_media_path.split("?", 1)[0]).suffix.lower()
    return (
        suffix
        if suffix
        in {".flac", ".m4a", ".mp3", ".mp4", ".mpeg", ".mpga", ".oga", ".ogg", ".wav", ".webm"}
        else ".mp3"
    )


def _read_raw_media_bytes(raw_media_path: str) -> bytes:
    if raw_media_path.startswith("s3://"):
        parsed = urlparse(raw_media_path)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        if not bucket or not key:
            raise RuntimeError(f"Invalid S3 raw_media_path: {raw_media_path}")

        obj = _s3_client().get_object(Bucket=bucket, Key=key)
        return obj["Body"].read()

    if not os.path.exists(raw_media_path):
        raise RuntimeError(f"Raw media file not found: {raw_media_path}")

    with open(raw_media_path, "rb") as f:
        return f.read()


def _restore_publishable_actions_from_objects(notes: dict[str, Any]) -> dict[str, Any]:
    """Ensure recovered action objects remain visible in persisted/API fields.

    Some canonical normalization keeps action_item_objects but clears the
    user-facing action_items and summary_slots.next_steps fields. For
    transcript-recalled long-meeting actions, preserve the recovered objects as
    publishable action lines and next steps.
    """

    action_items = list(notes.get("action_items") or [])
    action_objects = list(notes.get("action_item_objects") or [])

    if action_items or not action_objects:
        return notes

    restored_items: list[str] = []
    restored_next_steps: list[str] = []

    for item in action_objects:
        if not isinstance(item, dict):
            continue

        owner = str(item.get("owner") or "").strip()
        task = str(item.get("task") or "").strip()
        due_date = str(item.get("due_date") or "").strip()

        if not task:
            continue

        line = f"{owner} - {task}" if owner else task
        if due_date:
            line += f" (due: {due_date})"

        restored_items.append(line)
        restored_next_steps.append(task.rstrip(".") + ".")

    if not restored_items:
        return notes

    notes = dict(notes)
    notes["action_items"] = restored_items

    summary_slots = dict(notes.get("summary_slots") or {})
    if not summary_slots.get("next_steps"):
        summary_slots["next_steps"] = restored_next_steps[:5]
    notes["summary_slots"] = summary_slots

    return notes


def _meeting_owner_email(meeting: Meeting) -> str:
    try:
        user = getattr(meeting, "user", None)
        return str(getattr(user, "email", "") or "").strip()
    except Exception:
        return ""


def _resolve_notes_engine_mode_for_meeting(meeting: Meeting) -> str:
    return resolve_notes_engine_mode_for_user(
        os.getenv("NOTES_ENGINE", "v1"),
        _meeting_owner_email(meeting),
    )


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
    current_stage = "uploaded"
    try:
        db = SessionLocal()

        meeting_pk = int(meeting_id)

        # 1) Load meeting
        meeting = db.get(Meeting, meeting_pk)
        if meeting is None:
            raise RuntimeError(f"Meeting {meeting_id} not found in worker database")

        # 2) Mark as PROCESSING
        begin_attempt(meeting)
        db.commit()
        db.refresh(meeting)

        # 3) Read real uploaded media from saved path
        raw_media_path = getattr(meeting, "raw_media_path", None)
        if not raw_media_path:
            raise RuntimeError(f"Meeting {meeting.id} has no raw_media_path")

        log.info(
            "process_meeting: loading audio",
            extra={**log_extra, "raw_media_path": raw_media_path},
        )

        try:
            media_bytes = _read_raw_media_bytes(raw_media_path)
        except RuntimeError as exc:
            raise RuntimeError(
                f"Raw media file not found for meeting {meeting.id}: {raw_media_path}"
            ) from exc

        current_stage = "processing_audio"
        commit_stage(
            db,
            meeting,
            current_stage,
            status="PROCESSING",
            completed_key="media_validation_completed_at",
            started_key="audio_conversion_started_at",
        )
        audio_bytes = load_audio_for_meeting(str(meeting.id), media_bytes)
        commit_stage(
            db,
            meeting,
            current_stage,
            status="PROCESSING",
            completed_key="audio_conversion_completed_at",
        )

        # 4) Transcription
        log.info("process_meeting: transcribing audio", extra=log_extra)
        current_stage = "transcribing"
        commit_stage(
            db,
            meeting,
            current_stage,
            status="PROCESSING",
            started_key="transcription_started_at",
        )

        with tempfile.NamedTemporaryFile(suffix=_media_suffix(raw_media_path), delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_audio_path = tmp.name

        try:
            transcription = get_transcriber().transcribe(tmp_audio_path)
        finally:
            try:
                os.remove(tmp_audio_path)
            except OSError:
                pass
        commit_stage(
            db,
            meeting,
            current_stage,
            status="PROCESSING",
            completed_key="transcription_completed_at",
        )

        # 4a) Optional slide OCR enrichment
        log.info("process_meeting: running slide OCR", extra=log_extra)
        slide_text = extract_slide_text_for_meeting(
            db=db,
            meeting_id=meeting.id,
        )

        # 5) Generate notes
        log.info("process_meeting: generating notes", extra=log_extra)
        current_stage = "generating_notes"
        commit_stage(
            db,
            meeting,
            current_stage,
            status="PROCESSING",
            started_key="notes_generation_started_at",
        )

        notes_strategy_name = getattr(settings, "NOTES_STRATEGY", "local_summary")

        raw_transcript_payload = transcription.to_dict()
        transcript_text = str(
            getattr(transcription, "text", "") or raw_transcript_payload.get("text") or ""
        )
        if slide_text:
            raw_transcript_payload["slide_text"] = slide_text

        if notes_strategy_name == "local_rules":
            notes_dict = generate_meeting_notes(raw_transcript_payload)
        else:
            notes_result = get_notes_strategy().generate(transcript_text, slide_text or "")
            notes_dict = notes_result.to_api_dict()
            notes_dict = normalize_canonical_notes(notes_dict)
            notes_dict = apply_focused_30min_quality_pass(notes_dict, transcript_text)
        commit_stage(
            db,
            meeting,
            current_stage,
            status="PROCESSING",
            completed_key="notes_generation_completed_at",
        )

        current_stage = "finalizing"
        commit_stage(
            db,
            meeting,
            current_stage,
            status="PROCESSING",
            started_key="finalization_started_at",
        )
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

        decision_action_recall_text = "\n".join(
            str(item.get("text") or "") for item in decision_objects if isinstance(item, dict)
        )
        raw_action_recall_text = "\n".join(
            part
            for part in [
                str(
                    locals().get("transcript_text")
                    or locals().get("transcript")
                    or locals().get("raw_transcript")
                    or ""
                ),
                decision_action_recall_text,
            ]
            if part.strip()
        )

        cleaned_action_items, action_item_objects, summary_slots = (
            _finalize_persisted_action_contract(
                cleaned_action_items=cleaned_action_items,
                action_item_objects=action_item_objects,
                summary_slots=summary_slots,
                raw_transcript_text=raw_action_recall_text,
            )
        )

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
        normalized_notes = _restore_publishable_actions_from_objects(normalized_notes)
        normalized_notes = apply_risk_action_owner_consistency(normalized_notes)

        notes_engine_mode = _resolve_notes_engine_mode_for_meeting(meeting)
        commit_stage(
            db,
            meeting,
            current_stage,
            status="PROCESSING",
            started_key="quality_engine_started_at",
        )
        quality_engine_result = run_quality_engine_v2(
            normalized_notes,
            transcript_text,
            mode=notes_engine_mode,
        )
        commit_stage(
            db,
            meeting,
            current_stage,
            status="PROCESSING",
            completed_key="quality_engine_completed_at",
        )
        if quality_engine_result.get("metadata", {}).get("mode") == "v2":
            normalized_notes = quality_engine_result["notes"]

        for action_obj in normalized_notes.get("action_item_objects", []) or []:
            if not isinstance(action_obj, dict):
                continue
            task = str(action_obj.get("task") or "").strip()
            for marker_text in (". Confirmed,", ". confirmed,"):
                if marker_text in task:
                    task = task.split(marker_text, 1)[0].strip()
            task = re.sub(r"\s+that$", "", task, flags=re.I)
            if task:
                action_obj["task"] = task
                action_obj["text"] = f"{action_obj.get('owner') or 'Team'}: {task}"

        for action_obj in normalized_notes.get("action_item_objects", []) or []:
            if not isinstance(action_obj, dict):
                continue
            task = str(action_obj.get("task") or "").strip()
            for marker in (". Confirmed,", ". confirmed,"):
                if marker in task:
                    task = task.split(marker, 1)[0].strip()
            task = re.sub(r"\s+that$", "", task, flags=re.I)
            if task:
                action_obj["task"] = task
                action_obj["text"] = f"{action_obj.get('owner') or 'Team'}: {task}"

        normalized_notes["action_items"] = align_action_items_with_objects(
            normalized_notes.get("action_items") or [],
            normalized_notes.get("action_item_objects") or [],
        )

        if normalized_notes.get("action_item_objects"):
            summary_slots_for_publish = dict(normalized_notes.get("summary_slots") or {})
            summary_slots_for_publish["next_steps"] = [
                str(item.get("task") or "").rstrip(".") + "."
                for item in normalized_notes.get("action_item_objects", [])[:5]
                if isinstance(item, dict) and str(item.get("task") or "").strip()
            ]
            normalized_notes["summary_slots"] = summary_slots_for_publish

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
        db.query(MeetingNotes).filter(MeetingNotes.meeting_id == meeting.id).delete(
            synchronize_session=False
        )
        db.add(notes_row)

        commit_stage(
            db,
            meeting,
            current_stage,
            status="PROCESSING",
            completed_key="finalization_completed_at",
        )

        # 7) Mark meeting as DONE
        mark_completed(meeting)

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
                        mark_failed(meeting, exc, stage=current_stage)
                        db.commit()
            except Exception:
                db.rollback()

        raise

    finally:
        if db is not None:
            db.close()
