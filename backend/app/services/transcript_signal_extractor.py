from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")
_WORD_RE = re.compile(r"[a-z0-9]+")
_DATE_RE = re.compile(
    r"\b20\d{2}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?\b|"
    r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}\b",
    re.IGNORECASE,
)

_DECISION_CUES = (
    "agreed to",
    "agreed that",
    "approved",
    "confirmed",
    "decided",
    "decision",
    "final decision",
    "keep",
    "limit",
    "use",
    "we will",
    "will use",
    "will keep",
    "will limit",
    "will not",
    "do not",
    "do n't",
)

_ACTION_CUES = (
    "action",
    "action item",
    "assign",
    "assigned",
    "circulate",
    "complete",
    "confirm",
    "document",
    "follow up",
    "prepare",
    "review",
    "run",
    "send",
    "share",
    "upload",
    "verify",
    "will",
    "needs to",
    "need to",
    "owner",
)

_RISK_CUES = (
    "risk",
    "risks",
    "concern",
    "concerns",
    "blocker",
    "blocked",
    "blocking",
    "delay",
    "delays",
    "delayed",
    "dependency",
    "dependencies",
    "scope creep",
    "over-promising",
    "overpromising",
    "unrealistic",
    "stale",
    "unprepared",
    "pricing confirmation",
    "pricing delay",
    "miss",
    "missed",
    "missing",
    "failure",
    "failed",
    "unstable",
    "low confidence",
    "quality issue",
    "accuracy issue",
    "compliance",
    "privacy",
    "security",
    "may delay",
    "may reduce",
    "may create",
    "might delay",
    "could delay",
    "could reduce",
    "could create",
    "without",
    "unless",
)


_NAME_RE = re.compile(
    r"\b(Priya|Jordan|Alex|Morgan|Sam|Taylor|Casey|Riley|Avery|Speaker\s+[A-Z]|[A-Z][a-z]+)\b"
)

_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "use",
    "with",
    "will",
    "we",
}


def _sentences(text: str) -> list[str]:
    results: list[str] = []

    for raw in _SENTENCE_SPLIT_RE.split(text):
        sentence = " ".join(raw.split())
        if len(sentence.split()) < 4:
            continue
        results.append(sentence)

    return results


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in _WORD_RE.findall(text.lower())
        if token not in _STOP_WORDS and len(token) > 1
    }


def _dedupe_keep_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []

    for item in items:
        key = " ".join(sorted(_tokens(item)))
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return deduped


def _contains_any(text: str, cues: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(cue in lowered for cue in cues)


def _clean_decision(sentence: str) -> str:
    cleaned = sentence.strip(" -•\t")
    cleaned = re.sub(
        r"^(decision|decisions|we decided|the team decided)\s*[:\-]\s*", "", cleaned, flags=re.I
    )
    return cleaned.strip()


def _owner_from_sentence(sentence: str) -> str | None:
    match = _NAME_RE.search(sentence)
    if not match:
        return None

    owner = match.group(1).strip()
    if owner.lower() in {"action", "decision", "risk", "meeting", "summary"}:
        return None

    return owner


def _deadline_from_sentence(sentence: str) -> str | None:
    match = _DATE_RE.search(sentence)
    return match.group(0) if match else None


def extract_decisions_from_transcript(
    transcript: str,
    *,
    max_decisions: int = 14,
) -> list[str]:
    candidates: list[str] = []

    for sentence in _sentences(transcript):
        if _contains_any(sentence, _ACTION_CUES) and not _contains_any(sentence, _DECISION_CUES):
            continue

        if _contains_any(sentence, _DECISION_CUES):
            candidates.append(_clean_decision(sentence))

    return _dedupe_keep_order(candidates)[:max_decisions]


def extract_actions_from_transcript(
    transcript: str,
    *,
    max_actions: int = 14,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    for sentence in _sentences(transcript):
        if not _contains_any(sentence, _ACTION_CUES):
            continue

        # Avoid turning decision-only statements into action items unless there is an owner.
        owner = _owner_from_sentence(sentence)
        if owner is None and "action" not in sentence.lower():
            continue

        actions.append(
            {
                "owner": owner,
                "action": sentence.strip(" -•\t"),
                "deadline": _deadline_from_sentence(sentence),
            }
        )

    deduped_actions: list[dict[str, Any]] = []
    seen: set[str] = set()

    for action in actions:
        key = " ".join(
            sorted(_tokens(str(action.get("owner") or "") + " " + str(action.get("action") or "")))
        )
        if not key or key in seen:
            continue
        seen.add(key)
        deduped_actions.append(action)

    return deduped_actions[:max_actions]


def _clean_risk(sentence: str) -> str:
    cleaned = sentence.strip(" -•\t")
    cleaned = re.sub(r"^(risk|risks|concern|concerns)\s*[:\-]\s*", "", cleaned, flags=re.I)
    return cleaned.strip()


def extract_risks_from_transcript(
    transcript: str,
    *,
    max_risks: int = 16,
) -> list[str]:
    candidates: list[str] = []

    for sentence in _sentences(transcript):
        lowered = sentence.lower()

        if "no risks" in lowered or "no risk" in lowered or "(none)" in lowered:
            continue

        if _contains_any(sentence, _RISK_CUES):
            candidates.append(_clean_risk(sentence))

    return _dedupe_keep_order(candidates)[:max_risks]


def extract_structured_signals_from_transcript(transcript: str | None) -> dict[str, Any]:
    if not transcript:
        return {
            "decisions": [],
            "action_items": [],
            "risks": [],
        }

    return {
        "decisions": extract_decisions_from_transcript(transcript),
        "action_items": extract_actions_from_transcript(transcript),
        "risks": extract_risks_from_transcript(transcript),
    }
