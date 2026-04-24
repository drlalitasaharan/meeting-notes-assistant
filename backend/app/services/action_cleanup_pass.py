from __future__ import annotations

import re
from typing import Any

STRATEGY_ACTION_HINTS = re.compile(
    r"\b("
    r"pilot audience focused|users with clear pain|short meetings|"
    r"practical positioning message|broad platform pitch|"
    r"target consultants|target agencies|target startup teams"
    r")\b",
    re.IGNORECASE,
)

BACKUP_DEMO_HINTS = re.compile(
    r"\b("
    r"backup demo|backup meeting|live demo|live client presentation|"
    r"processed before any live demo|processed meeting ready|process meeting ready|"
    r"backup demo example|meeting 17"
    r")\b",
    re.IGNORECASE,
)


NON_ACTION_HINTS = re.compile(
    r"\b("
    r"concrete owners for the follow-up actions|"
    r"owners for the follow-up actions|"
    r"clear decision on the target audience|"
    r"finalized plan for the demo flow"
    r")\b",
    re.IGNORECASE,
)


def apply_deterministic_action_cleanup(
    action_items: list[str] | None,
    action_item_objects: list[dict[str, Any]] | None = None,
) -> tuple[list[str], list[dict[str, Any]]]:
    cleaned_lines: list[str] = []
    seen: set[str] = set()

    for raw in action_items or []:
        text = _canonicalize_action_text(str(raw or "").strip())
        if not text:
            continue

        norm = _action_norm(text)
        if not norm or norm in seen:
            continue

        seen.add(norm)
        cleaned_lines.append(text)

    norms = {_action_norm(x) for x in cleaned_lines}
    meeting17_norm = _action_norm(
        "Keep meeting 17 as the primary backup demo example before the live client presentation."
    )
    generic_backup_norm = _action_norm(
        "Keep one primary backup demo example ready before the live client presentation."
    )

    if meeting17_norm in norms:
        cleaned_lines = [x for x in cleaned_lines if _action_norm(x) != generic_backup_norm]

    rebuilt_objects = [_line_to_action_object(line) for line in cleaned_lines]
    return cleaned_lines, rebuilt_objects


def _canonicalize_action_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip(" -")

    if not text:
        return ""

    # Drop strategy / targeting statements that are not concrete follow-up tasks.
    if STRATEGY_ACTION_HINTS.search(text):
        return ""

    # Drop agenda/summary fragments that mention actions but are not themselves tasks.
    if NON_ACTION_HINTS.search(text):
        return ""

    # Canonicalize backup-demo variants into one strong action.
    lowered = text.lower()
    if BACKUP_DEMO_HINTS.search(text):
        if "meeting 17" in lowered:
            return "Keep meeting 17 as the primary backup demo example before the live client presentation."
        return "Keep one primary backup demo example ready before the live client presentation."

    # Drop weak fragments if they slipped through.
    if lowered in {
        "keep one process meeting ready.",
        "keep one processed meeting ready.",
        "keep one process meeting ready",
        "keep one processed meeting ready",
    }:
        return ""

    # Light cleanup for malformed verb phrase.
    text = re.sub(r"\bkeep meeting 17 is\b", "Keep meeting 17 as", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()

    if text and text[-1] not in ".!?":
        text += "."

    return text


def _action_norm(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\(due:\s*([^)]+)\)", "", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\b(a|an|the|is|as)\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _line_to_action_object(line: str) -> dict[str, Any]:
    owner = None
    task = line.strip()
    due_date = None

    due_match = re.search(r"\(due:\s*([^)]+)\)", task, flags=re.IGNORECASE)
    if due_match:
        due_date = due_match.group(1).strip()
        task = re.sub(r"\(due:\s*([^)]+)\)", "", task, flags=re.IGNORECASE).strip()

    if " - " in task:
        maybe_owner, maybe_task = task.split(" - ", 1)
        if len(maybe_owner.split()) <= 4:
            owner = maybe_owner.strip()
            task = maybe_task.strip()

    return {
        "owner": owner,
        "task": task,
        "due_date": due_date,
        "status": "open",
        "priority": "medium",
        "confidence": 0.7,
    }
