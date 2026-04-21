from __future__ import annotations

import re
from typing import List, Optional

from app.schemas.meeting_notes import (
    ActionItem,
    DecisionItem,
    MeetingNotesCanonical,
    RiskItem,
)

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")

PURPOSE_HINTS = (
    "purpose",
    "goal",
    "objective",
    "today we need",
    "this meeting is",
    "we are here to",
)

OUTCOME_HINTS = (
    "by the end",
    "we should leave with",
    "outcome",
    "result",
    "confirmed",
)

DECISION_HINTS = (
    "decide",
    "decided",
    "agreed",
    "agreement",
    "approved",
    "chosen",
    "we will use",
    "we'll use",
)

RISK_HINTS = (
    "risk",
    "blocker",
    "concern",
    "issue",
    "dependency",
    "challenge",
    "delay",
)

NEXT_STEP_HINTS = (
    "next step",
    "next steps",
    "follow up",
    "follow-up",
    "moving forward",
    "after this",
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


DUE_DATE_PATTERNS = [
    r"\bby (monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    r"\bby (tomorrow|today|next week|this week|end of week|eow)\b",
    r"\b(on|by) \d{1,2}/\d{1,2}(?:/\d{2,4})?\b",
    r"\b(on|by) [A-Z][a-z]+ \d{1,2}(?:, \d{4})?\b",
]


def _clean_sentence(text: str) -> str:
    text = text.strip(" -•\t")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _split_sentences(text: str) -> List[str]:
    raw = SENTENCE_SPLIT_RE.split(text)
    sentences = [_clean_sentence(x) for x in raw]
    return [x for x in sentences if x]


def _contains_hint(text: str, hints: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(h in lower for h in hints)


def _is_purpose_sentence(text: str) -> bool:
    lower = text.lower()
    return _contains_hint(text, PURPOSE_HINTS) and "next step" not in lower


def _is_outcome_sentence(text: str) -> bool:
    lower = text.lower()

    if _is_purpose_sentence(text):
        return False

    if "by the end" in lower:
        return True
    if "we should leave with" in lower:
        return True
    if lower.startswith("confirmed"):
        return True
    if "outcome" in lower or "result" in lower:
        return True

    return False


def _is_decision_sentence(text: str) -> bool:
    return _contains_hint(text, DECISION_HINTS)


def _is_risk_sentence(text: str) -> bool:
    return _contains_hint(text, RISK_HINTS)


def _extract_owner(text: str) -> Optional[str]:
    patterns = [
        r"^([A-Z][a-z]+(?: [A-Z][a-z]+)?)\s+(?:will|should|needs to|need to)\b",
        r"^(Team|Engineering|Product|Marketing|Sales|Design)\s+(?:will|should|needs to|need to)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def _extract_due_date(text: str) -> Optional[str]:
    for pattern in DUE_DATE_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(0)
    return None


def _is_action_candidate(text: str) -> bool:
    lower = text.lower()

    if _is_purpose_sentence(text):
        return False
    if _is_outcome_sentence(text):
        return False
    if _is_decision_sentence(text):
        return False

    if "by the end of the meeting" in lower:
        return False
    if "we should leave with" in lower:
        return False

    if re.search(r"\b[A-Z][a-z]+(?: [A-Z][a-z]+)? will\b", text):
        return True

    if lower.startswith(ACTION_STARTERS):
        return True

    explicit_task_patterns = (
        " should ",
        " will ",
        " need to ",
        " needs to ",
        " follow up ",
        " follow-up ",
        " please ",
        " can you ",
        " could you ",
    )
    if any(p in f" {lower} " for p in explicit_task_patterns):
        return True

    return False


def extract_from_chunks(meeting_id: int, chunks: List[str]) -> MeetingNotesCanonical:
    notes = MeetingNotesCanonical(meeting_id=meeting_id)

    for chunk_id, chunk in enumerate(chunks):
        sentences = _split_sentences(chunk)

        for sentence in sentences:
            if len(sentence) < 12:
                continue

            if not notes.purpose and _is_purpose_sentence(sentence):
                notes.purpose = sentence

            if not notes.outcome and _is_outcome_sentence(sentence):
                notes.outcome = sentence

            if _is_decision_sentence(sentence):
                notes.decisions.append(
                    DecisionItem(
                        text=sentence,
                        confidence=0.82,
                        source_chunk_ids=[chunk_id],
                    )
                )

            if _is_risk_sentence(sentence):
                notes.risks.append(
                    RiskItem(
                        text=sentence,
                        confidence=0.78,
                        source_chunk_ids=[chunk_id],
                    )
                )

            if _contains_hint(sentence, NEXT_STEP_HINTS):
                notes.next_steps.append(sentence)

            if _is_action_candidate(sentence):
                owner = _extract_owner(sentence)
                due_date = _extract_due_date(sentence)
                confidence = 0.70
                if owner:
                    confidence += 0.10
                if due_date:
                    confidence += 0.10

                notes.action_items.append(
                    ActionItem(
                        text=sentence,
                        owner=owner,
                        due_date=due_date,
                        confidence=min(confidence, 0.95),
                        source_chunk_ids=[chunk_id],
                    )
                )

            if len(notes.key_points) < 12:
                notes.key_points.append(sentence)

    return notes
