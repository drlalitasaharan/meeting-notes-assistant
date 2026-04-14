from __future__ import annotations

import re
from typing import Iterable

DROP_PATTERNS = [
    re.compile(r"\blet'?s make that an action item\b", re.I),
    re.compile(r"\bmake that an action item\b", re.I),
    re.compile(r"\bthat should be an action item\b", re.I),
    re.compile(r"\bwe should include\b", re.I),
    re.compile(r"\bthat'?s helpful\b", re.I),
    re.compile(r"\bsounds good\b", re.I),
    re.compile(r"\bexactly\b", re.I),
    re.compile(r"\bi think\b", re.I),
    re.compile(r"\bi also think\b", re.I),
    re.compile(r"\bthe main purpose\b", re.I),
]

ACTION_HINTS = (
    "send",
    "review",
    "finalize",
    "prepare",
    "create",
    "run",
    "share",
    "update",
    "fix",
    "keep",
    "record",
    "confirm",
    "draft",
    "upload",
    "check",
    "test",
    "validate",
    "follow up",
    "follow-up",
    "reach out",
    "schedule",
    "complete",
    "deliver",
    "use",
    "watch",
    "build",
    "document",
    "verify",
    "fetch",
    "add",
    "package",
    "save",
)

ACTION_STARTERS = (
    "prepare",
    "create",
    "test",
    "verify",
    "check",
    "use",
    "build",
    "review",
    "update",
    "send",
    "share",
    "confirm",
    "document",
    "fix",
    "run",
    "watch",
    "upload",
    "fetch",
    "validate",
    "keep",
    "draft",
    "finalize",
    "schedule",
    "add",
    "package",
    "save",
)

BAD_PREFIXES = (
    "speaker one",
    "speaker two",
    "speaker 1",
    "speaker 2",
    "team - speaker",
    "i think",
    "i also think",
    "we should be careful",
    "it is important",
    "the main purpose",
)

DUE_RE = re.compile(
    r"\b(by|before|on)\s+"
    r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"today|tomorrow|tonight|next week|next month)\b",
    re.I,
)

COMBINED_KEEP_PATTERNS = (
    "review and finalize",
    "check and confirm",
    "prepare the short-lived demo file and keep one backup processed meeting ready",
)

SPLIT_STARTERS = (
    "prepare",
    "keep",
    "create",
    "run",
    "send",
    "share",
    "update",
    "fix",
    "record",
    "upload",
    "test",
    "draft",
    "schedule",
    "review",
    "finalize",
    "confirm",
    "validate",
    "verify",
    "document",
    "add",
    "package",
    "save",
)


def _normalize(text: str) -> str:
    text = str(text).strip()

    # Normalize separator dashes, but preserve word-internal hyphens like "10-minute"
    text = re.sub(r"\s*[—–]\s*", " - ", text)

    # Normalize plain hyphen separators only when already surrounded by spaces
    text = re.sub(r"\s+-\s+", " - ", text)

    text = re.sub(r"\s+", " ", text)
    return text.strip(" -")


def _canonical(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\(due:[^)]+\)", "", text)
    text = re.sub(r"[^a-z0-9 ]+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_due(text: str) -> tuple[str, str | None]:
    match = DUE_RE.search(text)
    if not match:
        return text, None
    due_phrase = match.group(0).strip()
    text = text[: match.start()].strip(" ,.-")
    return text, due_phrase


def _starts_with_action_starter(text: str) -> bool:
    if not text:
        return False
    first = re.sub(r"[^a-z]", "", text.split()[0].lower())
    return first in ACTION_STARTERS


def _looks_actionable(text: str) -> bool:
    lowered = f" {text.lower()} "

    if len(text.split()) < 3:
        return False

    if len(text.split()) > 22:
        return False

    if any(lowered.strip().startswith(prefix) for prefix in BAD_PREFIXES):
        return False

    if " will " in lowered:
        return True

    if _starts_with_action_starter(text):
        return True

    return any(hint in lowered for hint in ACTION_HINTS)


def _split_owner_and_task(text: str) -> tuple[str | None, str]:
    if " - " in text:
        owner, task = text.split(" - ", 1)
        owner = owner.strip()
        task = task.strip()
        if owner and task:
            if owner.lower() in {"we", "team"}:
                owner = "Team"
            return owner, task

    match = re.match(r"^([A-Z][a-zA-Z]+)\s+will\s+(.+)$", text)
    if match:
        return match.group(1), match.group(2).strip()

    match = re.match(r"^(We|Team)\s+will\s+(.+)$", text, re.I)
    if match:
        return "Team", match.group(2).strip()

    match = re.match(r"^The\s+(.+?)\s+will\s+be\s+(.+)$", text, re.I)
    if match:
        subject = match.group(1).strip()
        task = match.group(2).strip()
        return None, f"{task} {subject}"

    return None, text


def _rewrite_task(owner: str | None, task: str) -> str:
    task = task.strip()

    # remove speaker bleed like "Kevin, ..."
    task = re.sub(r"^(?:[A-Z][a-z]+,\s*)+", "", task)

    # if owner is already known, remove repeated owner phrasing in task
    if owner:
        task = re.sub(rf"^{re.escape(owner)}\s+will\s+", "", task, flags=re.I)

    task = re.sub(r"^(will|to)\s+", "", task, flags=re.I)
    task = re.sub(r"^also\s+", "", task, flags=re.I)
    task = re.sub(r"^we should\s+", "", task, flags=re.I)
    task = re.sub(r"^should\s+", "", task, flags=re.I)
    task = re.sub(r"^we need to\s+", "", task, flags=re.I)
    task = re.sub(r"^need to\s+", "", task, flags=re.I)
    task = re.sub(r"^include\s+", "prepare ", task, flags=re.I)
    task = re.sub(r"^reviewed and finalized\b", "review and finalize", task, flags=re.I)
    task = re.sub(r"^reviewed\b", "review", task, flags=re.I)
    task = re.sub(r"^finalized\b", "finalize", task, flags=re.I)

    # normalize a few recap-style phrasings into stronger action starters
    task = re.sub(r"^stage timing logs\b", "add stage timing logs", task, flags=re.I)
    task = re.sub(
        r"^the final demo commands\b", "package the final demo commands", task, flags=re.I
    )
    task = re.sub(
        r"^the strongest current output\b", "save the strongest current output", task, flags=re.I
    )
    task = re.sub(
        r"^one backup meeting already processed\b",
        "keep one backup meeting already processed",
        task,
        flags=re.I,
    )
    task = re.sub(
        r"^a short command checklist\b", "keep a short command checklist", task, flags=re.I
    )
    task = re.sub(r"^keep meeting\s+(\d+)\s+is\b", r"keep meeting \1 as", task, flags=re.I)

    # normalize the demo-prep combined task
    task = re.sub(
        r"^prepare the short-lived demo file\s+and\s+keep one backup processed meeting ready\b",
        "prepare the short-lived demo file and keep one backup processed meeting ready",
        task,
        flags=re.I,
    )

    # remove obvious discussion filler / commentary tails
    task = re.sub(r"\s+so that\s+.+$", "", task, flags=re.I)
    task = re.sub(r"\s+because\s+.+$", "", task, flags=re.I)
    task = re.sub(r"\s+though\s+.+$", "", task, flags=re.I)
    task = re.sub(r"\s+without interruption\.?$", "", task, flags=re.I)

    task = task.strip(" .,-")
    if owner:
        return f"{owner} - {task}"
    return task


def _assign_default_owner(owner: str | None) -> str:
    return owner if owner else "Team"


def _should_keep_combined(task: str) -> bool:
    lowered = task.lower()
    return any(pattern in lowered for pattern in COMBINED_KEEP_PATTERNS)


def _split_compound_task(task: str) -> list[str]:
    task = task.strip()

    if _should_keep_combined(task):
        return [task]

    parts = re.split(r"\s+and\s+", task, maxsplit=1)
    if len(parts) != 2:
        return [task]

    left, right = parts[0].strip(), parts[1].strip()
    if not left or not right:
        return [task]

    if any(right.lower().startswith(starter + " ") for starter in SPLIT_STARTERS):
        return [left, right]

    return [task]


def _final_quality_gate(text: str) -> bool:
    lowered = text.lower()
    task_text = text.split(" - ", 1)[-1].strip()

    if any(prefix in lowered for prefix in BAD_PREFIXES):
        return False

    if "speaker " in lowered:
        return False

    if " i think " in f" {lowered} ":
        return False

    if " sounds good" in lowered or " exactly" in lowered:
        return False

    if _starts_with_action_starter(task_text):
        return True

    if any(hint in f" {task_text.lower()} " for hint in ACTION_HINTS):
        return True

    return False


def clean_action_items(items: Iterable[str] | None) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()

    for raw in items or []:
        text = _normalize(raw)
        if not text:
            continue

        if any(pattern.search(text) for pattern in DROP_PATTERNS):
            continue

        text, due = _extract_due(text)
        owner, task = _split_owner_and_task(text)
        rewritten = _rewrite_task(owner, task)

        if not _looks_actionable(rewritten):
            continue

        rewritten_owner, rewritten_task = _split_owner_and_task(rewritten)
        rewritten_owner = _assign_default_owner(rewritten_owner)

        split_tasks = _split_compound_task(rewritten_task)

        for subtask in split_tasks:
            subtask = subtask.strip()
            if not subtask:
                continue

            final = f"{rewritten_owner} - {subtask}"

            if due:
                final = f"{final} (due: {due})"

            if not _final_quality_gate(final):
                continue

            key = _canonical(final)
            if not key or key in seen:
                continue

            seen.add(key)
            cleaned.append(final)

    return cleaned
