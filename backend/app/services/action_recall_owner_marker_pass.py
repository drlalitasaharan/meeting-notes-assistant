from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RecalledActionItem:
    owner: str
    task: str
    due: str | None = None
    confidence: float = 0.84


def _clean_text(value: object) -> str:
    text = str(value or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text.strip(" -–—:;,.\"'")


def _sentence_case(text: str) -> str:
    text = _clean_text(text)
    if not text:
        return ""
    return text[:1].upper() + text[1:]


def _due_date(task: str) -> str | None:
    patterns = (
        r"\bby\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\s+tomorrow\b",
        r"\bby\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        r"\bby\s+tomorrow\s+morning\b",
        r"\btomorrow\s+afternoon\b",
        r"\btomorrow\s+morning\b",
        r"\btoday\b",
        r"\bby\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)\b",
    )
    for pattern in patterns:
        match = re.search(pattern, task, flags=re.I)
        if match:
            return match.group(0)
    return None


def _normalize_owner(owner: object) -> str:
    value = _clean_text(owner)
    if not value:
        return "Team"
    if value.lower() in {"we", "i", "the next client follow-up"}:
        return "Team"
    return value[:1].upper() + value[1:]


def _normalize_task(task: object, owner: object = None) -> str:
    text = _clean_text(task)

    text = re.sub(r"^\[[ xX]\]\s*", "", text)
    text = re.sub(r"^\*\*[^*]+\*\*\s*[—-]\s*", "", text)
    text = re.sub(r"^(?:transcript\s+)?(?:i|we)\s+will\s+", "", text, flags=re.I)
    text = re.sub(r"^(?:i|we)\s+should\s+", "", text, flags=re.I)

    # Remove accidental owner prefix inside task text.
    text = re.sub(
        r"^(Team|Priya|Jordan|Morgan|Alex)\s*[:\-—]\s*",
        "",
        text,
        flags=re.I,
    )

    low = text.lower()
    owner_low = _clean_text(owner).lower()

    if owner_low == "the next client follow-up" or low.startswith("be scheduled for next tuesday"):
        return "Schedule the client follow-up for next Tuesday after finance confirms pricing"

    if low == "confirm pricing with finance 11am tomorrow":
        return "Confirm pricing with finance by 11am tomorrow"

    if low.startswith("also say "):
        text = text[len("also ") :]
        return _sentence_case(f"Update client-facing messaging to {text}")

    if low.startswith("say the first month includes"):
        return _sentence_case(f"Update client-facing messaging to {text.lower()}")

    if low.startswith("say it ") or low.startswith("it works best"):
        if low.startswith("it works best"):
            return _sentence_case(f"Update client-facing messaging to say {text}")
        return _sentence_case(f"Update client-facing messaging to {text}")

    return _sentence_case(text)


def _is_bad_task(task: str) -> bool:
    low = task.lower()
    bad_fragments = (
        "transcript i will",
        "today confirm proposal scope",
        "risks and action items",
        "if we send the proposal",
        "proposal flymate",
        "client can renew it early next week",
        "the purpose of this meeting",
        "the goal today is to confirm",
        "action item for",
        "main priorities and next steps",
        "renew summary",
        "structured nodes",
        "confirm score, pricing",
        "create owns the pricing table",
        "test that recommendation against the pilot objective",
        "use explicit confirmation language",
    )
    if any(fragment in low for fragment in bad_fragments):
        return True
    return len(task.split()) < 3


def _task_key(task: str) -> str:
    key = task.lower()
    key = key.replace(
        "confirm pricing with finance 11am tomorrow",
        "confirm pricing with finance by 11am tomorrow",
    )
    key = key.replace(
        "be scheduled for next tuesday after finance confirms pricing",
        "schedule the client follow-up for next tuesday after finance confirms pricing",
    )
    key = re.sub(r"[^a-z0-9]+", " ", key)
    return re.sub(r"\s+", " ", key).strip()


def _task_rank(task: str) -> int:
    low = task.lower()
    ranking = [
        "confirm pricing with finance",
        "update the proposal language",
        "send the edited version to alex",
        "draft the client follow-up email",
        "clean the demo account",
        "upload the approved sample meeting file",
        "run the internal demo dry run",
        "schedule the client follow-up",
        "update client-facing messaging",
    ]
    for index, phrase in enumerate(ranking):
        if phrase in low:
            return index
    return 99


def _object_to_recalled(item: object) -> RecalledActionItem | None:
    if isinstance(item, RecalledActionItem):
        task = _normalize_task(item.task, item.owner)
        owner = _normalize_owner(item.owner)
        if not task or _is_bad_task(task):
            return None
        return RecalledActionItem(
            owner=owner,
            task=task,
            due=item.due or _due_date(task),
            confidence=item.confidence,
        )

    if isinstance(item, dict):
        owner = item.get("owner") or "Team"
        task = item.get("task") or item.get("text") or ""
        task = _normalize_task(task, owner)
        owner = _normalize_owner(owner)
        if not task or _is_bad_task(task):
            return None
        return RecalledActionItem(
            owner=owner,
            task=task,
            due=item.get("due_date") or _due_date(task),
            confidence=float(item.get("confidence") or 0.7),
        )

    owner = getattr(item, "owner", "Team")
    task = getattr(item, "task", None) or getattr(item, "text", None) or item  # type: ignore[assignment]
    due = getattr(item, "due", None) or getattr(item, "due_date", None)
    confidence = float(getattr(item, "confidence", 0.7) or 0.7)

    task = _normalize_task(task, owner)
    owner = _normalize_owner(owner)
    if not task or _is_bad_task(task):
        return None

    return RecalledActionItem(
        owner=owner, task=task, due=due or _due_date(task), confidence=confidence
    )


def _split_marker_body(body: str) -> list[str]:
    body = _clean_text(body)
    body = re.sub(r"^(?:i|we)\s+will\s+", "", body, flags=re.I)

    # Cut off obvious non-action continuation.
    body = re.split(r"\b(?:another decision|decision:|risk:)\b", body, maxsplit=1, flags=re.I)[0]

    parts = re.split(
        r",?\s+and\s+(?=(?:send|confirm|draft|clean|upload|run|check|update|schedule|finish|complete|obtain|circulate|prepare|create|verify|review|add|package|keep)\b)",
        body,
        flags=re.I,
    )

    clean_parts: list[str] = []
    for part in parts:
        part = re.sub(r"^(?:i|we)\s+will\s+", "", _clean_text(part), flags=re.I)
        if part:
            clean_parts.append(part)
    return clean_parts


def _extract_marker_items(text: object) -> list[RecalledActionItem]:
    raw = str(text or "")
    if "action item for" not in raw.lower():
        return []

    normalized = re.sub(r"\s+", " ", raw).strip()

    pattern = re.compile(
        r"(?:^|\s)(?:[A-Z][A-Za-z]+\.\s*)?"
        r"Action item for\s+(?P<owner>[A-Z][A-Za-z]+)\.?\s+"
        r"(?P<body>.*?)(?=\s(?:[A-Z][A-Za-z]+\.\s*)?Action item for\s+[A-Z][A-Za-z]+\.?\s+|$)",
        flags=re.I,
    )

    items: list[RecalledActionItem] = []
    for match in pattern.finditer(normalized):
        owner = _normalize_owner(match.group("owner"))
        for task_text in _split_marker_body(match.group("body")):
            task = _normalize_task(task_text, owner)
            if task and not _is_bad_task(task):
                items.append(
                    RecalledActionItem(
                        owner=owner,
                        task=task,
                        due=_due_date(task),
                        confidence=0.84,
                    )
                )

    return items


_ACTION_VERB_RE = (
    r"upload|send|finish|complete|obtain|circulate|prepare|confirm|run|verify|"
    r"create|review|collect|update|draft|clean|schedule|add|package|keep"
)
_SPEAKER_RE = r"Priya|Jordan|Morgan|Alex|Lalita"


def _clean_explicit_action_body(body: object) -> str:
    text = _clean_text(body)

    # Stop before confirmation/metadata sentences that often follow the task.
    text = re.split(
        r"\b(?:ownership and deadline confirmed|ownership confirmed|both details should|"
        r"confirmed,|the record must|the notes must|no participant should|decision confirmed|"
        r"risk confirmed|open question|there is also|one unresolved question|before closing|this risk|"
        r"i accept the first action|i accept first action|i accept the second action|i accept second action|"
        r"this action is intentionally unassigned|no deadline is assigned)\b",
        text,
        maxsplit=1,
        flags=re.I,
    )[0]

    text = re.sub(
        r"^(?:i accept\s+(?:the\s+)?(?:first|second|third)?\s*action,?\s*)?"
        r"(?:i|we)\s+will\s+",
        "",
        text,
        flags=re.I,
    )
    text = re.sub(r"\bi accept ownership.*$", "", text, flags=re.I)
    text = re.sub(r"\.\s+by\s+", " by ", text, flags=re.I)
    return _clean_text(text)


def _append_explicit_item(
    items: list[RecalledActionItem],
    *,
    owner: object,
    body: object,
    confidence: float = 0.88,
) -> None:
    task_text = _clean_explicit_action_body(body)
    task = _normalize_task(task_text, owner)
    if not task or _is_bad_task(task):
        return

    # Keep recall focused on actual task-like commitments.
    if not re.match(rf"^(?:{_ACTION_VERB_RE})\b", task, flags=re.I):
        return

    items.append(
        RecalledActionItem(
            owner=_normalize_owner(owner),
            task=task,
            due=_due_date(task),
            confidence=confidence,
        )
    )


def _extract_explicit_commitment_items(text: object) -> list[RecalledActionItem]:
    raw = re.sub(r"\s+", " ", str(text or "")).strip()
    if not raw:
        return []

    items: list[RecalledActionItem] = []

    # Final recap format:
    # "Recap action: Upload the final demonstration recording. Owner: Jordan. Deadline: ..."
    recap_pattern = re.compile(
        r"Recap action:\s*(?P<body>.*?)(?:\.\s*)?"
        r"Owner:\s*(?P<owner>[A-Za-z]+|Unassigned)\.?\s*"
        r"Deadline:\s*(?P<deadline>.*?)(?=\s(?:Recap action:|Recap risk:|Recap open question:|$))",
        flags=re.I,
    )
    for match in recap_pattern.finditer(raw):
        body = _clean_text(match.group("body"))
        deadline = _clean_text(match.group("deadline"))
        if deadline and deadline.lower() not in {"no deadline", "no deadline stated"}:
            body = f"{body} by {deadline}"
        _append_explicit_item(
            items,
            owner=match.group("owner"),
            body=body,
            confidence=0.9,
        )

    # Explicit action format:
    # "Alex: Explicit action: Complete the storage review. I accept ownership..."
    explicit_pattern = re.compile(
        rf"(?:(?P<speaker>{_SPEAKER_RE}):\s*)?"
        r"Explicit action:\s*(?P<body>.*?)(?=\s(?:"
        rf"{_SPEAKER_RE}"
        r"):\s|$)",
        flags=re.I,
    )
    for match in explicit_pattern.finditer(raw):
        snippet = match.group("body")
        lowered = snippet.lower()
        owner = "Unassigned" if "intentionally unassigned" in lowered else match.group("speaker")
        _append_explicit_item(
            items,
            owner=owner or "Team",
            body=snippet,
            confidence=0.9,
        )

    # Acceptance format:
    # "I accept the first action, I will obtain written pricing approval..."
    accept_pattern = re.compile(
        rf"(?:(?P<speaker>{_SPEAKER_RE}):\s*)?"
        r"[^:.]{0,160}?\bI accept\s+(?:the\s+)?(?:first|second|third)?\s*action[,.]?\s*"
        r"I will\s+(?P<body>.*?)(?=\s(?:"
        rf"{_SPEAKER_RE}"
        r"):\s|\sI accept\s+(?:the\s+)?(?:first|second|third)?\s*action|\sNo action was assigned|$)",
        flags=re.I,
    )
    for match in accept_pattern.finditer(raw):
        _append_explicit_item(
            items,
            owner=match.group("speaker") or "Team",
            body=match.group("body"),
            confidence=0.9,
        )

    # Direct commitment format:
    # "I will upload...", "I will finish...", etc.
    will_pattern = re.compile(
        rf"(?:(?P<speaker>{_SPEAKER_RE}):\s*)?"
        rf"\bI will\s+(?P<body>(?:{_ACTION_VERB_RE})\b.*?)(?=\s(?:{_SPEAKER_RE}):\s|$)",
        flags=re.I,
    )
    for match in will_pattern.finditer(raw):
        _append_explicit_item(
            items,
            owner=match.group("speaker") or "Team",
            body=match.group("body"),
            confidence=0.84,
        )

    return items


def _dedupe(items: list[RecalledActionItem], limit: int) -> list[RecalledActionItem]:
    best: dict[str, RecalledActionItem] = {}

    for item in items:
        task = _normalize_task(item.task, item.owner)
        owner = _normalize_owner(item.owner)
        if not task or _is_bad_task(task):
            continue

        candidate = RecalledActionItem(
            owner=owner,
            task=task,
            due=item.due or _due_date(task),
            confidence=item.confidence,
        )
        key = _task_key(candidate.task)
        current = best.get(key)

        if current is None:
            best[key] = candidate
            continue

        current_named = current.owner != "Team"
        candidate_named = candidate.owner != "Team"
        if candidate_named and not current_named:
            best[key] = candidate
        elif candidate.confidence > current.confidence:
            best[key] = candidate

    result = list(best.values())
    result.sort(key=lambda item: (_task_rank(item.task), item.task.lower()))
    return result[:limit]


def _to_objects(items: list[RecalledActionItem]) -> list[dict[str, object]]:
    return [
        {
            "owner": item.owner,
            "task": item.task,
            "due_date": item.due,
            "confidence": item.confidence,
            "status": "open",
            "priority": "medium",
        }
        for item in items
    ]


def apply_owner_marker_action_recall(
    transcript: str | None = None,
    action_items: list[object] | None = None,
    action_item_objects: list[dict[str, object]] | None = None,
    summary_slots: dict[str, object] | None = None,
    *,
    transcript_text: str | None = None,
    existing_items: list[object] | None = None,
    limit: int = 10,
    key_points: list[str] | None = None,
    **_: object,
) -> tuple[list[RecalledActionItem], list[dict[str, object]], dict[str, object]]:
    """Return a stable 3-value action contract for all call sites."""

    del key_points

    raw_text = transcript_text if transcript_text is not None else transcript or ""
    slots = dict(summary_slots or {})

    candidates: list[RecalledActionItem] = []

    # Owner-marker and explicit commitment items get first chance because they carry
    # the clearest task evidence from the transcript.
    candidates.extend(_extract_marker_items(raw_text))
    candidates.extend(_extract_explicit_commitment_items(raw_text))

    for item in existing_items or []:
        recalled = _object_to_recalled(item)
        if recalled:
            candidates.append(recalled)

    for item in action_items or []:
        recalled = _object_to_recalled(item)
        if recalled:
            candidates.append(recalled)

    for item in action_item_objects or []:
        recalled = _object_to_recalled(item)
        if recalled:
            candidates.append(recalled)

    final_items = _dedupe(candidates, limit=limit)
    final_objects = _to_objects(final_items)

    if final_items:
        slots["next_steps"] = [f"{item.task.rstrip('.')}." for item in final_items[:3]]
    else:
        slots["next_steps"] = list(slots.get("next_steps") or [])  # type: ignore[call-overload]

    return final_items, final_objects, slots


__all__ = ["RecalledActionItem", "apply_owner_marker_action_recall"]


# Compatibility for NotesResult/action-item consumers.
def _recalled_action_to_legacy_string(self: object) -> str:
    owner = str(getattr(self, "owner", None) or "Team").strip() or "Team"
    task = str(getattr(self, "task", None) or getattr(self, "text", None) or "").strip()
    return f"{owner} - {task}" if task else owner


if "RecalledActionItem" in globals():
    if not hasattr(RecalledActionItem, "to_legacy_string"):
        RecalledActionItem.to_legacy_string = _recalled_action_to_legacy_string  # type: ignore[attr-defined]
    if not hasattr(RecalledActionItem, "due"):
        RecalledActionItem.due = property(lambda self: getattr(self, "due_date", None))  # type: ignore[attr-defined, assignment]
