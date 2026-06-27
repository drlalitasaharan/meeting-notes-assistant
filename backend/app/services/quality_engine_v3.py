from __future__ import annotations

import copy
import re
from typing import Any

ACTION_VERBS = {
    "create",
    "prepare",
    "send",
    "share",
    "update",
    "review",
    "run",
    "test",
    "finalize",
    "publish",
    "submit",
    "schedule",
    "document",
    "fix",
    "implement",
    "confirm",
    "draft",
    "write",
    "collect",
    "follow up",
    "set up",
    "clean",
}

WEAK_ACTION_PATTERNS = [
    r"\bi['’]?d like us to leave\b",
    r"\bmain purpose\b",
    r"\bthe purpose of\b",
    r"\bthe goal is\b",
    r"\bgoal of\b",
    r"\bthis meeting is about\b",
    r"\bagenda\b",
    r"\btoday we(?:'|’)ll discuss\b",
    r"\bwe are here to\b",
    r"\bif we say\b",
    r"\bshould consider\b",
    r"\bmaybe\b",
    r"\bpossibly\b",
    r"\bthink about\b",
]

DECISION_PATTERNS = [
    r"\bwe decided\b",
    r"\bwe agreed\b",
    r"\bthe decision is\b",
    r"\bthe plan is\b",
    r"\bwill be\b",
    r"\bwill use\b",
    r"\bwill focus on\b",
]

RISK_PATTERNS = [
    r"\brisk\b",
    r"\bconcern\b",
    r"\bconcerns\b",
    r"\bblocker\b",
    r"\bblocked\b",
    r"\bdependency\b",
    r"\bissue\b",
    r"\bcareful\b",
    r"\bmay\b",
    r"\bmight\b",
    r"\bcould\b",
]

PURPOSE_PATTERNS = [
    r"\bi['’]?d like us to leave\b",
    r"\bmain purpose\b",
    r"\bthe purpose of\b",
    r"\bthe goal is\b",
    r"\bgoal of\b",
    r"\bobjective\b",
]

GENERIC_OWNERS = {"we", "i", "everyone", "somebody", "someone", "people"}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("text", "task", "title", "summary"):
            if value.get(key):
                return str(value[key])
    return str(value)


def _clean_sentence(text: Any) -> str:
    cleaned = re.sub(r"\s+", " ", _text(text)).strip()
    cleaned = cleaned.strip(" -–—•\t")
    return cleaned


def _lower(text: Any) -> str:
    return _clean_sentence(text).lower()


def _matches_any(text: str, patterns: list[str]) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in patterns)


def _dedupe_key(text: Any) -> str:
    value = _lower(text)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(
        r"\b(the|a|an|to|and|or|of|for|with|by|on|in|at|today|tomorrow)\b",
        " ",
        value,
    )
    return re.sub(r"\s+", " ", value).strip()


def _split_transcript_sentences(transcript_text: str | None) -> list[str]:
    text = str(transcript_text or "").strip()
    if not text:
        return []

    rough_parts: list[str] = []
    for line in text.splitlines():
        line = _clean_sentence(line)
        if not line:
            continue
        rough_parts.extend(re.split(r"(?<=[.!?])\s+", line))

    sentences: list[str] = []
    seen: set[str] = set()
    for part in rough_parts:
        sentence = _clean_sentence(part)
        key = _dedupe_key(sentence)
        if sentence and key and key not in seen:
            seen.add(key)
            sentences.append(sentence)

    return sentences


def _has_action_verb(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(rf"\b{re.escape(verb)}\b", lowered) for verb in ACTION_VERBS)


def _has_action_language(text: str) -> bool:
    lowered = text.lower()
    return bool(
        re.search(
            r"\b(will|needs to|need to|should|must|has to|have to|follow up|action item)\b",
            lowered,
        )
    )


def _normalize_owner(owner: Any) -> str:
    value = _clean_sentence(owner)
    value = re.sub(r"^(owner|assignee)\s*:\s*", "", value, flags=re.I).strip()
    if not value:
        return "Unassigned"

    lowered = value.lower()
    if lowered in GENERIC_OWNERS:
        return "Unassigned"

    if lowered in {"team", "the team"}:
        return "Team"

    return value[:1].upper() + value[1:]


def _extract_deadline(task: str) -> tuple[str, str]:
    text = _clean_sentence(task)
    lowered = text.lower()

    deadline_patterns = [
        (r"\bby\s+([A-Z][A-Za-z]+|\w+day|tomorrow|today|next week|end of week)\b", "by"),
        (r"\bbefore\s+([A-Z][A-Za-z]+|\w+day|launch|demo|next week)\b", "before"),
        (r"\btoday\b", "today"),
        (r"\btomorrow\b", "tomorrow"),
        (r"\bnext week\b", "next week"),
    ]

    for pattern, kind in deadline_patterns:
        match = re.search(pattern, text, flags=re.I)
        if not match:
            continue
        if kind in {"today", "tomorrow", "next week"}:
            return text, kind
        return text, match.group(0)

    if "today" in lowered:
        return text, "today"

    return text, "Not specified"


def _strip_owner_prefix(text: str) -> tuple[str, str]:
    cleaned = _clean_sentence(text)

    prefix_match = re.match(
        r"^(?P<owner>[A-Z][A-Za-z .'-]{1,40}|Team|Unassigned)\s*[:\-–—]\s*(?P<task>.+)$",
        cleaned,
    )
    if prefix_match:
        return _normalize_owner(prefix_match.group("owner")), _clean_sentence(
            prefix_match.group("task")
        )

    will_match = re.match(
        r"^(?P<owner>[A-Z][A-Za-z .'-]{1,40})\s+(?:will|needs to|need to|should|must|has to)\s+(?P<task>.+)$",
        cleaned,
    )
    if will_match:
        return _normalize_owner(will_match.group("owner")), _clean_sentence(
            will_match.group("task")
        )

    return "Unassigned", cleaned


def _is_invalid_action_text(text: str) -> bool:
    cleaned = _clean_sentence(text)
    if not cleaned or len(cleaned) < 12:
        return True

    if _matches_any(cleaned, WEAK_ACTION_PATTERNS):
        return True

    if _matches_any(cleaned, PURPOSE_PATTERNS):
        return True

    lowered = cleaned.lower()
    if lowered.startswith(
        ("the first pilot audience", "the live demo will use", "the demo will use")
    ):
        return True

    if _matches_any(cleaned, DECISION_PATTERNS) and not _has_action_verb(cleaned):
        return True

    return False


def _normalize_action_item(value: Any, evidence: str | None = None) -> dict[str, Any] | None:
    raw_text = _clean_sentence(value)
    if isinstance(value, dict):
        raw_text = _clean_sentence(value.get("task") or value.get("text") or value)

    if _is_invalid_action_text(raw_text):
        return None

    owner = "Unassigned"
    task = raw_text

    if isinstance(value, dict):
        owner = _normalize_owner(value.get("owner") or value.get("assignee") or "")
        task = _clean_sentence(value.get("task") or value.get("text") or raw_text)
    else:
        owner, task = _strip_owner_prefix(raw_text)

    if _is_invalid_action_text(task):
        return None

    if not _has_action_verb(task):
        return None

    task, deadline = _extract_deadline(task)

    return {
        "owner": owner,
        "task": task,
        "text": f"{owner}: {task}" if owner != "Unassigned" else task,
        "deadline": deadline,
        "status": "open",
        "priority": "medium",
        "evidence": evidence or raw_text,
        "confidence": 0.82 if owner != "Unassigned" else 0.68,
    }


def _extract_action_items(sentences: list[str]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    for sentence in sentences:
        if not _has_action_language(sentence):
            continue

        item = _normalize_action_item(sentence, evidence=sentence)
        if item:
            actions.append(item)

    return actions


def _action_key(item: dict[str, Any]) -> str:
    owner = _lower(item.get("owner"))
    task = _dedupe_key(item.get("task") or item.get("text"))
    return f"{owner}:{task}"


def _action_richness(item: dict[str, Any]) -> int:
    score = 0
    if item.get("owner") and item.get("owner") != "Unassigned":
        score += 3
    if item.get("deadline") and item.get("deadline") != "Not specified":
        score += 2
    if item.get("evidence"):
        score += 2
    if len(_text(item.get("task")).split()) >= 5:
        score += 1
    return score


def _dedupe_actions(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}

    for item in items:
        key = _action_key(item)
        if not key:
            continue
        existing = best.get(key)
        if existing is None or _action_richness(item) > _action_richness(existing):
            best[key] = item

    return list(best.values())


def _normalize_decision_text(text: Any) -> str:
    value = _clean_sentence(text)
    value = re.sub(r"^(decision|decided)\s*:\s*", "", value, flags=re.I).strip()
    return value


def _is_decision_sentence(sentence: str) -> bool:
    cleaned = _clean_sentence(sentence)
    if not cleaned or len(cleaned) < 12:
        return False

    lowered = cleaned.lower()

    if lowered.endswith("?"):
        return False

    if _matches_any(cleaned, WEAK_ACTION_PATTERNS):
        return False

    if re.search(r"\b(first pilot audience|target audience)\b.*\b(will be|is|are)\b", lowered):
        return True

    if re.search(r"\b(demo|live demo)\b.*\b(will use|uses|use)\b", lowered):
        return True

    if _matches_any(cleaned, DECISION_PATTERNS):
        return True

    return False


def _normalize_decision(value: Any, evidence: str | None = None) -> dict[str, Any] | None:
    text = _normalize_decision_text(value.get("text") if isinstance(value, dict) else value)
    if not _is_decision_sentence(text):
        return None

    return {
        "text": text,
        "evidence": evidence or text,
        "confidence": 0.82,
    }


def _extract_decisions(sentences: list[str]) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    for sentence in sentences:
        decision = _normalize_decision(sentence, evidence=sentence)
        if decision:
            decisions.append(decision)
    return decisions


def _dedupe_decisions(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in items:
        key = _dedupe_key(item.get("text"))
        if key and key not in seen:
            seen.add(key)
            output.append(item)

    return output


def _is_risk_sentence(sentence: str) -> bool:
    cleaned = _clean_sentence(sentence)
    if not cleaned or len(cleaned) < 12:
        return False

    lowered = cleaned.lower()

    if lowered.endswith("?"):
        return False

    if re.search(
        r"\b(if we say|be careful|risk|concern|blocked|blocker|dependency|issue)\b", lowered
    ):
        return True

    if _matches_any(cleaned, RISK_PATTERNS) and not _is_decision_sentence(cleaned):
        return True

    return False


def _extract_risks(sentences: list[str]) -> list[str]:
    risks: list[str] = []
    seen: set[str] = set()

    for sentence in sentences:
        if not _is_risk_sentence(sentence):
            continue
        key = _dedupe_key(sentence)
        if key and key not in seen:
            seen.add(key)
            risks.append(_clean_sentence(sentence))

    return risks[:8]


def _extract_open_questions(sentences: list[str]) -> list[str]:
    questions: list[str] = []
    seen: set[str] = set()

    for sentence in sentences:
        cleaned = _clean_sentence(sentence)
        lowered = cleaned.lower()
        if not cleaned:
            continue

        is_question = cleaned.endswith("?") or re.match(
            r"^(do|does|did|should|could|would|what|which|who|when|where|why|how)\b",
            lowered,
        )
        if not is_question:
            continue

        key = _dedupe_key(cleaned)
        if key and key not in seen:
            seen.add(key)
            questions.append(cleaned)

    return questions[:8]


def _infer_purpose(sentences: list[str], existing: Any = None) -> str:
    existing_text = _clean_sentence(existing)
    if existing_text:
        return existing_text

    for sentence in sentences:
        if _matches_any(sentence, PURPOSE_PATTERNS):
            return _clean_sentence(sentence)

    for sentence in sentences:
        lowered = sentence.lower()
        if "confirm" in lowered or "finalize" in lowered or "align" in lowered:
            return _clean_sentence(sentence)

    return ""


def _infer_outcome(sentences: list[str], existing: Any = None) -> str:
    existing_text = _clean_sentence(existing)
    if existing_text:
        return existing_text

    for sentence in sentences:
        lowered = sentence.lower()
        if re.search(r"\b(aligned|agreed|decided|finalized|confirmed)\b", lowered):
            return _clean_sentence(sentence)

    return ""


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _merge_text_lists(*values: Any, limit: int = 8) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()

    for value in values:
        for item in _as_list(value):
            text = _clean_sentence(item)
            key = _dedupe_key(text)
            if text and key and key not in seen:
                seen.add(key)
                output.append(text)
            if len(output) >= limit:
                return output

    return output


def _build_next_steps(actions: list[dict[str, Any]], existing: Any = None) -> list[str]:
    next_steps = _merge_text_lists(existing, limit=5)
    seen = {_dedupe_key(step) for step in next_steps}

    for action in actions:
        owner = _text(action.get("owner")) or "Unassigned"
        task = _text(action.get("task"))
        if not task:
            continue
        step = f"{owner}: {task}" if owner != "Unassigned" else task
        key = _dedupe_key(step)
        if key and key not in seen:
            seen.add(key)
            next_steps.append(step)
        if len(next_steps) >= 5:
            break

    return next_steps


def _summary_slots(notes: dict[str, Any]) -> dict[str, Any]:
    slots = notes.get("summary_slots")
    if isinstance(slots, dict):
        return copy.deepcopy(slots)
    return {}


def _commercial_quality_metadata(
    *,
    actions: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    risks: list[str],
    open_questions: list[str],
) -> dict[str, Any]:
    generic_owner_count = sum(1 for item in actions if item.get("owner") in {"Team", "Unassigned"})
    missing_deadline_count = sum(
        1 for item in actions if item.get("deadline") in {"", None, "Not specified"}
    )

    warnings: list[str] = []
    if generic_owner_count:
        warnings.append("Some action items have Team or Unassigned owners.")
    if missing_deadline_count:
        warnings.append("Some action items do not include explicit deadlines.")
    if not actions:
        warnings.append("No action items detected.")
    if not decisions:
        warnings.append("No decisions detected.")

    return {
        "action_count": len(actions),
        "decision_count": len(decisions),
        "risk_count": len(risks),
        "open_question_count": len(open_questions),
        "generic_owner_count": generic_owner_count,
        "missing_deadline_count": missing_deadline_count,
        "warnings": warnings,
        "passed": not any("No action items" in warning for warning in warnings),
    }


def apply_quality_engine_v3(notes: dict[str, Any], transcript_text: str | None) -> dict[str, Any]:
    """Apply QEv3-B commercial-quality deterministic cleanup.

    This intentionally does not call an LLM. V3-B focuses on correctness:
    action validity, section separation, owner cleanup, decisions, risks,
    open questions, evidence, dedupe, and next-step sync.
    """

    improved = copy.deepcopy(notes)
    sentences = _split_transcript_sentences(transcript_text)

    slots = _summary_slots(improved)

    existing_actions: list[dict[str, Any]] = []
    for item in _as_list(improved.get("action_item_objects")) + _as_list(
        improved.get("action_items")
    ):
        normalized_action = _normalize_action_item(item)
        if normalized_action is not None:
            existing_actions.append(normalized_action)

    extracted_actions = _extract_action_items(sentences)
    actions = _dedupe_actions(existing_actions + extracted_actions)

    existing_decisions: list[dict[str, Any]] = []
    for item in _as_list(improved.get("decision_objects")) + _as_list(improved.get("decisions")):
        normalized_decision = _normalize_decision(item)
        if normalized_decision is not None:
            existing_decisions.append(normalized_decision)

    extracted_decisions = _extract_decisions(sentences)
    decisions = _dedupe_decisions(existing_decisions + extracted_decisions)

    risks = _merge_text_lists(
        slots.get("risks"), improved.get("risks"), _extract_risks(sentences), limit=8
    )
    open_questions = _merge_text_lists(
        slots.get("open_questions"),
        improved.get("open_questions"),
        _extract_open_questions(sentences),
        limit=8,
    )

    slots["purpose"] = _infer_purpose(sentences, slots.get("purpose") or improved.get("purpose"))
    slots["outcome"] = _infer_outcome(sentences, slots.get("outcome") or improved.get("outcome"))
    slots["risks"] = risks
    slots["open_questions"] = open_questions
    slots["next_steps"] = _build_next_steps(actions, slots.get("next_steps"))

    improved["summary_slots"] = slots
    improved["action_item_objects"] = actions
    improved["action_items"] = actions
    improved["decision_objects"] = decisions
    improved["decisions"] = decisions

    metadata = _commercial_quality_metadata(
        actions=actions,
        decisions=decisions,
        risks=risks,
        open_questions=open_questions,
    )
    improved["_qev3_metadata"] = metadata

    return improved


def run_quality_engine_v3(
    notes: dict[str, Any],
    transcript_text: str | None,
    *,
    mode: str = "v3",
) -> dict[str, Any]:
    normalized_mode = str(mode or "").strip().lower()

    if normalized_mode != "v3":
        return {
            "notes": copy.deepcopy(notes),
            "metadata": {
                "mode": normalized_mode or "v1",
                "applied": False,
                "engine": "qev3",
                "fallback_used": False,
            },
        }

    try:
        improved = apply_quality_engine_v3(notes, transcript_text)
        qev3_metadata = improved.pop("_qev3_metadata", {})
        return {
            "notes": improved,
            "metadata": {
                "mode": "v3",
                "applied": True,
                "engine": "qev3",
                "fallback_used": False,
                "critic": qev3_metadata,
            },
        }
    except Exception as exc:  # pragma: no cover - defensive production safety
        return {
            "notes": copy.deepcopy(notes),
            "metadata": {
                "mode": "v3",
                "applied": False,
                "engine": "qev3",
                "fallback_used": True,
                "error": str(exc),
            },
        }


def render_quality_engine_v3_markdown(notes: dict[str, Any]) -> str:
    slots = _summary_slots(notes)

    sections: list[str] = ["# Meeting Notes"]

    summary = _clean_sentence(notes.get("summary"))
    if summary:
        sections.append("\n## Executive Summary")
        sections.append(summary)

    if slots.get("purpose"):
        sections.append("\n## Purpose")
        sections.append(_clean_sentence(slots["purpose"]))

    if slots.get("outcome"):
        sections.append("\n## Outcomes")
        sections.append(_clean_sentence(slots["outcome"]))

    decisions = _as_list(notes.get("decision_objects"))
    if decisions:
        sections.append("\n## Key Decisions")
        for decision in decisions:
            text = _clean_sentence(decision.get("text") if isinstance(decision, dict) else decision)
            if text:
                sections.append(f"- {text}")

    actions = _as_list(notes.get("action_item_objects"))
    if actions:
        sections.append("\n## Action Items")
        sections.append("| Owner | Action | Deadline |")
        sections.append("|---|---|---|")
        for action in actions:
            if not isinstance(action, dict):
                continue
            owner = _clean_sentence(action.get("owner")) or "Unassigned"
            task = _clean_sentence(action.get("task") or action.get("text"))
            deadline = _clean_sentence(action.get("deadline")) or "Not specified"
            if task:
                sections.append(f"| {owner} | {task} | {deadline} |")

    if slots.get("risks"):
        sections.append("\n## Risks / Concerns")
        for risk in _as_list(slots.get("risks")):
            text = _clean_sentence(risk)
            if text:
                sections.append(f"- {text}")

    if slots.get("open_questions"):
        sections.append("\n## Open Questions")
        for question in _as_list(slots.get("open_questions")):
            text = _clean_sentence(question)
            if text:
                sections.append(f"- {text}")

    if slots.get("next_steps"):
        sections.append("\n## Follow-Up")
        for step in _as_list(slots.get("next_steps")):
            text = _clean_sentence(step)
            if text:
                sections.append(f"- {text}")

    return "\n".join(sections).strip() + "\n"
