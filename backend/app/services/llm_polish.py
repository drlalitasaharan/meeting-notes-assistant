from __future__ import annotations

import copy
import json
import logging
import os
import re
from typing import Any, Callable

log = logging.getLogger(__name__)

GROQ_OPENAI_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"


def _truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    try:
        return int(str(os.getenv(name, default)).strip())
    except (TypeError, ValueError):
        return default


def llm_polish_enabled() -> bool:
    return _truthy(os.getenv("MEETIQ_LLM_POLISH_ENABLED"))


def _clean_text(value: object) -> str:
    text = str(value or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _string_list(value: object, *, limit: int = 12) -> list[str]:
    if not isinstance(value, list):
        return []

    output: list[str] = []
    seen: set[str] = set()

    for item in value:
        text = _clean_text(item)
        if not text:
            continue

        key = re.sub(r"\W+", " ", text.lower()).strip()
        if not key or key in seen:
            continue

        seen.add(key)
        output.append(text)

        if len(output) >= limit:
            break

    return output


def _build_polish_payload(notes: dict[str, Any]) -> dict[str, Any]:
    slots = notes.get("summary_slots")
    if not isinstance(slots, dict):
        slots = {}

    return {
        "summary": _clean_text(notes.get("summary")),
        "summary_slots": {
            "purpose": _clean_text(slots.get("purpose")),
            "outcome": _clean_text(slots.get("outcome")),
            "risks": _string_list(slots.get("risks"), limit=8),
        },
        "key_points": _string_list(notes.get("key_points"), limit=8),
        "decisions": _string_list(notes.get("decisions"), limit=8),
        "action_items_context_only": [
            {
                "owner": _clean_text(item.get("owner") or "Team"),
                "task": _clean_text(item.get("task") or item.get("text") or ""),
            }
            for item in notes.get("action_item_objects", []) or []
            if isinstance(item, dict) and _clean_text(item.get("task") or item.get("text") or "")
        ],
    }


def _extract_json_object(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            parsed = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            return None

    return parsed if isinstance(parsed, dict) else None


def _prompt_messages(payload: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are an expert editor for professional meeting notes. "
                "Polish wording only. Do not invent facts. Do not add action items. "
                "Do not remove concrete decisions. Preserve the same JSON structure. "
                "Return JSON only."
            ),
        },
        {
            "role": "user",
            "content": (
                "Polish these already-extracted meeting notes. "
                "Improve clarity, concision, executive tone, and readability. "
                "Keep action_items_context_only as context only and do not return it. "
                "Return JSON with exactly these keys: summary, summary_slots, key_points, decisions. "
                "summary_slots may contain only purpose, outcome, and risks.\n\n"
                f"{json.dumps(payload, ensure_ascii=False)}"
            ),
        },
    ]


def _call_groq_polish(payload: dict[str, Any]) -> dict[str, Any] | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        log.warning("llm_polish: skipped missing GROQ_API_KEY")
        return None

    provider = str(os.getenv("MEETIQ_LLM_PROVIDER") or "groq").strip().lower()
    if provider != "groq":
        log.warning(
            "llm_polish: skipped unsupported provider",
            extra={"llm_polish_provider": provider},
        )
        return None

    max_input_tokens = _int_env("MEETIQ_LLM_POLISH_MAX_INPUT_TOKENS", 8000)
    payload_text = json.dumps(payload, ensure_ascii=False)
    payload_chars = len(payload_text)
    if payload_chars > max_input_tokens * 4:
        log.warning(
            "llm_polish: skipped payload too large",
            extra={
                "llm_polish_payload_chars": payload_chars,
                "llm_polish_max_input_tokens": max_input_tokens,
            },
        )
        return None

    timeout_seconds = _int_env("MEETIQ_LLM_POLISH_TIMEOUT_SECONDS", 20)
    model = (
        os.getenv("MEETIQ_LLM_POLISH_MODEL") or os.getenv("MEETIQ_LLM_MODEL") or DEFAULT_GROQ_MODEL
    )

    log.warning(
        "llm_polish: groq request starting",
        extra={
            "llm_polish_provider": provider,
            "llm_polish_model": model,
            "llm_polish_timeout_seconds": timeout_seconds,
            "llm_polish_payload_chars": payload_chars,
        },
    )

    from openai import OpenAI

    client = OpenAI(
        api_key=api_key,
        base_url=GROQ_OPENAI_BASE_URL,
        timeout=timeout_seconds,
        max_retries=0,
    )

    response: Any = client.chat.completions.create(
        model=model,
        messages=_prompt_messages(payload),
        temperature=0.1,
        max_tokens=1400,
    )

    content = ""
    try:
        content = str(response.choices[0].message.content or "")
    except (AttributeError, IndexError, TypeError):
        log.warning("llm_polish: skipped empty or malformed Groq response")
        return None

    if not content.strip():
        log.warning("llm_polish: skipped empty Groq response content")
        return None

    parsed = _extract_json_object(content)
    if parsed is None:
        log.warning(
            "llm_polish: skipped invalid JSON response",
            extra={"llm_polish_response_chars": len(content)},
        )
        return None

    log.warning(
        "llm_polish: groq response parsed",
        extra={"llm_polish_response_chars": len(content)},
    )
    return parsed


def _same_length_polished_list(
    *,
    original: list[str],
    polished: object,
    limit: int,
) -> list[str] | None:
    candidate = _string_list(polished, limit=limit)
    if not original:
        return None

    if len(candidate) != len(original):
        return None

    return candidate


def _visible_polish_changed(
    original_notes: dict[str, Any],
    polished_notes: dict[str, Any],
) -> bool:
    original_slots = original_notes.get("summary_slots")
    polished_slots = polished_notes.get("summary_slots")

    if not isinstance(original_slots, dict):
        original_slots = {}
    if not isinstance(polished_slots, dict):
        polished_slots = {}

    fields_to_compare = (
        ("summary", original_notes.get("summary"), polished_notes.get("summary")),
        ("key_points", original_notes.get("key_points"), polished_notes.get("key_points")),
        ("decisions", original_notes.get("decisions"), polished_notes.get("decisions")),
        ("purpose", original_slots.get("purpose"), polished_slots.get("purpose")),
        ("outcome", original_slots.get("outcome"), polished_slots.get("outcome")),
        ("risks", original_slots.get("risks"), polished_slots.get("risks")),
    )

    return any(original != polished for _, original, polished in fields_to_compare)


def _merge_polished_notes(
    original_notes: dict[str, Any],
    polished: dict[str, Any],
) -> dict[str, Any]:
    output = copy.deepcopy(original_notes)

    original_slots = output.get("summary_slots")
    slots = dict(original_slots) if isinstance(original_slots, dict) else {}

    summary = _clean_text(polished.get("summary"))
    if 40 <= len(summary) <= 1800:
        output["summary"] = summary

    polished_slots = polished.get("summary_slots")
    if isinstance(polished_slots, dict):
        purpose = _clean_text(polished_slots.get("purpose"))
        if 12 <= len(purpose) <= 900:
            slots["purpose"] = purpose

        outcome = _clean_text(polished_slots.get("outcome"))
        if 12 <= len(outcome) <= 900:
            slots["outcome"] = outcome

        original_risks = _string_list(slots.get("risks"), limit=8)
        polished_risks = _same_length_polished_list(
            original=original_risks,
            polished=polished_slots.get("risks"),
            limit=8,
        )
        if polished_risks is not None:
            slots["risks"] = polished_risks

    output["summary_slots"] = slots

    original_key_points = _string_list(output.get("key_points"), limit=8)
    polished_key_points = _same_length_polished_list(
        original=original_key_points,
        polished=polished.get("key_points"),
        limit=8,
    )
    if polished_key_points is not None:
        output["key_points"] = polished_key_points

    original_decisions = _string_list(output.get("decisions"), limit=8)
    polished_decisions = _same_length_polished_list(
        original=original_decisions,
        polished=polished.get("decisions"),
        limit=8,
    )
    if polished_decisions is not None:
        output["decisions"] = polished_decisions

    # Locked deterministic fields: the LLM must not create, remove, or reorder actions/next steps.
    output["action_items"] = copy.deepcopy(original_notes.get("action_items") or [])
    output["action_item_objects"] = copy.deepcopy(original_notes.get("action_item_objects") or [])
    locked_slots = output.get("summary_slots")
    if isinstance(locked_slots, dict):
        original_locked_slots = original_notes.get("summary_slots")
        if isinstance(original_locked_slots, dict):
            for key in ("next_steps", "open_questions", "known_entity_warnings"):
                if key in original_locked_slots:
                    locked_slots[key] = copy.deepcopy(original_locked_slots.get(key))
        output["summary_slots"] = locked_slots

    return output


def apply_llm_polish_to_notes(
    notes: dict[str, Any],
    *,
    polish_client: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None,
) -> dict[str, Any]:
    """Optionally polish structured notes with an LLM.

    This is intentionally fail-closed: disabled config, missing keys, timeouts,
    invalid JSON, and schema mismatches all return the original notes unchanged.
    """

    original = copy.deepcopy(notes)

    if not llm_polish_enabled():
        log.warning("llm_polish: skipped disabled")
        return original

    provider = str(os.getenv("MEETIQ_LLM_PROVIDER") or "groq").strip().lower()
    model = (
        os.getenv("MEETIQ_LLM_POLISH_MODEL") or os.getenv("MEETIQ_LLM_MODEL") or DEFAULT_GROQ_MODEL
    )
    log.warning(
        "llm_polish: enabled",
        extra={
            "llm_polish_provider": provider,
            "llm_polish_model": model,
        },
    )

    try:
        payload = _build_polish_payload(original)
        polished = (
            polish_client(payload) if polish_client is not None else _call_groq_polish(payload)
        )
        if not isinstance(polished, dict):
            log.warning("llm_polish: skipped no valid polish payload")
            return original

        merged = _merge_polished_notes(original, polished)
        if not _visible_polish_changed(original, merged):
            log.warning("llm_polish: skipped no visible changes after merge")
            return original

        merged["_llm_polish_applied"] = True
        log.warning(
            "llm_polish: applied successfully",
            extra={
                "llm_polish_provider": provider,
                "llm_polish_model": model,
            },
        )
        return merged
    except Exception:
        log.exception("llm_polish: failed; falling back to deterministic notes")
        if _truthy(os.getenv("MEETIQ_LLM_POLISH_FALLBACK_ON_ERROR", "true")):
            return original
        return original
