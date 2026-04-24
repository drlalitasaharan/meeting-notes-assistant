from __future__ import annotations

import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class TranscriptRecord:
    def __init__(self, text: str, source: str = "transcript") -> None:
        self.text = text
        self.source = source


def _normalize(value: Any) -> Any:
    if value is None:
        return None

    if hasattr(value, "model_dump"):
        return _normalize(value.model_dump())

    if hasattr(value, "dict"):
        return _normalize(value.dict())

    if is_dataclass(value):
        return _normalize(asdict(value))

    if isinstance(value, dict):
        return {str(k): _normalize(v) for k, v in value.items()}

    if isinstance(value, list | tuple):
        return [_normalize(v) for v in value]

    if hasattr(value, "__dict__") and not isinstance(value, str | int | float | bool):
        return {str(k): _normalize(v) for k, v in vars(value).items() if not k.startswith("_")}

    return value


def _blob(value: Any) -> str:
    value = _normalize(value)

    if value is None:
        return ""

    if isinstance(value, dict):
        return " ".join(_blob(v) for v in value.values())

    if isinstance(value, list):
        return " ".join(_blob(v) for v in value)

    return str(value)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [value]


def _get_nested(data: dict[str, Any], path: str, default: Any = None) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return default
        current = current.get(part)
        if current is None:
            return default
    return current


def _generate_notes_from_transcript(text: str) -> dict[str, Any]:
    from app.services.note_strategies.local_summary import LocalSummaryStrategy

    strategy = LocalSummaryStrategy()

    dict_records = [{"text": text, "source": "transcript"}]
    object_records = [TranscriptRecord(text)]

    candidate_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = [
        ((object_records,), {}),
        ((dict_records,), {}),
        ((), {"records": object_records}),
        ((), {"records": dict_records}),
        ((), {"segments": object_records}),
        ((), {"segments": dict_records}),
        ((text,), {}),
        ((), {"text": text}),
        ((), {"transcript_text": text}),
        ((), {"transcript": text}),
    ]

    errors: list[str] = []

    for args, kwargs in candidate_calls:
        try:
            result = strategy.generate(*args, **kwargs)
        except TypeError as exc:
            errors.append(str(exc))
            continue

        normalized = _normalize(result)

        if isinstance(normalized, dict):
            return normalized

        raise AssertionError(
            f"Expected notes dict from LocalSummaryStrategy.generate, "
            f"got {type(normalized)}: {normalized!r}"
        )

    raise AssertionError(
        "Could not call LocalSummaryStrategy.generate with any known transcript-level "
        f"signature. Last errors: {errors[-5:]}"
    )


def _decision_items(notes: dict[str, Any]) -> list[Any]:
    return _as_list(notes.get("decision_objects")) or _as_list(notes.get("decisions"))


def _action_items(notes: dict[str, Any]) -> list[Any]:
    return _as_list(notes.get("action_item_objects")) or _as_list(notes.get("action_items"))


def test_meeting81_real_meeting_quality_gate() -> None:
    transcript = (FIXTURES / "meeting81_transcript_excerpt.txt").read_text()
    notes = _generate_notes_from_transcript(transcript)

    outcome = _get_nested(notes, "summary_slots.outcome", "") or notes.get("outcome", "")
    next_steps = _get_nested(notes, "summary_slots.next_steps", []) or notes.get("next_steps", [])
    actions = _action_items(notes)

    all_notes_blob = _blob(notes).lower()
    next_steps_blob = _blob(next_steps).lower()
    actions_blob = _blob(actions).lower()

    assert str(outcome).strip(), notes
    assert actions, notes
    assert "validate" in actions_blob, notes
    assert "meeting 81" in actions_blob or "product meeting" in actions_blob, notes
    assert "validate" in next_steps_blob or "fresh product meeting" in next_steps_blob, notes

    assert "good morning" not in all_notes_blob
    assert "verify the duration, third" not in all_notes_blob


def test_meeting86_non_meeting_safety_gate() -> None:
    transcript = (FIXTURES / "meeting86_narrative_excerpt.txt").read_text()
    notes = _generate_notes_from_transcript(transcript)

    next_steps = _get_nested(notes, "summary_slots.next_steps", []) or notes.get("next_steps", [])
    decisions = _decision_items(notes)
    actions = _action_items(notes)

    assert decisions == [], notes
    assert actions == [], notes
    assert _as_list(next_steps) == [], notes
