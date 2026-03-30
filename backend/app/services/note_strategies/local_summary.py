from __future__ import annotations

import re
from collections import Counter
from typing import Literal

from .base import ActionItem, NotesResult, NotesStrategy

SourceType = Literal["transcript", "slide"]


STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "to",
    "of",
    "in",
    "on",
    "for",
    "is",
    "are",
    "was",
    "were",
    "it",
    "that",
    "this",
    "with",
    "as",
    "at",
    "by",
    "we",
    "you",
    "they",
    "he",
    "she",
    "i",
    "our",
    "their",
    "be",
    "from",
    "will",
    "would",
    "should",
    "could",
    "can",
    "have",
    "has",
    "had",
    "not",
    "if",
    "then",
    "than",
    "so",
    "do",
    "does",
    "did",
    "done",
}

ACTION_VERBS = {
    "send",
    "share",
    "prepare",
    "review",
    "update",
    "draft",
    "schedule",
    "check",
    "follow",
    "create",
    "fix",
    "test",
    "confirm",
    "deliver",
    "finalize",
    "upload",
    "document",
    "investigate",
    "call",
    "verify",
    "complete",
    "move",
    "deploy",
    "implement",
    "add",
    "remove",
    "refactor",
    "improve",
    "validate",
    "publish",
    "release",
}

CUE_PATTERNS = [
    r"\bdecided\b",
    r"\bdecision\b",
    r"\baction item\b",
    r"\baction items\b",
    r"\bnext step\b",
    r"\bnext steps\b",
    r"\bowner\b",
    r"\bdue\b",
    r"\bdeadline\b",
    r"\bwe need to\b",
    r"\blet'?s\b",
    r"\bshould\b",
    r"\bwill\b",
    r"\bgoing to\b",
    r"\bfollow up\b",
    r"\bagreed\b",
]

OWNER_PATTERNS = [
    r"\b([A-Z][a-z]+)\s+will\s+",
    r"\b([A-Z][a-z]+)\s+to\s+",
    r"\bowner[:\-]\s*([A-Z][a-z]+)\b",
]

DUE_PATTERNS = [
    r"\bby\s+([A-Za-z0-9 ,/_-]+)\b",
    r"\b(tomorrow|next week|next month|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
]


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text: str) -> list[str]:
    if not text:
        return []

    normalized = normalize_text(text)

    # keep bullets / slide lines useful
    normalized = normalized.replace("•", ". ")
    normalized = normalized.replace(" - ", ". ")
    normalized = normalized.replace("\n", " ")

    parts = re.split(r"(?<=[.!?])\s+", normalized)
    return [part.strip() for part in parts if part.strip()]


def build_sentence_records(transcript_text: str, slide_text: str) -> list[tuple[str, SourceType]]:
    records: list[tuple[str, SourceType]] = []

    for sentence in split_sentences(transcript_text):
        records.append((sentence, "transcript"))

    for sentence in split_sentences(slide_text):
        records.append((sentence, "slide"))

    return records


def chunk_records(
    records: list[tuple[str, SourceType]],
    max_chars: int = 1800,
) -> list[list[tuple[str, SourceType]]]:
    chunks: list[list[tuple[str, SourceType]]] = []
    current: list[tuple[str, SourceType]] = []
    current_len = 0

    for sentence, source in records:
        if current and current_len + len(sentence) > max_chars:
            chunks.append(current)
            current = [(sentence, source)]
            current_len = len(sentence)
        else:
            current.append((sentence, source))
            current_len += len(sentence)

    if current:
        chunks.append(current)

    return chunks


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9_-]+", text.lower())


def word_freq(sentences: list[str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for sentence in sentences:
        for word in tokenize(sentence):
            if word not in STOPWORDS and len(word) > 2:
                counts[word] += 1
    return counts


def sentence_score(sentence: str, freq: Counter[str], source: SourceType) -> float:
    score = 0.0
    lowered = sentence.lower()

    for word in tokenize(sentence):
        score += freq.get(word, 0)

    for pattern in CUE_PATTERNS:
        if re.search(pattern, lowered):
            score += 8

    if re.search(
        r"\bby (monday|tuesday|wednesday|thursday|friday|tomorrow|next week|next month)\b",
        lowered,
    ):
        score += 6

    if ":" in sentence:
        score += 1

    # Slightly prefer transcript discussion over slide OCR
    if source == "transcript":
        score += 2
    else:
        score += 1

    return score


def dedupe_points(points: list[str]) -> list[str]:
    seen = set()
    out: list[str] = []

    for point in points:
        key = re.sub(r"[^a-z0-9]+", "", point.lower())
        if key and key not in seen:
            seen.add(key)
            out.append(point)

    return out


def make_summary(points: list[str], max_points: int = 4) -> str:
    top = points[:max_points]
    if not top:
        return "No substantial discussion could be summarized."
    return " ".join(top)


def extract_owner(sentence: str) -> str | None:
    for pattern in OWNER_PATTERNS:
        match = re.search(pattern, sentence)
        if match:
            return match.group(1)
    return None


def extract_due(sentence: str) -> str | None:
    for pattern in DUE_PATTERNS:
        match = re.search(pattern, sentence, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def looks_like_action(sentence: str) -> bool:
    lowered = sentence.lower().strip()

    strong_patterns = [
        r"\bneed to\b",
        r"\bneeds to\b",
        r"\bshould\b",
        r"\blet'?s\b",
        r"\baction item\b",
        r"\baction items\b",
        r"\bnext step\b",
        r"\bnext steps\b",
        r"\bfollow up\b",
        r"\bto do\b",
        r"\bowner\b",
        r"\bby (monday|tuesday|wednesday|thursday|friday|tomorrow|next week|next month)\b",
    ]

    if any(re.search(pattern, lowered) for pattern in strong_patterns):
        return True

    owner_future_patterns = [
        r"\b[A-Z][a-z]+\s+will\b",
        r"\b[A-Z][a-z]+\s+to\b",
    ]
    if any(re.search(pattern, sentence) for pattern in owner_future_patterns):
        return True

    return False


def looks_like_decision(sentence: str) -> bool:
    lowered = sentence.lower()
    return any(
        phrase in lowered
        for phrase in [
            "we decided",
            "decision",
            "agreed to",
            "it was decided",
            "we will proceed with",
            "approved",
            "we chose",
        ]
    )


def extract_action_items(records: list[tuple[str, SourceType]]) -> list[ActionItem]:
    items: list[ActionItem] = []

    for sentence, source in records:
        if not looks_like_action(sentence):
            continue

        owner = extract_owner(sentence)
        due = extract_due(sentence)
        confidence = 0.35

        if owner:
            confidence += 0.25
        if due:
            confidence += 0.20
        if re.search(
            r"\b(action item|action items|next step|next steps|follow up)\b",
            sentence,
            re.IGNORECASE,
        ):
            confidence += 0.20
        if source == "transcript":
            confidence += 0.05

        items.append(
            ActionItem(
                owner=owner,
                task=sentence.strip(),
                due=due,
                confidence=min(confidence, 0.95),
            )
        )

    deduped: list[ActionItem] = []
    seen = set()
    for item in sorted(items, key=lambda x: x.confidence, reverse=True):
        key = re.sub(r"[^a-z0-9]+", "", item.task.lower())
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    return deduped[:8]


def extract_decisions(records: list[tuple[str, SourceType]]) -> list[str]:
    decisions = [sentence.strip() for sentence, _source in records if looks_like_decision(sentence)]
    return dedupe_points(decisions)[:5]


class LocalSummaryStrategy(NotesStrategy):
    def generate(self, transcript_text: str, slide_text: str = "") -> NotesResult:
        transcript_text = normalize_text(transcript_text)
        slide_text = normalize_text(slide_text)

        if not transcript_text and not slide_text:
            return NotesResult(
                summary="No transcript or slide content available.",
                key_points=[],
                action_items=[],
                decisions=[],
                model_version="local-summary-v1",
            )

        records = build_sentence_records(transcript_text, slide_text)
        chunks = chunk_records(records, max_chars=1800)

        all_points: list[str] = []
        for chunk in chunks:
            sentences = [sentence for sentence, _source in chunk]
            freq = word_freq(sentences)
            ranked = sorted(
                chunk,
                key=lambda item: sentence_score(item[0], freq, item[1]),
                reverse=True,
            )
            all_points.extend([sentence for sentence, _source in ranked[:3]])

        key_points = dedupe_points(all_points)[:8]
        action_items = extract_action_items(records)
        decisions = extract_decisions(records)
        summary = make_summary(key_points, max_points=4)

        return NotesResult(
            summary=summary,
            key_points=key_points,
            action_items=action_items,
            decisions=decisions,
            model_version="local-summary-v1",
        )
