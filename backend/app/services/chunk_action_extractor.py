from __future__ import annotations

import re
from dataclasses import dataclass

_ACTION_MARKERS = (
    " will ",
    " should ",
    " need to ",
    " needs to ",
    " must ",
    " has to ",
    " have to ",
    " action item",
    " follow up",
    " prepare ",
    " review ",
    " provide ",
    " create ",
    " send ",
    " confirm ",
    " update ",
    " investigate ",
    " validate ",
    " finalize ",
    " document ",
    " share ",
    " test ",
    " resolve ",
)

_DEADLINE_PATTERNS = (
    r"\bby\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    r"\bby\s+(?:today|tomorrow|next week|next month|end of week|eod)\b",
    r"\bbefore\s+[^,.!?;]+",
    r"\bnext\s+(?:week|month|quarter)\b",
    r"\btomorrow\b",
    r"\btoday\b",
    r"\bthis\s+(?:week|month|quarter)\b",
)


@dataclass(frozen=True)
class TranscriptChunk:
    index: int
    text: str
    start_word: int
    end_word: int


@dataclass(frozen=True)
class CandidateAction:
    action: str
    owner: str
    deadline: str
    reason_context: str
    related_decision: str
    related_risk: str
    source_chunk: int
    confidence: str


def chunk_transcript(transcript: str, *, max_words: int = 900) -> list[TranscriptChunk]:
    """Split transcript into word-bounded chunks while preserving sequence order."""

    words = transcript.split()
    if not words:
        return []

    chunks: list[TranscriptChunk] = []
    for start in range(0, len(words), max_words):
        end = min(start + max_words, len(words))
        chunks.append(
            TranscriptChunk(
                index=len(chunks) + 1,
                text=" ".join(words[start:end]),
                start_word=start,
                end_word=end,
            )
        )

    return chunks


def extract_candidate_actions(
    transcript: str,
    *,
    max_words_per_chunk: int = 900,
) -> list[CandidateAction]:
    """Extract conservative action candidates from transcript chunks.

    This is intentionally heuristic and safe. It creates source-chunk-aware
    candidates before the later model/pipeline consolidation layer.
    """

    candidates: list[CandidateAction] = []

    for chunk in chunk_transcript(transcript, max_words=max_words_per_chunk):
        for statement in _split_statements(chunk.text):
            candidate = _candidate_from_statement(statement, chunk.index)
            if candidate is not None:
                candidates.append(candidate)

    return candidates


def _split_statements(text: str) -> list[str]:
    return [
        statement.strip() for statement in re.split(r"(?<=[.!?])\s+|\n+", text) if statement.strip()
    ]


def _candidate_from_statement(statement: str, source_chunk: int) -> CandidateAction | None:
    if not _looks_actionable(statement):
        return None

    owner, action = _extract_owner_and_action(statement)
    if not action:
        return None

    return CandidateAction(
        action=action,
        owner=owner,
        deadline=_extract_deadline(statement),
        reason_context=statement.strip(),
        related_decision="",
        related_risk="",
        source_chunk=source_chunk,
        confidence=_confidence(owner, statement),
    )


def _looks_actionable(statement: str) -> bool:
    normalized = f" {statement.lower()} "
    return any(marker in normalized for marker in _ACTION_MARKERS)


def _extract_owner_and_action(statement: str) -> tuple[str, str]:
    speaker, body = _split_speaker(statement)

    first_person_match = re.search(
        r"\b(?:i will|i'll|i can|i should)\s+(?P<action>.+)",
        body,
        flags=re.IGNORECASE,
    )
    if first_person_match:
        return speaker or "Unassigned", _clean_action(first_person_match.group("action"))

    named_owner_match = re.search(
        r"\b(?P<owner>[A-Z][A-Za-z0-9_-]*(?:\s+[A-Z][A-Za-z0-9_-]*)?|Speaker\s+[A-Z])\s+"
        r"(?P<marker>will|should|needs to|need to|must|has to|have to|can)\s+"
        r"(?P<action>.+)",
        body,
        flags=re.IGNORECASE,
    )
    if named_owner_match:
        return (
            named_owner_match.group("owner").strip(),
            _clean_action(named_owner_match.group("action")),
        )

    unassigned_match = re.search(
        r"\b(?:we need to|we should|need to|needs to|action item:?|follow up to)\s+"
        r"(?P<action>.+)",
        body,
        flags=re.IGNORECASE,
    )
    if unassigned_match:
        return "Unassigned", _clean_action(unassigned_match.group("action"))

    if speaker:
        return speaker, _clean_action(body)

    return "Unassigned", _clean_action(body)


def _split_speaker(statement: str) -> tuple[str, str]:
    match = re.match(
        r"^(?P<speaker>Speaker\s+[A-Z]|[A-Z][A-Za-z0-9_-]+):\s*(?P<body>.+)$", statement
    )
    if not match:
        return "", statement.strip()

    return match.group("speaker").strip(), match.group("body").strip()


def _extract_deadline(statement: str) -> str:
    for pattern in _DEADLINE_PATTERNS:
        match = re.search(pattern, statement, flags=re.IGNORECASE)
        if match:
            return match.group(0).strip()

    return "No deadline stated"


def _clean_action(action: str) -> str:
    cleaned = action.strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.rstrip(" .;")
    return cleaned


def _confidence(owner: str, statement: str) -> str:
    normalized = statement.lower()

    if owner != "Unassigned" and any(
        marker in normalized for marker in (" will ", " should ", " needs to ")
    ):
        return "high"

    if owner != "Unassigned":
        return "medium"

    return "low"
