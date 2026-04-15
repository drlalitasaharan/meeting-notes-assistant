from __future__ import annotations

import re
from typing import List

from app.schemas.meeting_notes import MeetingNotesCanonical


def _sentence(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    if text.endswith((".", "!", "?")):
        return text
    return f"{text}."


def _norm(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9 ]+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def compose_summary(notes: MeetingNotesCanonical) -> str:
    parts: List[str] = []

    if notes.purpose:
        parts.append(_sentence(notes.purpose))

    if notes.outcome and _norm(notes.outcome) != _norm(notes.purpose):
        parts.append(_sentence(notes.outcome))

    if notes.decisions:
        decisions_text = "; ".join(x.text for x in notes.decisions[:2])
        parts.append(_sentence(f"Key decisions included {decisions_text}"))

    if notes.action_items:
        parts.append(_sentence(f"{len(notes.action_items)} validated action items were captured"))

    return " ".join(x for x in parts if x).strip()


def to_markdown(notes: MeetingNotesCanonical) -> str:
    lines: List[str] = []

    lines.append(f"# Meeting {notes.meeting_id} Notes")
    lines.append("")
    lines.append("## Summary")
    lines.append(notes.summary or "No summary available.")
    lines.append("")

    if notes.purpose:
        lines.append("## Purpose")
        lines.append(f"- {notes.purpose}")
        lines.append("")

    if notes.outcome:
        lines.append("## Outcome")
        lines.append(f"- {notes.outcome}")
        lines.append("")

    if notes.key_points:
        lines.append("## Key Points")
        for item in notes.key_points:
            lines.append(f"- {item}")
        lines.append("")

    if notes.decisions:
        lines.append("## Decisions")
        for item in notes.decisions:
            lines.append(f"- {item.text}")
        lines.append("")

    if notes.risks:
        lines.append("## Risks")
        for item in notes.risks:
            lines.append(f"- {item.text}")
        lines.append("")

    if notes.next_steps:
        lines.append("## Next Steps")
        for item in notes.next_steps:
            lines.append(f"- {item}")
        lines.append("")

    if notes.action_items:
        lines.append("## Action Items")
        for item in notes.action_items:
            suffix = []
            if item.owner:
                suffix.append(f"owner: {item.owner}")
            if item.due_date:
                suffix.append(f"due: {item.due_date}")
            meta = f" ({', '.join(suffix)})" if suffix else ""
            lines.append(f"- {item.text}{meta}")
        lines.append("")

    lines.append("## Metadata")
    lines.append(f"- extractor_version: {notes.metadata.extractor_version}")
    lines.append(f"- validator_version: {notes.metadata.validator_version}")
    lines.append(f"- formatter_version: {notes.metadata.formatter_version}")

    return "\n".join(lines).strip() + "\n"
