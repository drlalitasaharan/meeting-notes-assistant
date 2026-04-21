from __future__ import annotations

import re
from typing import List

from app.schemas.meeting_notes import ActionItem, MeetingNotesCanonical

STATUS_HINTS = (
    "we discussed",
    "we reviewed",
    "we talked about",
    "already done",
    "has been done",
    "was fixed",
    "was completed",
    "completed",
    "finished",
)

DECISION_HINTS = (
    "we agreed",
    "agreed that",
    "decided",
    "approved",
    "chosen",
)

PLANNING_FRAME_HINTS = (
    "by the end of the meeting",
    "we should leave with",
    "purpose of this meeting",
    "goal of this meeting",
)

TASK_HINTS = (
    " will ",
    " should ",
    " need to ",
    " needs to ",
    " follow up ",
    " follow-up ",
    " please ",
    " can you ",
    " could you ",
)

ACTION_STARTERS = (
    "review ",
    "prepare ",
    "finalize ",
    "update ",
    "create ",
    "share ",
    "send ",
    "schedule ",
    "confirm ",
    "test ",
    "fix ",
    "draft ",
)


def _clean_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -•")


def _looks_like_status_update(text: str) -> bool:
    lower = text.lower()
    return any(h in lower for h in STATUS_HINTS)


def _looks_like_decision(text: str) -> bool:
    lower = text.lower()
    return any(h in lower for h in DECISION_HINTS)


def _looks_like_planning_frame(text: str) -> bool:
    lower = text.lower()
    return any(h in lower for h in PLANNING_FRAME_HINTS)


def _looks_task_oriented(text: str, owner: str | None) -> bool:
    lower = text.lower()

    if lower.startswith(ACTION_STARTERS):
        return True

    if any(h in f" {lower} " for h in TASK_HINTS):
        return True

    if owner and re.search(r"\bwill\b|\bshould\b|\bneed[s]? to\b", lower):
        return True

    return False


def validate_action_items(items: List[ActionItem]) -> List[ActionItem]:
    valid: List[ActionItem] = []
    seen = set()

    for item in items:
        item.text = _clean_text(item.text)

        if len(item.text) < 12:
            continue
        if item.confidence < 0.65:
            continue
        if _looks_like_status_update(item.text):
            continue
        if _looks_like_decision(item.text):
            continue
        if _looks_like_planning_frame(item.text):
            continue
        if not _looks_task_oriented(item.text, item.owner):
            continue

        if item.text.lower().startswith("we ") and not item.owner:
            continue

        key = item.text.lower()
        if key in seen:
            continue
        seen.add(key)

        valid.append(item)

    return valid[:6]


def validate_canonical(notes: MeetingNotesCanonical) -> MeetingNotesCanonical:
    notes.action_items = validate_action_items(notes.action_items)
    return notes
