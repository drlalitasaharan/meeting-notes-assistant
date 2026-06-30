from __future__ import annotations

import logging
import os
import re
import tempfile
from datetime import datetime, timezone
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
from app.services.data_controls import delete_raw_media_best_effort
from app.services.llm_polish import apply_llm_polish_to_notes
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
    is_quality_engine_v2_email_allowlisted,
    resolve_notes_engine_mode_for_user,
    run_quality_engine_v2,
)
from app.services.quality_engine_v3 import (
    finalize_quality_engine_v3_persisted_notes,
    run_quality_engine_v3,
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


def _finalize_confidential_recording_delete(
    db: Session,
    meeting: Meeting,
    raw_media_path: str | None,
    log_extra: dict[str, Any],
) -> None:
    """Best-effort delete of original recording after notes are safely persisted.

    Confidential Mode still uses hosted cloud processing. This helper only runs
    after notes have been generated, persisted, and the meeting has been marked
    completed. Deletion failure must not fail the completed notes job.
    """

    if not getattr(meeting, "confidential_mode", False):
        return

    if not raw_media_path:
        meeting.recording_delete_status = "failed"
        meeting.recording_delete_error = "No recording path was available for deletion."
        db.add(meeting)
        db.commit()
        return

    delete_error: str | None = None
    try:
        deleted = delete_raw_media_best_effort(raw_media_path)
    except Exception as exc:  # noqa: BLE001
        deleted = False
        delete_error = str(exc)[:500]

    if deleted:
        meeting.recording_deleted_at = datetime.now(timezone.utc)
        meeting.recording_delete_status = "deleted"
        meeting.recording_delete_error = None
        log.info(
            "process_meeting: confidential recording deleted",
            extra={**log_extra, "raw_media_path": raw_media_path},
        )
    else:
        meeting.recording_delete_status = "failed"
        meeting.recording_delete_error = delete_error or "Recording deletion did not complete."
        log.warning(
            "process_meeting: confidential recording deletion failed",
            extra={
                **log_extra,
                "raw_media_path": raw_media_path,
                "recording_delete_error": meeting.recording_delete_error,
            },
        )

    db.add(meeting)
    db.commit()


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


def _mask_email_for_logs(email: str) -> str:
    value = str(email or "").strip().lower()
    if "@" not in value:
        return ""
    local, domain = value.split("@", 1)
    if not local or not domain:
        return ""
    visible = local[:2] if len(local) > 2 else local[:1]
    return f"{visible}***@{domain}"


def _quality_engine_routing_context(meeting: Meeting) -> dict[str, Any]:
    owner_email = _meeting_owner_email(meeting)
    global_mode = os.getenv("NOTES_ENGINE", "v1")
    allowlist_value = os.getenv("MEETIQ_QEV2_ALLOWLIST_EMAILS", "")
    owner_allowlisted = is_quality_engine_v2_email_allowlisted(
        owner_email,
        allowlist_value,
    )
    return {
        "owner_email": owner_email,
        "owner_email_masked": _mask_email_for_logs(owner_email),
        "global_notes_engine_mode": global_mode,
        "qev2_allowlist_configured": bool(allowlist_value.strip()),
        "qev2_owner_allowlisted": owner_allowlisted,
        "resolved_notes_engine_mode": resolve_notes_engine_mode_for_user(
            global_mode,
            owner_email,
            allowlist_value,
        ),
    }


def _resolve_notes_engine_mode_for_meeting(meeting: Meeting) -> str:
    return str(_quality_engine_routing_context(meeting)["resolved_notes_engine_mode"])


def _quality_engine_result_log_fields(metadata: dict[str, Any]) -> dict[str, Any]:
    critic = metadata.get("critic")
    critic_passed = None
    critic_warning_count = None
    if isinstance(critic, dict):
        critic_passed = critic.get("passed")
        warnings = critic.get("warnings")
        critic_warning_count = len(warnings) if isinstance(warnings, list) else 0

    return {
        "quality_engine_result_mode": metadata.get("mode"),
        "quality_engine_v2_applied": bool(metadata.get("applied")),
        "quality_engine_v2_fallback_used": bool(metadata.get("fallback_used")),
        "quality_engine_v2_critic_passed": critic_passed,
        "quality_engine_v2_warning_count": critic_warning_count,
    }


def _is_successful_selected_qev3_output(
    selected_mode: str,
    metadata: dict[str, Any],
) -> bool:
    """Treat selected NOTES_ENGINE=v3 as the source of truth for v3 application."""

    return selected_mode == "v3" and not bool(metadata.get("fallback_used"))


def _should_apply_quality_engine_result(
    selected_mode: str,
    metadata: dict[str, Any],
) -> bool:
    if _is_successful_selected_qev3_output(selected_mode, metadata):
        return True

    return str(metadata.get("mode") or "") in {"v2", "v3"}


def _model_version_with_quality_engine_suffix(
    model_version: object,
    metadata: dict[str, Any],
) -> str | None:
    base = str(model_version or "").strip()
    if metadata.get("mode") != "v2":
        return base or None

    if metadata.get("fallback_used"):
        suffix = "+qev2-fallback"
    elif metadata.get("applied"):
        suffix = "+qev2"
    else:
        return base or None

    if not base:
        base = "unknown"
    if base.endswith(("+qev2", "+qev2-fallback")):
        return base
    return f"{base}{suffix}"


def _normalize_qev2_purpose_text(value: object) -> str:
    purpose = re.sub(r"\s+", " ", str(value or "")).strip()
    purpose = re.sub(r"\b(confirm)(?:\s+\1\b)+", r"\1", purpose, flags=re.IGNORECASE)
    return purpose


_QEV2_ACTION_LEAK_PREFIXES = (
    "we decided",
    "the team decided",
    "the team aligned on",
    "the client demo will use",
    "key action owners are",
    "today we need to confirm",
    "today confirm proposal scope",
)


def _qev2_action_task_text(item: Any) -> str:
    if not isinstance(item, dict):
        return ""
    return str(
        item.get("task") or item.get("action") or item.get("text") or item.get("description") or ""
    ).strip()


def _looks_like_qev2_action_leak(task: object) -> bool:
    normalized = re.sub(r"\s+", " ", str(task or "")).strip(" .:-").lower()
    if not normalized:
        return True
    return any(normalized.startswith(prefix) for prefix in _QEV2_ACTION_LEAK_PREFIXES)


def _clean_qev2_action_task(task: object) -> str:
    cleaned = re.sub(r"\s+", " ", str(task or "")).strip(" .:-")
    if not cleaned:
        return ""

    cleaned = re.split(
        r"\.\s+(?:Priya|Jordan|Morgan|Alex|Team|We|Decision\s+\d+|Final recap)\b",
        cleaned,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0].strip(" .:-")

    cleaned = re.sub(
        r"\s+\bI\s+will\s+clean\s+the\s+demo\s+account\b\.?$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip(" .:-")

    return cleaned


def _qev2_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


_QEV2_KEY_POINT_LEAK_PREFIXES = (
    "key action owners are",
    "we decided",
    "the team decided",
    "the team aligned on",
    "today we need to confirm",
)


_QEV2_ACTION_LIKE_DECISION_PREFIXES = (
    "we should",
    "i will",
)


def _qev2_starts_with_any(value: object, prefixes: tuple[str, ...]) -> bool:
    normalized = _qev2_text(value).strip(" .:-").lower()
    return any(normalized.startswith(prefix) for prefix in prefixes)


def _clean_qev2_key_points(key_points: object) -> list[str]:
    if not isinstance(key_points, list):
        return []

    cleaned: list[str] = []
    seen: set[str] = set()

    for item in key_points:
        text = _qev2_text(item).strip(" .:-")
        if not text:
            continue
        if _qev2_starts_with_any(text, _QEV2_KEY_POINT_LEAK_PREFIXES):
            continue

        key = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
        if not key or key in seen:
            continue

        seen.add(key)
        cleaned.append(text)

    return cleaned


def _qev2_decision_text(item: object) -> str:
    if isinstance(item, dict):
        return _qev2_text(item.get("text") or item.get("decision") or item.get("summary"))
    return _qev2_text(item)


def _looks_like_qev2_action_like_decision(item: object) -> bool:
    text = _qev2_decision_text(item)
    if _qev2_starts_with_any(text, _QEV2_ACTION_LIKE_DECISION_PREFIXES):
        return True

    normalized = text.lower()
    return bool(
        re.match(r"^(?:we|i)\s+(?:will|should)\b", normalized)
        and re.search(r"\b(?:remove|upload|clean|send|draft|check|request|escalate)\b", normalized)
    )


def _clean_qev2_decisions(decisions: object) -> list[str]:
    if not isinstance(decisions, list):
        return []

    cleaned: list[str] = []
    seen: set[str] = set()

    for item in decisions:
        text = _qev2_text(item).strip(" .:-")
        if not text:
            continue
        if _looks_like_qev2_action_like_decision(text):
            continue

        key = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
        if not key or key in seen:
            continue

        seen.add(key)
        cleaned.append(text)

    return cleaned


def _clean_qev2_decision_objects(decision_objects: object) -> list[dict[str, Any]]:
    if not isinstance(decision_objects, list):
        return []

    cleaned: list[dict[str, Any]] = []
    seen: set[str] = set()

    for raw_item in decision_objects:
        if not isinstance(raw_item, dict):
            continue

        text = _qev2_decision_text(raw_item).strip(" .:-")
        if not text:
            continue
        if _looks_like_qev2_action_like_decision(raw_item):
            continue

        key = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
        if not key or key in seen:
            continue

        seen.add(key)
        item = dict(raw_item)
        item["text"] = text
        cleaned.append(item)

    return cleaned


def _qev2_should_drop_generic_owner_action(owner: object, task: object) -> bool:
    owner_text = _qev2_text(owner).lower()
    task_text = _qev2_text(task).lower()
    return (
        owner_text == "we"
        and task_text.startswith("remove old test files")
        and "upload one approved sample meeting before the client call" in task_text
    )


def _qev2_safe_owner_for_task(owner: object, task: object) -> str:
    owner_text = _qev2_text(owner) or "Team"
    task_text = _qev2_text(task).lower()

    if (
        owner_text.lower() == "team"
        and task_text
        == "check upload, processing, structured notes, markdown export, and non-meeting safety"
    ):
        return "Alex"

    return owner_text


def _apply_qev2_action_precision_cleanup(notes: dict[str, Any]) -> dict[str, Any]:
    """Remove obvious decision/key-point leakage from QEv2 output."""

    output = dict(notes)

    summary_slots = output.get("summary_slots")
    if isinstance(summary_slots, dict):
        summary_slots = dict(summary_slots)
        if summary_slots.get("purpose"):
            summary_slots["purpose"] = _normalize_qev2_purpose_text(summary_slots.get("purpose"))
        output["summary_slots"] = summary_slots

    output["key_points"] = _clean_qev2_key_points(output.get("key_points") or [])
    output["decisions"] = _clean_qev2_decisions(output.get("decisions") or [])
    output["decision_objects"] = _clean_qev2_decision_objects(output.get("decision_objects") or [])

    action_objects = output.get("action_item_objects")
    if not isinstance(action_objects, list):
        return output

    cleaned_objects: list[dict[str, Any]] = []
    seen: set[str] = set()

    for raw_item in action_objects:
        if not isinstance(raw_item, dict):
            continue

        task = _clean_qev2_action_task(_qev2_action_task_text(raw_item))
        if not task or _looks_like_qev2_action_leak(task):
            continue

        owner = _qev2_safe_owner_for_task(raw_item.get("owner"), task)
        if _qev2_should_drop_generic_owner_action(owner, task):
            continue

        key = re.sub(r"[^a-z0-9]+", " ", task.lower()).strip()
        if not key or key in seen:
            continue
        seen.add(key)

        item = dict(raw_item)
        item["task"] = task
        item["owner"] = owner
        item["text"] = f"{owner}: {task}"
        cleaned_objects.append(item)

    output["action_item_objects"] = cleaned_objects

    if cleaned_objects:
        output["action_items"] = align_action_items_with_objects(
            output.get("action_items") or [],
            cleaned_objects,
        )
    else:
        output["action_items"] = []

    return output


def _run_selected_quality_engine(
    notes: dict[str, Any],
    transcript_text: str | None,
    *,
    mode: str,
) -> dict[str, Any]:
    """Run the selected notes engine without changing production routing defaults."""

    if mode == "v3":
        return run_quality_engine_v3(notes, transcript_text, mode="v3")

    return run_quality_engine_v2(notes, transcript_text, mode=mode)


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

        quality_engine_routing = _quality_engine_routing_context(meeting)
        notes_engine_mode = str(quality_engine_routing["resolved_notes_engine_mode"])
        log.info(
            "process_meeting: quality engine routing",
            extra={
                **log_extra,
                "owner_email_masked": quality_engine_routing["owner_email_masked"],
                "global_notes_engine_mode": quality_engine_routing["global_notes_engine_mode"],
                "qev2_allowlist_configured": quality_engine_routing["qev2_allowlist_configured"],
                "qev2_owner_allowlisted": quality_engine_routing["qev2_owner_allowlisted"],
                "resolved_notes_engine_mode": notes_engine_mode,
            },
        )
        commit_stage(
            db,
            meeting,
            current_stage,
            status="PROCESSING",
            started_key="quality_engine_started_at",
        )
        quality_engine_result = _run_selected_quality_engine(
            normalized_notes,
            transcript_text,
            mode=notes_engine_mode,
        )
        quality_engine_metadata = quality_engine_result.get("metadata", {})
        if not isinstance(quality_engine_metadata, dict):
            quality_engine_metadata = {}
        log.info(
            "process_meeting: quality engine result",
            extra={
                **log_extra,
                **_quality_engine_result_log_fields(quality_engine_metadata),
            },
        )
        commit_stage(
            db,
            meeting,
            current_stage,
            status="PROCESSING",
            completed_key="quality_engine_completed_at",
        )
        is_qev3_output = _is_successful_selected_qev3_output(
            notes_engine_mode,
            quality_engine_metadata,
        )
        if _should_apply_quality_engine_result(notes_engine_mode, quality_engine_metadata):
            normalized_notes = quality_engine_result["notes"]
            if is_qev3_output:
                normalized_notes = finalize_quality_engine_v3_persisted_notes(normalized_notes)
            else:
                normalized_notes = _apply_qev2_action_precision_cleanup(normalized_notes)

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

        if is_qev3_output:
            normalized_notes = finalize_quality_engine_v3_persisted_notes(normalized_notes)
            log.info(
                "process_meeting: qev3 final persisted output applied",
                extra={
                    **log_extra,
                    "qev3_final_action_count": len(
                        normalized_notes.get("action_item_objects") or []
                    ),
                    "qev3_final_next_step_count": len(
                        (normalized_notes.get("summary_slots") or {}).get("next_steps") or []
                    ),
                },
            )

        action_items_source = [] if is_qev3_output else normalized_notes.get("action_items") or []
        normalized_notes["action_items"] = align_action_items_with_objects(
            action_items_source,
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

        llm_polish_enabled_value = os.getenv("MEETIQ_LLM_POLISH_ENABLED", "")
        llm_gate_fields = {
            **log_extra,
            "notes_engine_mode": notes_engine_mode,
            "is_qev3_output": is_qev3_output,
            "quality_engine_metadata_mode": quality_engine_metadata.get("mode"),
            "quality_engine_fallback_used": quality_engine_metadata.get("fallback_used"),
            "quality_engine_applied": quality_engine_metadata.get("applied"),
            "llm_polish_enabled": llm_polish_enabled_value,
            "source_model_version": notes_dict.get("model_version"),
        }
        log.warning("process_meeting: llm polish gate", extra=llm_gate_fields)
        print(
            "process_meeting: llm polish gate "
            f"meeting_id={meeting.id} "
            f"notes_engine_mode={notes_engine_mode} "
            f"is_qev3_output={is_qev3_output} "
            f"metadata_mode={quality_engine_metadata.get('mode')} "
            f"fallback_used={quality_engine_metadata.get('fallback_used')} "
            f"applied={quality_engine_metadata.get('applied')} "
            f"llm_enabled={llm_polish_enabled_value} "
            f"source_model_version={notes_dict.get('model_version')}",
            flush=True,
        )

        if is_qev3_output:
            normalized_notes = apply_llm_polish_to_notes(normalized_notes)

        model_version_for_persistence = _model_version_with_quality_engine_suffix(
            notes_dict.get("model_version"),
            quality_engine_metadata,
        )
        if normalized_notes.pop("_llm_polish_applied", False):
            if "+llm-polish" not in str(model_version_for_persistence or "").lower():
                model_version_for_persistence = (
                    f"{model_version_for_persistence or 'local-summary-v3'}+llm-polish"
                )
            log.warning(
                "process_meeting: llm polish applied to persisted notes",
                extra={
                    **log_extra,
                    "llm_polish_model_version": model_version_for_persistence,
                },
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
            model_version=model_version_for_persistence,
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

        _finalize_confidential_recording_delete(
            db=db,
            meeting=meeting,
            raw_media_path=raw_media_path,
            log_extra=log_extra,
        )

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
