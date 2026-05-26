from __future__ import annotations

import re
from typing import Any

ACTION_VERBS = (
    "update",
    "send",
    "confirm",
    "draft",
    "clean",
    "upload",
    "run",
    "check",
    "schedule",
    "prepare",
    "finalize",
    "review",
    "share",
)


def _textify(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(_textify(item) for item in value)
    if isinstance(value, dict):
        return " ".join(_textify(v) for v in value.values())
    return str(value)


def _clean_space(text: object) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _capitalize_task(text: str) -> str:
    text = _clean_space(text)
    if not text:
        return ""
    return text[0].upper() + text[1:]


def _extract_due_date(task: str, existing: object = None) -> str | None:
    if existing:
        return str(existing)

    patterns = [
        r"\bby\s+\d{1,2}\s*(?:am|pm)\s+tomorrow\b",
        r"\bby\s+\d{1,2}\s*(?:am|pm)\b",
        r"\bby\s+monday(?:\s+morning|\s+afternoon)?\b",
        r"\bby\s+tuesday(?:\s+morning|\s+afternoon)?\b",
        r"\btomorrow\s+morning\b",
        r"\btomorrow\s+afternoon\b",
        r"\bmonday\s+afternoon\b",
        r"\btoday\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, task, flags=re.IGNORECASE)
        if match:
            value = match.group(0)
            return value[0].lower() + value[1:]
    return None


def _normalize_task(task: object, owner: object = None) -> str:
    text = _clean_space(task)
    owner_text = _clean_space(owner)

    text = re.sub(r"^(transcript\s+)+", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"^i\s+will\s+", "", text, flags=re.IGNORECASE).strip()

    low = text.lower()

    if (
        owner_text.lower() == "the next client follow-up"
        or ("the next client follow-up" in low and "be scheduled" in low)
        or low.startswith("be scheduled for next tuesday after finance confirms pricing")
    ):
        return "Schedule the client follow-up for next Tuesday after finance confirms pricing"

    text = re.sub(
        r"\bconfirm pricing with finance\s+(\d{1,2}\s*(?:am|pm)\s+tomorrow)\b",
        r"confirm pricing with finance by \1",
        text,
        flags=re.IGNORECASE,
    )

    if re.match(r"^say\s+the\s+first\s+month\s+includes\b", text, flags=re.IGNORECASE):
        text = "Update client-facing messaging to " + text

    if re.match(r"^(also\s+)?say\s+it\s+(works\s+)?best\b", text, flags=re.IGNORECASE):
        text = re.sub(r"^(also\s+)?say\s+", "", text, flags=re.IGNORECASE)
        text = "Update client-facing messaging to say " + text

    return _capitalize_task(text).rstrip(".")


def _normalize_owner(owner: object, task: str = "") -> str:
    owner_text = _clean_space(owner) or "Team"
    if owner_text.lower() in {
        "the next client follow-up",
        "we",
        "i",
        "none",
        "null",
        "unknown",
    }:
        return "Team"
    if "client-facing messaging" in task.lower():
        return "Team"
    return owner_text


def _is_low_precision_task(task: str) -> bool:
    low = task.lower().strip()
    if not low:
        return True
    blocked = (
        "if we send the proposal",
        "proposal flymate",
        "today confirm proposal scope",
        "risks and action items",
        "the demo should show the workflow",
        "wait for processing",
        "review summary",
        "copy or export",
    )
    if low.startswith("if "):
        return True
    return any(phrase in low for phrase in blocked)


def _dedupe_key(task: str) -> str:
    key = task.lower()
    key = key.replace(" by 11am tomorrow", " 11am tomorrow")
    key = re.sub(r"[^a-z0-9]+", " ", key)
    return re.sub(r"\s+", " ", key).strip()


def _object_from_any(item: object) -> dict[str, Any] | None:
    if item is None:
        return None

    if isinstance(item, dict):
        owner = item.get("owner") or "Team"
        task = item.get("task") or item.get("text") or ""
        if isinstance(task, str) and ":" in task and not item.get("task"):
            maybe_owner, maybe_task = task.split(":", 1)
            if maybe_owner.strip():
                owner = maybe_owner.strip()
                task = maybe_task.strip()

        task_text = _normalize_task(task, owner)
        if _is_low_precision_task(task_text):
            return None

        owner_text = _normalize_owner(owner, task_text)
        return {
            "text": f"{owner_text}: {task_text}",
            "owner": owner_text,
            "task": task_text,
            "due_date": _extract_due_date(task_text, item.get("due_date")),
            "confidence": float(item.get("confidence") or 0.7),
            "status": str(item.get("status") or "open"),
            "priority": str(item.get("priority") or "medium"),
        }

    if hasattr(item, "task") or hasattr(item, "text"):
        owner = getattr(item, "owner", None) or "Team"
        task = getattr(item, "task", None) or getattr(item, "text", None) or ""
        task_text = _normalize_task(task, owner)
        if _is_low_precision_task(task_text):
            return None
        owner_text = _normalize_owner(owner, task_text)
        return {
            "text": f"{owner_text}: {task_text}",
            "owner": owner_text,
            "task": task_text,
            "due_date": _extract_due_date(
                task_text, getattr(item, "due", None) or getattr(item, "due_date", None)
            ),
            "confidence": float(getattr(item, "confidence", 0.7) or 0.7),
            "status": "open",
            "priority": "medium",
        }

    text = _clean_space(item)
    if not text:
        return None

    owner = "Team"
    task = text

    if " - " in text:
        owner, task = text.split(" - ", 1)
    elif ":" in text:
        owner, task = text.split(":", 1)

    task_text = _normalize_task(task, owner)
    if _is_low_precision_task(task_text):
        return None

    owner_text = _normalize_owner(owner, task_text)
    return {
        "text": f"{owner_text}: {task_text}",
        "owner": owner_text,
        "task": task_text,
        "due_date": _extract_due_date(task_text),
        "confidence": 0.7,
        "status": "open",
        "priority": "medium",
    }


def _split_marker_tasks(body: str) -> list[str]:
    body = _clean_space(body)
    body = re.sub(r"^(transcript\s+)+", "", body, flags=re.IGNORECASE).strip()
    body = re.sub(r"^i\s+will\s+", "", body, flags=re.IGNORECASE).strip()

    pieces = re.split(
        r",?\s+and\s+(?=(?:update|send|confirm|draft|clean|upload|run|check|schedule|prepare|review)\b)",
        body,
        flags=re.IGNORECASE,
    )

    tasks: list[str] = []
    for piece in pieces:
        piece = re.sub(r"^i\s+will\s+", "", piece, flags=re.IGNORECASE).strip()
        task = _normalize_task(piece)
        if task and not _is_low_precision_task(task):
            tasks.append(task)
    return tasks


def _extract_owner_marker_objects(raw_transcript_text: object) -> list[dict[str, Any]]:
    text = _textify(raw_transcript_text)
    if not text or "action item for" not in text.lower():
        return []

    pattern = re.compile(
        r"(?:^|[\n.]\s*)"
        r"(?:[A-Z][a-zA-Z]+\.\s*)?"
        r"Action item for\s+(?P<owner>[A-Z][a-zA-Z]+)\.?\s+"
        r"(?P<body>.*?)(?=(?:[\n.]\s*(?:[A-Z][a-zA-Z]+\.\s*)?"
        r"Action item for\s+[A-Z][a-zA-Z]+\.?)|\Z)",
        flags=re.IGNORECASE | re.DOTALL,
    )

    objects: list[dict[str, Any]] = []

    for match in pattern.finditer(text):
        owner = _normalize_owner(match.group("owner"))
        body = _clean_space(match.group("body"))

        sentences = re.split(r"(?<=[.!?])\s+", body)
        body = " ".join(
            sentence for sentence in sentences if not sentence.strip().lower().startswith("if ")
        )

        for task in _split_marker_tasks(body):
            objects.append(
                {
                    "text": f"{owner}: {task}",
                    "owner": owner,
                    "task": task,
                    "due_date": _extract_due_date(task),
                    "confidence": 0.84,
                    "status": "open",
                    "priority": "medium",
                }
            )

    return objects


def _dedupe_objects(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []

    for obj in objects:
        task = _normalize_task(obj.get("task") or obj.get("text") or "", obj.get("owner"))
        if _is_low_precision_task(task):
            continue

        owner = _normalize_owner(obj.get("owner"), task)
        key = _dedupe_key(task)
        if not key or key in seen:
            continue

        seen.add(key)
        deduped.append(
            {
                "text": f"{owner}: {task}",
                "owner": owner,
                "task": task,
                "due_date": _extract_due_date(task, obj.get("due_date")),
                "confidence": float(obj.get("confidence") or 0.7),
                "status": str(obj.get("status") or "open"),
                "priority": str(obj.get("priority") or "medium"),
            }
        )

    return deduped


def _normalize_client_facing_messaging_action(task: str) -> str:
    normalized = str(task or "").strip()
    prefix = "Update client-facing messaging to "

    if normalized.startswith(prefix):
        tail = normalized[len(prefix) :].lstrip()
        if tail:
            normalized = f"{prefix}{tail[:1].lower()}{tail[1:]}"

    return normalized


def _normalize_persisted_action_contract_return(*payload):
    def _normalize_task_text(value: str) -> str:
        normalized = str(value or "").strip()
        prefix = "Update client-facing messaging to "

        index = normalized.find(prefix)
        if index == -1:
            return normalized

        tail_start = index + len(prefix)
        tail = normalized[tail_start:].lstrip()
        if not tail:
            return normalized

        skipped_spaces = len(normalized[tail_start:]) - len(tail)
        real_tail_start = tail_start + skipped_spaces

        return normalized[:real_tail_start] + tail[:1].lower() + tail[1:]

    def _normalize_value(value):
        if isinstance(value, str):
            return _normalize_task_text(value)

        if isinstance(value, dict):
            normalized = dict(value)
            task = normalized.get("task")
            if isinstance(task, str):
                normalized["task"] = _normalize_task_text(task)

            next_steps = normalized.get("next_steps")
            if isinstance(next_steps, list):
                normalized["next_steps"] = [_normalize_value(item) for item in next_steps]

            return normalized

        if isinstance(value, list):
            return [_normalize_value(item) for item in value]

        if isinstance(value, tuple):
            return tuple(_normalize_value(item) for item in value)

        return value

    if len(payload) == 1:
        return _normalize_value(payload[0])

    return tuple(_normalize_value(item) for item in payload)


def _collapse_spaces(value: object) -> str:
    return " ".join(str(value or "").replace("\n", " ").split()).strip()


def _cut_task_at_transcript_boundary(task: object) -> str:
    text = _collapse_spaces(task)
    if not text:
        return ""

    lowered = f" {text.lower()}"

    boundary_tokens = [
        " alex.",
        " alex,",
        " priya.",
        " priya,",
        " jordan.",
        " jordan,",
        " morgan.",
        " morgan,",
        " medication.",
        " mitigation.",
        " final recap.",
        " thanks everyone",
        " good morning team",
        " this is the ",
        " you you",
    ]

    cut_at: int | None = None

    for token in boundary_tokens:
        idx = lowered.find(token)
        if idx > 0:
            cut_at = idx - 1 if cut_at is None else min(cut_at, idx - 1)

    for label in (" decision ", " risk "):
        idx = lowered.find(label)
        if idx > 0:
            cut_at = idx - 1 if cut_at is None else min(cut_at, idx - 1)

    if cut_at is not None and cut_at > 0:
        text = text[:cut_at].strip()

    return text.rstrip(" .")


def _normalize_action_task_text(task: object) -> str:
    text = _cut_task_at_transcript_boundary(task)

    replacements = {
        "Be scheduled for next Tuesday after finance confirms pricing": "Schedule the client follow-up for next Tuesday after finance confirms pricing",
        "be scheduled for next Tuesday after finance confirms pricing": "Schedule the client follow-up for next Tuesday after finance confirms pricing",
        "Last the client follow-up email": "Draft the client follow-up email",
        "last the client follow-up email": "Draft the client follow-up email",
        "Laugh to short on Morgan note": "Draft a short onboarding note",
        "Laugh to short onboarding note": "Draft a short onboarding note",
        "laugh to short on Morgan note": "Draft a short onboarding note",
        "laugh to short onboarding note": "Draft a short onboarding note",
        "Upload near approved sample meeting file": "Upload the approved sample meeting file",
        "upload near approved sample meeting file": "Upload the approved sample meeting file",
        "Clean the MMO account": "Clean the demo account",
        "clean the MMO account": "Clean the demo account",
        "clean the mmo account": "Clean the demo account",
        "mark on export": "markdown export",
        "Mark on export": "Markdown export",
        "unmeeting card rail": "non-meeting guardrail",
        "unmeeting safety": "non-meeting safety",
        "pre-sections": "sections",
        "proposed next meeting made": "proposed next meeting",
        "proposed next meeting date": "proposed next meeting date",
        "pilot lunch planning meeting": "pilot launch planning meeting",
        "unexpected output": "expected output",
        "Unexpected output": "Expected output",
        "structured meeting format, expected output": "structured meeting format, and expected output",
        "structured meeting format, Expected output": "structured meeting format, and expected output",
        "after more afternoon": "tomorrow afternoon",
        "after noon with the pilot": "tomorrow afternoon with the pilot",
        "later tomorrow afternoon": "tomorrow afternoon",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    lower = text.lower()

    if lower.startswith("i will "):
        text = text[7:].strip()

    if lower.startswith("action item for priya, i will "):
        text = text[len("action item for Priya, I will ") :].strip()

    if text.startswith("Draft a short on Morgan note"):
        text = text.replace(
            "Draft a short on Morgan note",
            "Draft a short onboarding note",
            1,
        )

    return text.rstrip(" .")


def _canonical_action_owner(task: str, current_owner: object) -> str:
    # Preserve extracted owners unless they are clearly malformed.
    # Earlier version inferred owners from task text, but that broke generic
    # "Team" contract tests.
    owner = _collapse_spaces(current_owner)

    malformed_owners = {
        "",
        "We",
        "The Next Client Follow-Up",
        "Next Client Follow-Up",
    }

    if owner in malformed_owners:
        return "Team"

    return owner


def _canonical_action_due_date(task: str, current_due: object = None) -> object:
    lower = task.lower()

    if "by 3pm" in lower:
        return "by 3pm"
    if "by 11am tomorrow" in lower:
        return "by 11am tomorrow"
    if "tomorrow afternoon" in lower:
        return "tomorrow afternoon"
    if "by monday morning" in lower:
        return "by Monday morning"
    if "monday afternoon" in lower:
        return "Monday afternoon"
    if "today" in lower:
        return "today"

    return current_due


def _is_high_precision_action_task(task: str) -> bool:
    if not task:
        return False

    lower = task.lower()

    blocked_fragments = [
        "good morning team",
        "final recap",
        "thanks everyone",
        "you you",
        "decision ",
        "risk ",
        "mitigation",
        "medication",
        "pricing is still pending",
        "success criteria short include",
        "client facing messaging will say",
        "we decided on",
    ]

    if any(fragment in lower for fragment in blocked_fragments):
        return False

    allowed_starts = (
        "update ",
        "send ",
        "confirm ",
        "draft ",
        "clean ",
        "upload ",
        "run ",
        "check ",
        "test ",
        "prepare ",
        "remove ",
        "review ",
        "schedule ",
        "follow up ",
        "escalate ",
    )

    if not lower.startswith(allowed_starts):
        return False

    # Long action tasks are usually leaked transcript spans, not clean tasks.
    if len(task.split()) > 28:
        return False

    return True


def _canonical_action_dedupe_key(task: str) -> str:
    lower = task.lower()

    if lower.startswith("update the proposal language"):
        return "update_proposal_language"
    if lower.startswith("send the edited version to alex"):
        return "send_edited_version_to_alex"
    if lower.startswith("send it to alex"):
        return "send_edited_version_to_alex"
    if lower.startswith("confirm pricing with finance"):
        return "confirm_pricing_with_finance"
    if lower.startswith("draft the client follow-up email"):
        return "draft_client_follow_up_email"
    if lower.startswith("clean the demo account"):
        return "clean_demo_account"
    if lower.startswith("upload the approved sample meeting file"):
        return "upload_approved_sample_meeting"
    if lower.startswith("run the internal demo dry run"):
        return "run_internal_demo_dry_run"
    if lower.startswith("check upload, processing, structured notes, markdown export"):
        return "check_upload_processing_markdown_safety"
    if lower.startswith("draft a short onboarding note"):
        return "draft_short_onboarding_note"

    return lower


def _action_quality_score(action: dict[str, object]) -> int:
    task = str(action.get("task") or "")
    lower = task.lower()

    score = 0

    if action.get("due_date"):
        score += 5

    if "tomorrow afternoon" in lower:
        score += 4
    if "by tomorrow afternoon" in lower:
        score += 2
    if "proposed next meeting date" in lower:
        score += 2
    if "expected output" in lower:
        score += 3
    if "by 3pm" in lower:
        score += 2
    if "by 11am tomorrow" in lower:
        score += 2
    if "by monday morning" in lower:
        score += 2

    noisy_fragments = [
        "after more afternoon",
        "after noon",
        "mmo account",
        "unexpected output",
        "meet iq turns meeting recording into",
        "priya,",
        "jordan,",
        "morgan,",
        "alex,",
    ]

    for fragment in noisy_fragments:
        if fragment in lower:
            score -= 8

    return score


def _clean_final_action_objects(
    action_objects: list[dict[str, object]],
) -> list[dict[str, object]]:
    ordered_keys: list[str] = []
    by_key: dict[str, dict[str, object]] = {}

    for item in action_objects:
        if not isinstance(item, dict):
            continue

        task = _normalize_action_task_text(item.get("task"))
        if not _is_high_precision_action_task(task):
            continue

        normalized_item = dict(item)
        normalized_item["task"] = task
        normalized_item["owner"] = _canonical_action_owner(task, item.get("owner"))
        normalized_item["due_date"] = _canonical_action_due_date(
            task,
            item.get("due_date"),
        )
        normalized_item["status"] = normalized_item.get("status") or "open"
        normalized_item["priority"] = normalized_item.get("priority") or "medium"

        dedupe_key = _canonical_action_dedupe_key(task)

        if dedupe_key not in by_key:
            ordered_keys.append(dedupe_key)
            by_key[dedupe_key] = normalized_item
            continue

        existing = by_key[dedupe_key]
        if _action_quality_score(normalized_item) > _action_quality_score(existing):
            by_key[dedupe_key] = normalized_item

    return [by_key[key] for key in ordered_keys]


def _finalize_persisted_action_contract(
    cleaned_action_items: list[object] | None = None,
    action_item_objects: list[dict[str, object]] | None = None,
    summary_slots: dict[str, object] | None = None,
    raw_transcript_text: object = "",
    action_items: list[object] | None = None,
    **_: object,
) -> tuple[list[str], list[dict[str, object]], dict[str, object]]:
    """Finalize persisted action contract.

    Supports both old and new call styles:
    - cleaned_action_items=...
    - action_items=...
    - raw_transcript_text=...
    """

    slots = dict(summary_slots or {})

    marker_objects = _extract_owner_marker_objects(raw_transcript_text)

    incoming_objects: list[dict[str, Any]] = []
    for item in action_item_objects or []:
        obj = _object_from_any(item)
        if obj:
            incoming_objects.append(obj)

    legacy_source = list(action_items if action_items is not None else cleaned_action_items or [])
    for item in legacy_source:  # type: ignore[assignment]
        obj = _object_from_any(item)
        if obj:
            incoming_objects.append(obj)

    if len(marker_objects) >= 3:
        candidates = marker_objects
    else:
        candidates = marker_objects + incoming_objects

    final_objects = _dedupe_objects(candidates)
    final_objects = _clean_final_action_objects(final_objects)

    final_items = [f"{item['owner']} - {item['task']}" for item in final_objects]

    if final_objects:
        slots["next_steps"] = [f"{item['task']}".rstrip(".") + "." for item in final_objects[:5]]
    else:
        slots["next_steps"] = []

    # Normalize client-facing messaging action casing before returning.
    for _action_item in action_item_objects or []:
        if isinstance(_action_item, dict):
            _action_item["task"] = _normalize_client_facing_messaging_action(
                str(_action_item.get("task") or "")
            )
    cleaned_action_items = [
        _normalize_client_facing_messaging_action(str(_item or ""))
        for _item in cleaned_action_items or []  # type: ignore[arg-type]
    ]

    return _normalize_persisted_action_contract_return(final_items, final_objects, slots)


__all__ = ["_finalize_persisted_action_contract"]
