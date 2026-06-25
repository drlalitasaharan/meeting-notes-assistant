from __future__ import annotations

import copy
import re
from typing import Any


def apply_quality_engine_v2(
    notes: dict[str, Any],
    transcript_text: str | None,
) -> dict[str, Any]:
    """Apply conservative Quality Engine v2 improvements to generated notes.

    This pass is intentionally additive and evidence-preserving. It should not
    remove existing decisions, actions, or summary fields unless a later guarded
    cleanup explicitly does so.
    """

    improved = copy.deepcopy(notes)

    summary_slots = improved.get("summary_slots")
    if not isinstance(summary_slots, dict):
        summary_slots = {}

    summary_slots = dict(summary_slots)

    if not _text(summary_slots.get("purpose")):
        inferred_purpose = _infer_purpose(transcript_text) or _infer_purpose(
            _text(improved.get("summary"))
        )
        if inferred_purpose:
            summary_slots["purpose"] = inferred_purpose

    action_items = improved.get("action_item_objects")
    if not isinstance(action_items, list):
        action_items = []

    next_steps = summary_slots.get("next_steps")
    if not isinstance(next_steps, list):
        next_steps = []

    summary_slots["next_steps"] = _sync_next_steps_from_actions(
        next_steps,
        action_items,
    )

    improved["summary_slots"] = summary_slots

    decision_objects = improved.get("decision_objects")
    if not isinstance(decision_objects, list):
        decision_objects = []

    improved["decision_objects"] = decision_objects
    improved["action_item_objects"] = action_items

    return improved


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _clean_sentence(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip(" .")
    if not cleaned:
        return ""
    return cleaned[0].upper() + cleaned[1:] + "."


def _infer_purpose(text: str | None) -> str:
    normalized = _text(text)
    if not normalized:
        return ""

    patterns = [
        r"\b(?:today we need to|we need to|the goal is to|goal is to)\s+([^.\n]+)",
        r"\b(?:the purpose is to|purpose is to)\s+([^.\n]+)",
        r"\b(?:confirm|review|align on)\s+([^.\n]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if not match:
            continue

        purpose = match.group(1).strip(" .")
        purpose = re.sub(r"\band\s+the\s+", "and ", purpose, flags=re.IGNORECASE)
        if purpose:
            return _clean_sentence(f"Confirm {purpose}")

    return ""


def _action_to_next_step(action_item: Any) -> str:
    if not isinstance(action_item, dict):
        return ""

    task = _text(
        action_item.get("task")
        or action_item.get("action")
        or action_item.get("text")
        or action_item.get("description")
    )
    if not task:
        return ""

    owner = _text(action_item.get("owner"))
    if owner:
        task = re.sub(rf"^{re.escape(owner)}\s*[-:]\s*", "", task, flags=re.IGNORECASE)

    return _clean_sentence(task)


def _dedupe_key(text: str) -> str:
    normalized = text.lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _sync_next_steps_from_actions(
    existing_next_steps: list[Any],
    action_items: list[Any],
    *,
    limit: int = 5,
) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()

    for step in existing_next_steps:
        step_text = _clean_sentence(_text(step))
        key = _dedupe_key(step_text)
        if step_text and key not in seen:
            seen.add(key)
            output.append(step_text)

    for action_item in action_items:
        step_text = _action_to_next_step(action_item)
        key = _dedupe_key(step_text)
        if step_text and key not in seen:
            seen.add(key)
            output.append(step_text)

        if len(output) >= limit:
            break

    return output[:limit]


VALID_NOTES_ENGINE_MODES = {"v1", "v2", "shadow"}


def normalize_notes_engine_mode(value: object) -> str:
    """Normalize NOTES_ENGINE mode.

    Defaults to v1 for safety.
    """

    mode = str(value or "").strip().lower()
    if mode in VALID_NOTES_ENGINE_MODES:
        return mode
    return "v1"


def should_apply_quality_engine_v2(mode: object) -> bool:
    """Return True only when v2 should become the user-facing notes output."""

    return normalize_notes_engine_mode(mode) == "v2"


def should_run_quality_engine_v2_shadow(mode: object) -> bool:
    """Return True when v2 should run for comparison only."""

    return normalize_notes_engine_mode(mode) == "shadow"
