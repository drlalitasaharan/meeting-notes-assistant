from __future__ import annotations

import copy
import re
from typing import Any

KNOWN_ENTITY_VARIANTS: dict[str, tuple[str, ...]] = {
    "Acjen AI": (
        r"\ba gen\.?\s*ai\b",
        r"\bagenda\s+ai\b",
        r"\bacjenai\b",
        r"\bacjen\s+acjen\s+ai\b",
        r"\bacgen\s+ai\b",
        r"\bajencel\s+ai\b",
    ),
    "MeetIQ": (
        r"\bmeet\s+iq\b",
        r"\bmeeting\s+iq\b",
        r"\bmeetiq\.ai\b",
    ),
    "support@acjen.ai": (
        r"\bsupport\s+(?:at|\[at\])\s+acjen(?:\.|\s+dot\s+)?ai\b",
        r"\bsupport@(?:agenda|acgen|ajencel)\.ai\b",
        r"\bsupport@acjen\.(?:com|io|co)\b",
        r"\bsupport@acjenai\b",
    ),
    "PayPal": (
        r"\bpay\s+pal\b",
        r"\bpay-pal\b",
    ),
    "Square": (
        r"\bsqare\b",
        r"\bsquire\s+checkout\b",
    ),
    "Render": (r"\brendr\b",),
    "Vercel": (r"\bvercell\b",),
    "GoDaddy": (r"\bgo\s+daddy\b", r"\bgodady\b"),
    "BetaList": (r"\bbeta\s+list\b",),
    "Indie Hackers": (r"\bindiehackers\b", r"\bindy\s+hackers\b"),
    "Product Hunt": (r"\bproducthunt\b", r"\bproduct\s+hunter\b"),
    "GitHub": (r"\bgit\s+hub\b",),
    "Markdown": (r"\bmark\s+down\b",),
    "Starter": (r"\bstater\s+plan\b",),
    "Pro Pilot": (r"\bpro\s+pilate\b", r"\bpropilot\b"),
}


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
    summary_slots["open_questions"] = _merge_open_questions(
        summary_slots.get("open_questions"),
        detect_open_questions(improved, transcript_text),
    )
    summary_slots["known_entity_warnings"] = _merge_warnings(
        summary_slots.get("known_entity_warnings"),
        detect_known_entity_warnings(improved),
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


def _merge_warnings(existing: Any, new_warnings: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()

    for warning in [*(existing if isinstance(existing, list) else []), *new_warnings]:
        text = _text(warning)
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(text)

    return output


def _normalize_question(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip(" .:-")
    if not cleaned:
        return ""
    cleaned = re.sub(
        r"^(?:open|unresolved)\s+questions?\s*(?:remains?|is|are)?\s*[:\-]?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"^question\s+remains?\s*[:\-]?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"^(?:we|the team)\s+still\s+need(?:s)?\s+to\s+(?:confirm|decide|know)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    if not cleaned:
        return ""
    cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned if cleaned.endswith("?") else f"{cleaned}?"


def _looks_like_rhetorical_or_answered_question(text: str) -> bool:
    normalized = _dedupe_key(text)
    if not normalized:
        return True

    rhetorical_patterns = (
        r"\bdoes that make sense\b",
        r"\bcan you hear me\b",
        r"\bany questions\b",
        r"\bright\b",
        r"\bokay\b",
        r"\byou know\b",
        r"\bwhat do you think\b",
    )
    answered_patterns = (
        r"\balready answered\b",
        r"\banswered\b",
        r"\bresolved\b",
        r"\bconfirmed\b",
        r"\bdecided\b",
        r"\bclosed\b",
    )

    return any(re.search(pattern, normalized) for pattern in rhetorical_patterns) or any(
        re.search(pattern, normalized) for pattern in answered_patterns
    )


def _extract_open_questions_from_text(text: str) -> list[str]:
    normalized_text = _text(text)
    if not normalized_text:
        return []

    candidates: list[str] = []
    marker_patterns = (
        r"\bopen questions?\s*(?:remains?|is|are)?\s*[:\-]\s*([^.\n?]+(?:\?)?)",
        r"\bunresolved questions?\s*(?:remains?|is|are)?\s*[:\-]\s*([^.\n?]+(?:\?)?)",
        r"\bquestion remains?\s*[:\-]\s*([^.\n?]+(?:\?)?)",
        r"\b(?:we|the team)\s+still\s+need(?:s)?\s+to\s+(?:confirm|decide|know)\s+([^.\n?]+(?:\?)?)",
    )

    for pattern in marker_patterns:
        for match in re.finditer(pattern, normalized_text, flags=re.IGNORECASE):
            question = _normalize_question(match.group(1))
            if question and not _looks_like_rhetorical_or_answered_question(question):
                candidates.append(question)

    for sentence in re.split(r"(?<=[.!?])\s+|\n+", normalized_text):
        sentence = sentence.strip()
        if "?" not in sentence:
            continue
        lowered = sentence.lower()
        if not any(
            marker in lowered
            for marker in (
                "open question",
                "unresolved question",
                "question remains",
                "still need to confirm",
                "still need to decide",
                "still need to know",
            )
        ):
            continue
        question = _normalize_question(sentence)
        if question and not _looks_like_rhetorical_or_answered_question(question):
            candidates.append(question)

    return candidates


def _merge_open_questions(existing: Any, new_questions: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()

    for question in [*(existing if isinstance(existing, list) else []), *new_questions]:
        text = _normalize_question(_text(question))
        if not text or _looks_like_rhetorical_or_answered_question(text):
            continue
        key = _dedupe_key(text)
        if key in seen:
            continue
        seen.add(key)
        output.append(text)

    return output


def detect_open_questions(notes: dict[str, Any], transcript_text: str | None) -> list[str]:
    """Extract likely unresolved questions without rewriting source content."""

    sources = [_text(transcript_text), _note_text_blob(notes)]
    questions: list[str] = []
    for source in sources:
        questions.extend(_extract_open_questions_from_text(source))
    return _merge_open_questions([], questions)


def _iter_note_text_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        output: list[str] = []
        for item in value:
            output.extend(_iter_note_text_values(item))
        return output
    if isinstance(value, dict):
        output = []
        for key, item in value.items():
            if key == "known_entity_warnings":
                continue
            output.extend(_iter_note_text_values(item))
        return output
    return []


def _note_text_blob(notes: dict[str, Any]) -> str:
    fields = (
        "summary",
        "summary_slots",
        "key_points",
        "decisions",
        "decision_objects",
        "action_items",
        "action_item_objects",
    )
    texts: list[str] = []
    for field in fields:
        texts.extend(_iter_note_text_values(notes.get(field)))
    return "\n".join(text for text in texts if text.strip())


def detect_known_entity_warnings(notes: dict[str, Any]) -> list[str]:
    """Return warning-only known-entity guardrail findings.

    This function intentionally does not rewrite notes. It only flags likely
    variants/misspellings that should be reviewed before v2 output is trusted.
    """

    text_blob = _note_text_blob(notes)
    if not text_blob:
        return []

    warnings: list[str] = []
    for canonical, patterns in KNOWN_ENTITY_VARIANTS.items():
        for pattern in patterns:
            match = re.search(pattern, text_blob, flags=re.IGNORECASE)
            if match:
                warnings.append(
                    f"Possible known entity rewrite: '{match.group(0)}' may refer to '{canonical}'."
                )
                break

    return warnings


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


def run_quality_engine_v2(
    notes: dict[str, Any],
    transcript_text: str | None,
    *,
    mode: object = "v1",
) -> dict[str, Any]:
    """Run Quality Engine v2 according to mode.

    Modes:
    - v1: return original notes unchanged.
    - v2: return improved notes.
    - shadow: run v2 for comparison but return original notes unchanged.
    """

    normalized_mode = normalize_notes_engine_mode(mode)

    metadata: dict[str, Any] = {
        "applied": False,
        "mode": normalized_mode,
        "fallback_used": False,
        "warnings": [],
    }

    if normalized_mode == "v1":
        return {"notes": notes, "metadata": metadata}

    try:
        improved = apply_quality_engine_v2(notes, transcript_text)
    except Exception as exc:  # pragma: no cover - defensive production fallback
        metadata["fallback_used"] = True
        metadata["warnings"].append(f"Quality Engine v2 failed: {exc.__class__.__name__}")
        return {"notes": notes, "metadata": metadata}

    if normalized_mode == "shadow":
        metadata["shadow_ran"] = True
        metadata["shadow_summary"] = _compare_v1_v2_notes(notes, improved)
        return {"notes": notes, "metadata": metadata}

    metadata["applied"] = True
    return {"notes": improved, "metadata": metadata}


def _compare_v1_v2_notes(
    original: dict[str, Any],
    improved: dict[str, Any],
) -> dict[str, Any]:
    original_slots = original.get("summary_slots") if isinstance(original, dict) else {}
    improved_slots = improved.get("summary_slots") if isinstance(improved, dict) else {}

    if not isinstance(original_slots, dict):
        original_slots = {}
    if not isinstance(improved_slots, dict):
        improved_slots = {}

    original_purpose = _text(original_slots.get("purpose"))
    improved_purpose = _text(improved_slots.get("purpose"))

    original_actions = original.get("action_item_objects") if isinstance(original, dict) else []
    improved_actions = improved.get("action_item_objects") if isinstance(improved, dict) else []

    original_decisions = original.get("decision_objects") if isinstance(original, dict) else []
    improved_decisions = improved.get("decision_objects") if isinstance(improved, dict) else []

    return {
        "purpose_added": not bool(original_purpose) and bool(improved_purpose),
        "original_action_count": len(original_actions) if isinstance(original_actions, list) else 0,
        "improved_action_count": len(improved_actions) if isinstance(improved_actions, list) else 0,
        "original_decision_count": len(original_decisions)
        if isinstance(original_decisions, list)
        else 0,
        "improved_decision_count": len(improved_decisions)
        if isinstance(improved_decisions, list)
        else 0,
    }
