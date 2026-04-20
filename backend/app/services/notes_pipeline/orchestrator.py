from __future__ import annotations

import re
from typing import Iterable, Optional

from app.schemas.meeting_notes import (
    ActionItem,
    DecisionItem,
    MeetingNotesCanonical,
    RiskItem,
)
from app.services.notes_pipeline.compose import compose_summary

PURPOSE_PATTERNS = (
    r"^the purpose of this meeting is\b",
    r"^the main purpose of (?:today'?s|this) meeting is\b",
    r"^the main purpose is\b",
    r"^purpose:\b",
    r"^today(?:,)? we need to\b",
    r"^we are here to\b",
    r"^the meeting is to\b",
)

OUTCOME_PATTERNS = (
    r"^by the end of the meeting\b",
    r"^the goal is to leave with\b",
    r"^we should leave with\b",
    r"^i(?:'d| would) like us to leave (?:this )?meeting with\b",
    r"^i want us to leave (?:this )?meeting with\b",
    r"^outcome:\b",
)

NEXT_STEP_PREFIXES = (
    "next step",
    "next steps",
    "we will next",
    "after this",
)

DECISION_PREFIXES = (
    "we agreed",
    "we decided",
    "decision:",
    "final decision",
    "the decision is",
    "the first pilot audience will be",
    "the live demo will use",
    "we will keep one backup meeting",
    "the best first audience is",
    "i think the best first audience is",
    "for the pilot, i suggest",
    "let's separate two things clearly",
    "we should have one already processed meeting",
)

BAD_DECISION_PHRASES = (
    "let's talk about",
    "we should discuss",
    "create a brand new meeting",
    "upload the audio",
    "monitor the worker logs",
    "review the ai notes",
    "review the markdown notes",
    "check the summary",
)

ACTION_OWNER_HINTS = (
    "lalita",
    "team",
    "marketing",
    "engineering",
    "product",
    "design",
)

ACTION_VERBS = (
    "prepare",
    "finalize",
    "update",
    "review",
    "benchmark",
    "create",
    "send",
    "share",
    "test",
    "compare",
    "fix",
    "lock",
    "package",
    "keep",
    "confirm",
    "draft",
    "record",
)

BAD_ACTION_PHRASES = (
    "if the live run feels slow",
    "one risk is",
    "the risk is",
    "let's talk about",
    "we should decide",
    "by the end of the meeting",
    "the purpose of this meeting",
    "the first pilot audience will be",
    "the live demo will use",
    "we agreed",
    "we decided",
)

DUE_PATTERNS = (
    r"\bby\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    r"\bthis week\b",
    r"\bnext week\b",
    r"\btomorrow\b",
    r"\btoday\b",
)


def _normalize_sentence(sentence: str) -> str:
    sentence = sentence.strip()
    if not sentence:
        return ""

    sentence = re.sub(r"\b[Ss]peaker\s+(?:One|Two|Three)\s*,?\s*", "", sentence)
    sentence = re.sub(
        r"^(yes|yeah|okay|ok|right|exactly|perfect|sounds good)\s*,\s*",
        "",
        sentence,
        flags=re.IGNORECASE,
    )
    sentence = re.sub(r"\s+", " ", sentence)
    sentence = re.sub(r"\s+,", ",", sentence)
    sentence = re.sub(r",\s*\.", ".", sentence)
    sentence = re.sub(r"\.{2,}", ".", sentence)
    sentence = sentence.strip(" ,")

    if sentence and sentence[0].islower():
        sentence = sentence[0].upper() + sentence[1:]

    if sentence and sentence[-1] not in ".!?":
        sentence += "."

    return sentence


def _to_sentences(text: str) -> list[str]:
    raw_parts = re.split(r"(?<=[.!?])\s+|\n+", text or "")
    out: list[str] = []
    for part in raw_parts:
        sentence = _normalize_sentence(part)
        if sentence:
            out.append(sentence)
    return out


def _dedupe_texts(items: Iterable[str], limit: int) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        norm = re.sub(r"\s+", " ", str(item).strip().lower())
        if not norm or norm in seen:
            continue
        seen.add(norm)
        out.append(str(item).strip())
        if len(out) >= limit:
            break
    return out


def _pick_first(sentences: list[str], patterns: tuple[str, ...]) -> str:
    for sentence in sentences:
        low = sentence.lower()
        if any(re.search(pattern, low) for pattern in patterns):
            return sentence
    return ""


def _is_transcripty(sentence: str) -> bool:
    s = sentence.strip().lower()

    # Only reject truly messy transcript fragments, not normal spoken sentences.
    if len(s.split()) > 50:
        return True
    if s.count(",") >= 5 and len(s.split()) > 35:
        return True
    if s.count(" and ") >= 4 and len(s.split()) > 35:
        return True

    return False


def _is_good_decision(sentence: str) -> bool:
    s = sentence.strip().lower()
    if not s:
        return False
    if _is_transcripty(sentence):
        return False
    if len(s.split()) > 40:
        return False
    if any(bad in s for bad in BAD_DECISION_PHRASES):
        return False
    return any(prefix in s for prefix in DECISION_PREFIXES)


def _extract_decisions(sentences: list[str]) -> list[DecisionItem]:
    out: list[DecisionItem] = []
    seen: set[str] = set()

    for idx, sentence in enumerate(sentences):
        if not _is_good_decision(sentence):
            continue

        norm = sentence.lower()
        if norm in seen:
            continue
        seen.add(norm)

        out.append(
            DecisionItem(
                text=sentence,
                confidence=0.82,
                source_chunk_ids=[idx],
            )
        )
        if len(out) >= 5:
            break

    return out


def _extract_risks(sentences: list[str]) -> list[RiskItem]:
    out: list[RiskItem] = []
    seen: set[str] = set()

    for idx, sentence in enumerate(sentences):
        low = sentence.lower()
        if not (
            "one risk" in low
            or "the risk" in low
            or low.startswith("risk:")
            or "one issue" in low
            or low.startswith("concern:")
            or "watch carefully" in low
        ):
            continue

        if _is_transcripty(sentence):
            continue

        norm = sentence.lower()
        if norm in seen:
            continue
        seen.add(norm)

        out.append(
            RiskItem(
                text=sentence,
                confidence=0.78,
                source_chunk_ids=[idx],
            )
        )
        if len(out) >= 5:
            break

    return out


def _extract_due_date(sentence: str) -> Optional[str]:
    low = sentence.lower()
    for pattern in DUE_PATTERNS:
        match = re.search(pattern, low)
        if match:
            return match.group(0)
    return None


def _extract_owner_and_task(sentence: str) -> tuple[Optional[str], str]:
    clean = sentence.strip()

    owner_patterns = [
        r"^(Lalita)\s+will\s+(.+)$",
        r"^(Team)\s+should\s+(.+)$",
        r"^(Team)\s+will\s+(.+)$",
        r"^(Marketing)\s+should\s+(.+)$",
        r"^(Engineering)\s+should\s+(.+)$",
        r"^(Product)\s+should\s+(.+)$",
        r"^(Design)\s+should\s+(.+)$",
    ]

    for pattern in owner_patterns:
        match = re.match(pattern, clean, flags=re.IGNORECASE)
        if match:
            owner = match.group(1).strip().title()
            task = match.group(2).strip()
            task = task[0].upper() + task[1:] if task else task
            if task and task[-1] not in ".!?":
                task += "."
            return owner, task

    low = clean.lower()
    if any(low.startswith(verb + " ") for verb in ACTION_VERBS):
        return None, clean

    return None, clean


def _is_good_action(sentence: str) -> bool:
    s = sentence.strip().lower()
    if not s:
        return False
    if _is_transcripty(sentence):
        return False
    if len(s.split()) > 35:
        return False
    if any(bad in s for bad in BAD_ACTION_PHRASES):
        return False
    if s.startswith("if "):
        return False

    has_owner = bool(
        re.match(
            r"^(lalita|team|marketing|engineering|product|design)\b.*\b(will|should|need to|needs to)\b",
            s,
        )
    )

    starts_with_action = any(s.startswith(verb + " ") for verb in ACTION_VERBS)

    contains_action = any(
        s.startswith(f"we should {verb} ")
        or s.startswith(f"we will {verb} ")
        or s.startswith(f"{verb} ")
        or f" we should {verb} " in s
        or f" we will {verb} " in s
        or f" let's {verb} " in s
        or f" we need to {verb} " in s
        for verb in ACTION_VERBS
    )

    return has_owner or starts_with_action or contains_action


def _extract_actions(sentences: list[str]) -> list[ActionItem]:
    out: list[ActionItem] = []
    seen: set[str] = set()

    for idx, sentence in enumerate(sentences):
        if not _is_good_action(sentence):
            continue

        owner, task = _extract_owner_and_task(sentence)
        task = _normalize_sentence(task)

        if not task:
            continue

        low_task = task.lower()
        if low_task in seen:
            continue
        seen.add(low_task)

        out.append(
            ActionItem(
                text=task,
                owner=owner,
                due_date=_extract_due_date(sentence),
                confidence=0.90 if owner else 0.78,
                source_chunk_ids=[idx],
            )
        )

        if len(out) >= 6:
            break

    return out


def _extract_next_steps(sentences: list[str]) -> list[str]:
    out: list[str] = []

    for sentence in sentences:
        low = sentence.lower().strip()
        if any(low.startswith(prefix) for prefix in NEXT_STEP_PREFIXES):
            out.append(sentence)

    return _dedupe_texts(out, limit=5)


def _build_key_points(
    purpose: str,
    outcome: str,
    decisions: list[DecisionItem],
    risks: list[RiskItem],
    next_steps: list[str],
    actions: list[ActionItem],
) -> list[str]:
    points: list[str] = []

    if purpose:
        points.append(purpose)
    if outcome:
        points.append(outcome)

    points.extend(item.text for item in decisions[:2])
    points.extend(item.text for item in risks[:2])
    points.extend(next_steps[:2])
    points.extend(item.text for item in actions[:2])

    return _dedupe_texts(points, limit=8)


def _pre_split_transcript_text(transcript_text: str) -> str:
    text = transcript_text or ""

    # Break on speaker tags so multi-speaker blobs do not remain one giant sentence.
    text = re.sub(r"\b[Ss]peaker\s+(?:One|Two|Three)\s*,", ". ", text)
    text = re.sub(r"\b[Ss]peaker\s+(?:One|Two|Three)\s*:", ". ", text)

    # Break on enumerated items and decision markers.
    text = re.sub(r"\b[Dd]ecision\s+(?:one|two|three|four|1|2|3|4)\s*,", ". ", text)
    text = re.sub(r"\b[Ff]irst\s*,", ". First, ", text)
    text = re.sub(r"\b[Ss]econd\s*,", ". Second, ", text)
    text = re.sub(r"\b[Tt]hird\s*,", ". Third, ", text)
    text = re.sub(r"\b[Ff]ourth\s*,", ". Fourth, ", text)
    text = re.sub(r"\b[Ff]ifth\s*,", ". Fifth, ", text)
    text = re.sub(r"\b[Ss]ixth\s*,", ". Sixth, ", text)

    # Break on strong action-assignment cues.
    text = re.sub(r"\b[Ll]alita will\b", ". Lalita will", text)
    text = re.sub(r"\b[Tt]eam will\b", ". Team will", text)
    text = re.sub(r"\b[Tt]eam should\b", ". Team should", text)
    text = re.sub(r"\b[Mm]arketing should\b", ". Marketing should", text)
    text = re.sub(r"\b[Ee]ngineering should\b", ". Engineering should", text)
    text = re.sub(r"\b[Pp]roduct should\b", ". Product should", text)
    text = re.sub(r"\b[Dd]esign should\b", ". Design should", text)

    # Break on next-step phrasing.
    text = re.sub(r"\b[Tt]he next step is to\b", ". The next step is to", text)
    text = re.sub(r"\b[Ii]mmediate next steps\b", ". Immediate next steps", text)

    # Clean up accidental duplicated punctuation/spacing.
    text = re.sub(r"\.\s*\.", ". ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def build_canonical_notes(meeting_id: int, transcript_text: str) -> MeetingNotesCanonical:
    transcript_text = _pre_split_transcript_text(transcript_text)
    sentences = _to_sentences(transcript_text)

    purpose = _pick_first(sentences, PURPOSE_PATTERNS)
    outcome = _pick_first(sentences, OUTCOME_PATTERNS)
    decisions = _extract_decisions(sentences)
    risks = _extract_risks(sentences)
    actions = _extract_actions(sentences)
    next_steps = _extract_next_steps(sentences)
    key_points = _build_key_points(purpose, outcome, decisions, risks, next_steps, actions)

    notes = MeetingNotesCanonical(
        meeting_id=meeting_id,
        summary="",
        purpose=purpose,
        outcome=outcome,
        key_points=key_points,
        decisions=decisions,
        risks=risks,
        next_steps=next_steps,
        action_items=actions,
        metadata={
            "extractor_version": "canonical-tight-v3.1",
            "validator_version": "canonical-tight-v3.1",
            "formatter_version": "canonical-tight-v3.1",
        },
    )
    notes.summary = compose_summary(notes)
    return notes
