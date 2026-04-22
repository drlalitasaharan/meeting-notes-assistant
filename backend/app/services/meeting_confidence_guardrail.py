from __future__ import annotations

import re
from typing import Any

MEETING_SIGNALS = [
    "agenda",
    "next steps",
    "action item",
    "action items",
    "decision",
    "decisions",
    "follow up",
    "follow-up",
    "owner",
    "deadline",
    "by friday",
    "let's",
    "we should",
    "pilot",
    "demo",
    "meeting notes",
    "summary",
    "client",
]

NON_MEETING_SIGNALS = [
    "sherlock holmes",
    "dr. watson",
    "watson",
    "holmes",
    "mr. wilson",
    "red-headed league",
    "gentleman",
    "armchair",
    "billet",
    "i cried",
    "said holmes",
    "he stood at the side of the hole",
]


def _count_hits(text: str, patterns: list[str]) -> int:
    lower = text.lower()
    return sum(1 for pattern in patterns if pattern in lower)


def _strip_generic_meeting_tail(summary: str) -> str:
    cleaned = re.sub(
        r"\bThe meeting aligned on the main priorities and next steps\.?\s*$",
        "",
        summary,
        flags=re.IGNORECASE,
    ).strip()
    return cleaned.rstrip(" ;,.")


def apply_meeting_confidence_guardrail(
    notes_dict: dict[str, Any],
    transcript_text: str,
) -> dict[str, Any]:
    text = (transcript_text or "").strip()
    if not text:
        return notes_dict

    meeting_hits = _count_hits(text, MEETING_SIGNALS)
    non_meeting_hits = _count_hits(text, NON_MEETING_SIGNALS)

    should_downgrade = non_meeting_hits >= 2 and meeting_hits <= 1
    if not should_downgrade:
        return notes_dict

    summary = (notes_dict.get("summary") or "").strip()
    summary = _strip_generic_meeting_tail(summary)

    if summary:
        summary = (
            summary
            + ". This audio does not appear to be a structured business meeting. "
            + "Meeting-style decisions and action items were not generated."
        )
    else:
        summary = (
            "This audio does not appear to be a structured business meeting. "
            "Meeting-style decisions and action items were not generated."
        )

    notes_dict["summary"] = summary
    notes_dict["decisions"] = []
    notes_dict["action_items"] = []
    notes_dict["decision_objects"] = []
    notes_dict["action_item_objects"] = []
    notes_dict["summary_slots"] = {
        "purpose": "",
        "outcome": "",
        "risks": [],
        "next_steps": [],
    }

    key_points = notes_dict.get("key_points") or []
    notes_dict["key_points"] = key_points[:5]

    return notes_dict
