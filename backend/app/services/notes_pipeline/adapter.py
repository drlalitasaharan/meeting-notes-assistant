from __future__ import annotations

from typing import Any, Dict, List

from app.services.notes_pipeline.orchestrator import build_canonical_notes, build_markdown


def _dump(model: Any) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _format_action_item(item: Dict[str, Any]) -> str:
    text = item.get("text", "").strip()
    owner = item.get("owner")
    due_date = item.get("due_date")

    suffix: List[str] = []
    if owner:
        suffix.append(f"owner: {owner}")
    if due_date:
        suffix.append(f"due: {due_date}")

    if suffix:
        return f"{text} ({', '.join(suffix)})"
    return text


def build_legacy_notes_payload(meeting_id: int, transcript_text: str) -> Dict[str, Any]:
    notes = build_canonical_notes(meeting_id=meeting_id, transcript_text=transcript_text)
    payload = _dump(notes)

    return {
        "meeting_id": meeting_id,
        "status": "DONE",
        "model_version": "canonical-slots-v1",
        "summary": payload.get("summary", ""),
        "key_points": payload.get("key_points", []),
        "action_items": [_format_action_item(item) for item in payload.get("action_items", [])],
        "purpose": payload.get("purpose", ""),
        "outcome": payload.get("outcome", ""),
        "decisions": payload.get("decisions", []),
        "risks": payload.get("risks", []),
        "next_steps": payload.get("next_steps", []),
        "metadata": payload.get("metadata", {}),
    }


def build_legacy_notes_markdown(meeting_id: int, transcript_text: str) -> str:
    notes = build_canonical_notes(meeting_id=meeting_id, transcript_text=transcript_text)
    return build_markdown(notes)
