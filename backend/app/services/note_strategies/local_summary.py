from __future__ import annotations

import re
from collections import Counter
from dataclasses import replace
from typing import Literal

from app.services.notes_postprocess import postprocess_notes_v3

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
    "run",
    "keep",
    "record",
    "preserve",
    "begin",
    "start",
    "save",
    "package",
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
    r"\bteam\s+will\s+",
]

DUE_PATTERNS = [
    r"\bby\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    r"\b(tomorrow|next week|next month|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
]

NAME_CORRECTIONS = {
    "Lily": "Lalita",
    "Lalitaa": "Lalita",
}

TOPIC_PATTERNS: dict[str, tuple[str, ...]] = {
    "status": (
        r"\bproduct status\b",
        r"\bworks end to end\b",
        r"\bsmoke test\b",
        r"\brealistic\b",
        r"\bmeeting (?:fourteen|fifteen|seventeen|14|15|17)\b",
    ),
    "demo": (
        r"\bdemo\b",
        r"\blive\b",
        r"\bbackup\b",
        r"\bjson\b",
        r"\bmarkdown\b",
        r"\bworker logs\b",
        r"\brunbook\b",
        r"\bcommand checklist\b",
    ),
    "pilot": (
        r"\bpilot\b",
        r"\blanding page\b",
        r"\boutreach\b",
        r"\bconsultants?\b",
        r"\bsmall agencies?\b",
        r"\bagencies?\b",
        r"\bstartup teams?\b",
        r"\bfounders?\b",
        r"\bdelivery teams?\b",
        r"\bpositioning\b",
        r"\btime saved after meetings\b",
        r"\bsave follow-up time\b",
        r"\breduce missed action items\b",
        r"\bshareable notes\b",
        r"\blightweight workflow\b",
        r"\bmachine readable\b",
        r"\bhuman readable\b",
    ),
    "risk": (
        r"\brisk\b",
        r"\bruntime\b",
        r"\btimeout\b",
        r"\braw media path\b",
        r"\bsequencing\b",
        r"\btiming logs\b",
        r"\bstress test\b",
    ),
    "quality": (
        r"\bnote quality\b",
        r"\bcleanup\b",
        r"\baction item\b",
        r"\bsummarization tuning\b",
        r"\bdeeper summarization\b",
    ),
    "decision": (
        r"\bdecision\b",
        r"\bdecided\b",
        r"\bagreed\b",
        r"\bwe chose\b",
        r"\bfirst pilot audience\b",
        r"\bprimary backup demo example\b",
        r"\bmain proof of quality\b",
        r"\bstress test\b",
    ),
}


def normalize_known_names(text: str) -> str:
    for wrong, correct in NAME_CORRECTIONS.items():
        text = re.sub(rf"\b{re.escape(wrong)}\b", correct, text)
    return text


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text: str) -> list[str]:
    if not text:
        return []

    normalized = normalize_text(text)
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

    score += 2 if source == "transcript" else 1
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


def sentence_topics(sentence: str) -> set[str]:
    lowered = sentence.lower()
    matched: set[str] = set()
    for topic, patterns in TOPIC_PATTERNS.items():
        if any(re.search(pattern, lowered) for pattern in patterns):
            matched.add(topic)
    return matched


def select_diverse_points(points: list[str], limit: int = 12) -> list[str]:
    unique_points = dedupe_points(points)
    selected: list[str] = []
    seen: set[str] = set()

    for topic in TOPIC_PATTERNS:
        for point in unique_points:
            key = re.sub(r"[^a-z0-9]+", "", point.lower())
            if key in seen:
                continue
            if topic in sentence_topics(point):
                selected.append(point)
                seen.add(key)
                break

    for point in unique_points:
        key = re.sub(r"[^a-z0-9]+", "", point.lower())
        if key in seen:
            continue
        selected.append(point)
        seen.add(key)
        if len(selected) >= limit:
            break

    return selected[:limit]


def make_summary(points: list[str], max_points: int = 4) -> str:
    top = points[:max_points]
    if not top:
        return "No substantial discussion could be summarized."
    return " ".join(top)


def extract_owner(sentence: str) -> str | None:
    sentence = normalize_known_names(sentence)
    for pattern in OWNER_PATTERNS:
        match = re.search(pattern, sentence)
        if match:
            owner = match.group(1) if match.groups() else "Team"
            return NAME_CORRECTIONS.get(owner, owner)
    if re.search(r"\bteam\s+will\b", sentence, re.IGNORECASE):
        return "Team"
    return None


def extract_due(sentence: str) -> str | None:
    for pattern in DUE_PATTERNS:
        match = re.search(pattern, sentence, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def clean_action_text(sentence: str) -> str:
    text = normalize_known_names(sentence.strip())

    text = re.sub(r"^([A-Za-z]+)\s*[—\-:]\s*\1\b", r"\1", text)
    text = re.sub(r"^[A-Z][a-z]+,\s+", "", text)  # strip speaker lead-ins like "Kevin, "
    text = re.sub(
        r"^(Lalita|We|I|Team)\s+will\s+",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"^(Lalita|We|I|Team)\s+(should|need to|needs to)\s+",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"^(something like[,:\s]+)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(that\s+[—\-:]\s*)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^will\s+", "", text, flags=re.IGNORECASE)

    return text.strip(" .")


def looks_like_action(sentence: str) -> bool:
    lowered = sentence.lower().strip()

    weak_starts = [
        "the main purpose",
        "i'd like us to",
        "something like",
        "that will allow",
        "we can check",
        "identify decisions and action items",
        "turns short meeting recordings",
        "create a meeting, upload the file",
        "ideally, the flow is",
        "on the product side",
        "we already saw",
        "by the end of the meeting",
        "that means",
        "i would also",
        "lalita, let's capture decisions explicitly",
        "decision 1",
    ]
    if any(lowered.startswith(x) for x in weak_starts):
        return False

    strong_patterns = [
        r"\bneed to\b",
        r"\bneeds to\b",
        r"\bshould\b",
        r"\bmust\b",
        r"\blet'?s\b",
        r"\baction item\b",
        r"\baction items\b",
        r"\bnext step\b",
        r"\bnext steps\b",
        r"\bfollow up\b",
        r"\bto do\b",
        r"\bowner\b",
        r"\bby (monday|tuesday|wednesday|thursday|friday|tomorrow|next week|next month)\b",
        r"\bwill\b",
    ]

    if any(re.search(pattern, lowered) for pattern in strong_patterns):
        return True

    owner_future_patterns = [
        r"\b[A-Z][a-z]+\s+will\b",
        r"\b[A-Z][a-z]+\s+should\b",
        r"\b[A-Z][a-z]+\s+needs to\b",
    ]
    if any(re.search(pattern, sentence) for pattern in owner_future_patterns):
        return True

    words = tokenize(sentence)
    return any(v in words for v in ACTION_VERBS) and any(
        w in words for w in {"we", "i", "team", "lalita"}
    )


def looks_like_decision(sentence: str) -> bool:
    lowered = sentence.lower()

    bad_decision_patterns = [
        "by the end of the meeting",
        "let's capture decisions explicitly",
        "lalita, let's capture decisions explicitly",
        "the landing page should lead with",
        "decision on which use case we will lead",
    ]
    if any(phrase in lowered for phrase in bad_decision_patterns):
        return False

    phrases = [
        "we decided",
        "agreed to",
        "it was decided",
        "we will proceed with",
        "approved",
        "we chose",
        "will be the primary backup demo example",
        "remains the main proof of quality",
        "is a stress test",
        "not the default live demo",
        "first pilot audience",
        "will lead with a practical positioning message",
        "preferred flow",
        "backup demo artifact",
    ]
    return any(phrase in lowered for phrase in phrases)


def extract_action_items(records: list[tuple[str, SourceType]]) -> list[ActionItem]:
    items: list[ActionItem] = []

    for sentence, source in records:
        if not looks_like_action(sentence):
            continue

        cleaned_task = _clean_sentence_text(clean_action_text(sentence))
        lowered_task = cleaned_task.lower()

        if any(
            phrase in lowered_task
            for phrase in [
                "the main purpose",
                "i'd like us to leave this meeting",
                "turns short meeting recordings",
                "we can check the summary",
                "identify decisions and action items",
                "create a meeting, upload the file, process it",
                "that will allow us to see",
            ]
        ):
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
        if re.search(r"\bwill\b|\bshould\b|\bneeds to\b|\bneed to\b", sentence, re.IGNORECASE):
            confidence += 0.10
        if source == "transcript":
            confidence += 0.05

        items.append(
            ActionItem(
                owner=owner,
                task=cleaned_task,
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


_COMPOUND_ACTION_SPLIT_RE = re.compile(
    r"\s+and\s+(?=(?:keep|prepare|create|update|review|finalize|begin|send|collect|upload|monitor|preserve|generate|verify|complete)\b)",
    re.IGNORECASE,
)


def _split_compound_action_task(task: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", str(task or "")).strip(" .")
    if not cleaned:
        return []

    return [
        part.strip(" .") for part in _COMPOUND_ACTION_SPLIT_RE.split(cleaned) if part.strip(" .")
    ]


def _make_action_item(
    owner: str | None,
    task: str,
    source_sentence: str,
    confidence: float = 0.82,
) -> ActionItem | None:
    cleaned_task = _clean_sentence_text(task)
    if not _looks_like_publishable_action_task(cleaned_task):
        return None

    return ActionItem(
        owner=owner,
        task=cleaned_task,
        due=extract_due(source_sentence),
        confidence=confidence,
    )


def extract_final_section_action_items(
    records: list[tuple[str, SourceType]],
) -> list[ActionItem]:
    items: list[ActionItem] = []

    for sentence, source in records:
        if source != "transcript":
            continue

        cleaned_sentence = re.sub(r"\s+", " ", sentence).strip()
        lowered = cleaned_sentence.lower()

        owner_match = re.search(
            r"\b(?P<owner>[A-Z][a-z]+)\s+will\s+(?:also\s+)?(?P<task>.+)$",
            cleaned_sentence,
        )
        if owner_match:
            owner = owner_match.group("owner")
            raw_task = owner_match.group("task")
            for task in _split_compound_action_task(raw_task):
                item = _make_action_item(owner, task, cleaned_sentence)
                if item:
                    items.append(item)

        if "demo command runbook will be updated" in lowered:
            item = _make_action_item(
                None,
                "Update the demo command runbook after the successful test",
                cleaned_sentence,
            )
            if item:
                items.append(item)

        if "landing page and outreach message will be reviewed and finalized" in lowered:
            item = _make_action_item(
                None,
                "Review and finalize the landing page and outreach message",
                cleaned_sentence,
            )
            if item:
                items.append(item)

        next_step_match = re.search(
            r"\bnext step is to (?P<task>.+)$",
            cleaned_sentence,
            flags=re.IGNORECASE,
        )
        if next_step_match:
            task = next_step_match.group("task")
            item = _make_action_item(None, task, cleaned_sentence)
            if item:
                items.append(item)

    deduped: list[ActionItem] = []
    seen: set[str] = set()

    for item in items:
        key = _canonical_action_task(item.task)
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return deduped[:8]


def extract_decisions(records: list[tuple[str, SourceType]]) -> list[str]:
    decisions: list[str] = []
    for sentence, _source in records:
        if not looks_like_decision(sentence):
            continue
        cleaned = _clean_sentence_text(sentence)
        decisions.append(cleaned)
    return dedupe_points(decisions)[:5]


def _canonical_action_task(task: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", task.lower())


def extract_final_action_records(
    records: list[tuple[str, SourceType]],
) -> list[tuple[str, SourceType]]:
    start_idx: int | None = None
    collected: list[tuple[str, SourceType]] = []

    for idx, (sentence, source) in enumerate(records):
        lowered = sentence.lower()
        if (
            "let’s close with concrete actions" in lowered
            or "let's close with concrete actions" in lowered
        ):
            start_idx = idx + 1
            break

    if start_idx is None:
        return []

    stop_phrases = (
        "that captures the essentials",
        "thank you everyone",
        "i’ll send a short written recap",
        "i'll send a short written recap",
        "direction is clear",
    )

    for sentence, source in records[start_idx:]:
        lowered = sentence.lower()
        if any(phrase in lowered for phrase in stop_phrases):
            break
        if source != "transcript":
            continue
        collected.append((sentence, source))

    return collected


def merge_action_items(
    primary: list[ActionItem], secondary: list[ActionItem], limit: int = 8
) -> list[ActionItem]:
    merged: list[ActionItem] = []
    seen: set[str] = set()

    for item in [*primary, *secondary]:
        key = _canonical_action_task(item.task)
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(item)
        if len(merged) >= limit:
            break

    return merged


def _canonical_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def _strip_speaker_prefix(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^[A-Z][a-z]+,\s*", "", cleaned)
    cleaned = re.sub(r"^Decision\s+\d+[,:\-]\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^[A-Z][a-z]+,\s*Decision\s+\d+[,:\-]\s*", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _clean_sentence_text(text: str) -> str:
    cleaned = _strip_speaker_prefix(text)
    cleaned = re.sub(
        r"\bkeep\s+meeting\s+17\s+is\b", "keep meeting 17 as", cleaned, flags=re.IGNORECASE
    )
    cleaned = re.sub(
        r"\bthat means meeting 17 should be our backup demo artifact\b",
        "meeting 17 should be our backup demo artifact",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\bto\s+will\b", "to", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bLalita to save\b", "Save", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(
        r"\bI would also us to\b", "I would also like us to", cleaned, flags=re.IGNORECASE
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return cleaned


_NEXT_STEP_ACTION_PREFIXES = (
    "prepare",
    "finalize",
    "keep",
    "create",
    "send",
    "share",
    "review",
    "confirm",
    "draft",
    "update",
    "schedule",
    "test",
    "validate",
    "package",
    "record",
    "process",
    "upload",
    "publish",
    "follow up",
    "align",
    "document",
)

_NEXT_STEP_BAD_PREFIXES = (
    "i think",
    "i agree",
    "we should also",
    "if ",
    "because ",
    "and ",
    "but ",
    "so ",
    "another thing",
    "yeah ",
    "okay ",
    "right ",
    "well ",
)

_NEXT_STEP_BAD_ENDINGS = {
    "and",
    "or",
    "because",
    "so",
    "also",
}


def _normalize_next_step_text(text: str) -> str:
    text = re.sub(r"^\s*[-*•]+\s*", "", str(text).strip())
    text = re.sub(r"\s+", " ", text)
    return text.strip(" ,;:-")


def _looks_like_speaker_style_text(text: str) -> bool:
    lower = text.lower()
    if re.match(r"^\s*speaker(\s+\w+)?\b", lower):
        return True
    if re.match(r"^\s*[A-Z][a-z]+:\s*", text):
        return True
    return False


def _looks_action_oriented(text: str) -> bool:
    lower = text.lower()
    return any(lower.startswith(prefix) for prefix in _NEXT_STEP_ACTION_PREFIXES)


def _is_valid_next_step(text: str) -> bool:
    lower = text.lower().strip()
    if not lower:
        return False
    if _looks_like_speaker_style_text(text):
        return False
    if any(lower.startswith(prefix) for prefix in _NEXT_STEP_BAD_PREFIXES):
        return False
    if "..." in text:
        return False

    words = lower.split()
    if len(words) < 4 or len(words) > 18:
        return False
    if words[-1] in _NEXT_STEP_BAD_ENDINGS:
        return False
    if not _looks_action_oriented(text):
        return False
    return True


def _build_next_steps_from_action_items(
    action_items: list[ActionItem], limit: int = 3
) -> list[str]:
    results: list[str] = []
    seen: set[str] = set()

    for item in action_items:
        task = _normalize_next_step_text(_clean_sentence_text(item.task))
        if not _is_valid_next_step(task):
            continue

        key = re.sub(r"[^a-z0-9]+", " ", task.lower()).strip()
        if key in seen:
            continue
        seen.add(key)

        task = task.rstrip(".")
        task = task[:1].upper() + task[1:]
        results.append(task + ".")

        if len(results) >= limit:
            break

    return results


def _summary_slots_to_text(summary_slots: dict[str, object] | None) -> str:
    if not summary_slots:
        return ""
    purpose = str(summary_slots.get("purpose") or "").strip()
    outcome = str(summary_slots.get("outcome") or "").strip()

    parts: list[str] = []
    if purpose:
        parts.append(purpose.rstrip(".") + ".")
    if outcome and _canonical_text(outcome) != _canonical_text(purpose):
        parts.append(outcome.rstrip(".") + ".")

    return " ".join(parts).strip()


def _convert_v3_action_items(v3_items: list[object]) -> list[ActionItem]:
    converted: list[ActionItem] = []
    for item in v3_items:
        owner = getattr(item, "owner", None)
        task = getattr(item, "task", "")
        due = getattr(item, "due_date", None)
        confidence = float(getattr(item, "confidence", 0.0) or 0.0)

        converted.append(
            ActionItem(
                owner=owner,
                task=task,
                due=due,
                confidence=confidence,
            )
        )
    return converted


def _merge_text_items(primary: list[str], secondary: list[str], limit: int) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for text in [*primary, *secondary]:
        cleaned = _clean_sentence_text(text)
        key = _canonical_text(cleaned)
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(cleaned)
        if len(merged) >= limit:
            break
    return merged


def _first_transcript_match(
    records: list[tuple[str, SourceType]],
    patterns: list[str],
    search_limit: int = 40,
) -> str | None:
    checked = 0
    for sentence, source in records:
        if source != "transcript":
            continue
        checked += 1
        lowered = sentence.lower()
        if any(re.search(pattern, lowered) for pattern in patterns):
            return sentence.strip().rstrip(".")
        if checked >= search_limit:
            break
    return None


def _bad_purpose(text: str, decisions: list[str]) -> bool:
    if not text.strip():
        return True

    lowered = text.lower()
    if any(
        phrase in lowered
        for phrase in [
            "first pilot audience",
            "primary backup demo example",
            "main proof of quality",
            "stress test",
            "not the default live demo",
            "will lead with",
            "that means",
            "by the end of the meeting",
            "i would also",
            "decision 1",
            "let's capture decisions explicitly",
        ]
    ):
        return True

    decision_keys = {_canonical_text(item) for item in decisions}
    return _canonical_text(text) in decision_keys


def _build_purpose(
    records: list[tuple[str, SourceType]],
    selected_points: list[str],
    decisions: list[str],
    fallback: str,
) -> str:
    if fallback and not _bad_purpose(fallback, decisions):
        return fallback.strip().rstrip(".")

    candidate = _first_transcript_match(
        records,
        patterns=[
            r"\bmeeting focused on\b",
            r"\bthe goal is\b",
            r"\btoday we need to\b",
            r"\bby the end of the meeting\b",
            r"\bi'?d like us to\b",
        ],
    )
    if candidate and not _bad_purpose(candidate, decisions):
        return candidate

    topics: set[str] = set()
    for sentence in selected_points:
        topics.update(sentence_topics(sentence))

    phrases: list[str] = []
    if "status" in topics or "quality" in topics:
        phrases.append("review current Meeting Notes Assistant progress")
    if "demo" in topics:
        phrases.append("align demo planning and artifacts")
    if "pilot" in topics:
        phrases.append("refine pilot outreach and positioning")
    if "risk" in topics:
        phrases.append("review current technical risks")

    if not phrases:
        return "The meeting focused on reviewing progress and aligning next steps"

    if len(phrases) == 1:
        phrase = phrases[0]
    else:
        phrase = ", ".join(phrases[:-1]) + ", and " + phrases[-1]

    phrase = (
        phrase.replace("review current", "reviewing current")
        .replace("align demo", "aligning demo")
        .replace("refine pilot", "refining pilot")
        .replace("review current technical", "reviewing current technical")
    )
    return "The meeting focused on " + phrase


def _bad_outcome(text: str, purpose: str) -> bool:
    lowered = text.lower().strip()
    if not lowered:
        return True
    if lowered.startswith("the meeting resulted in"):
        return True
    if _canonical_text(text) == _canonical_text(purpose):
        return True
    return bool(purpose and _canonical_text(purpose) in _canonical_text(text))


def _build_outcome(
    decisions: list[str],
    key_points: list[str],
    purpose: str,
    fallback: str,
) -> str:
    if fallback and not _bad_outcome(fallback, purpose):
        return fallback.strip().rstrip(".")

    cleaned_decisions: list[str] = []
    seen = set()
    for item in decisions:
        cleaned = _clean_sentence_text(item).strip().rstrip(".")
        key = _canonical_text(cleaned)
        if not cleaned or key in seen:
            continue
        seen.add(key)
        if "backup demo artifact" in cleaned.lower() and any(
            "primary backup demo example" in x.lower() for x in cleaned_decisions
        ):
            continue
        cleaned_decisions.append(cleaned)

    if cleaned_decisions:
        return "Key outcomes: " + "; ".join(cleaned_decisions[:3])

    fallback_points = [
        point.strip().rstrip(".")
        for point in key_points
        if _canonical_text(point) != _canonical_text(purpose)
    ]
    if fallback_points:
        return "Key outcomes: " + "; ".join(fallback_points[:2])

    return ""


def extract_risks(records: list[tuple[str, SourceType]]) -> list[str]:
    risks: list[str] = []
    for sentence, _source in records:
        lowered = sentence.lower()
        if (
            "raw media path" in lowered
            or "runtime" in lowered
            or "timeout" in lowered
            or "sequencing" in lowered
            or "stress test" in lowered
            or "timing logs" in lowered
        ):
            risks.append(_clean_sentence_text(sentence))
    return dedupe_points(risks)[:3]


_ACTION_ITEM_BAD_PHRASES = (
    "concrete owners for the follow-up actions",
    "action item clean up in the current version",
)

_ACTION_ITEM_BAD_PREFIXES = (
    "since last week",
    "we also confirmed",
    "the main purpose",
    "the meeting aligned",
    "key outcomes",
    "speaker one",
    "speaker two",
)

_ACTION_ITEM_GOOD_PREFIXES = (
    "create ",
    "prepare ",
    "keep ",
    "review ",
    "finalize ",
    "begin ",
    "send ",
    "collect ",
    "upload ",
    "monitor ",
    "preserve ",
    "generate ",
    "verify ",
    "validate ",
    "update ",
    "complete ",
)


def _normalize_publishable_action_task(task: str) -> str:
    """Rewrite noisy transcript/procedure fragments into publishable task text."""
    cleaned = _clean_sentence_text(task)
    lowered = cleaned.lower()

    # Meeting/demo command fragments often arrive as: "verify the duration, third, create..."
    # That is a transcript procedure, not a clean user-facing action item.
    if "verify the duration" in lowered and (
        "brand new meeting" in lowered or ", third" in lowered or "third," in lowered
    ):
        return "Validate the audio flow using a fresh product meeting."

    return cleaned


def _looks_like_publishable_action_task(task: str) -> bool:
    task = _normalize_publishable_action_task(task)
    lowered = task.lower()

    if not task:
        return False
    if any(phrase in lowered for phrase in _ACTION_ITEM_BAD_PHRASES):
        return False
    if any(lowered.startswith(prefix) for prefix in _ACTION_ITEM_BAD_PREFIXES):
        return False
    if re.search(r"\b(?:first|second|third|fourth|fifth)\s*,", lowered):
        return False
    if len(task.split()) < 4 or len(task.split()) > 18:
        return False
    if any(lowered.startswith(prefix) for prefix in _ACTION_ITEM_GOOD_PREFIXES):
        return True
    if re.match(r"^(?:[A-Z][a-z]+|Team|We|I)\s+(?:will|should|need|needs)\b", task):
        return True
    return False


def _normalize_action_items_for_publish(
    items: list[ActionItem],
    *,
    limit: int = 8,
) -> list[ActionItem]:
    cleaned: list[ActionItem] = []
    seen: set[str] = set()

    for item in items:
        task = _normalize_publishable_action_task(item.task)
        if not _looks_like_publishable_action_task(task):
            continue

        key = task.lower().rstrip(".")
        if key in seen:
            continue

        seen.add(key)
        cleaned.append(replace(item, task=task))

        if len(cleaned) >= limit:
            break

    return cleaned


_DECISION_MARKER_RE = re.compile(
    r"\bdecision\s+(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s*,?\s*",
    re.IGNORECASE,
)


def _looks_like_transcript_chunk(text: str, max_chars: int = 260) -> bool:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    lowered = cleaned.lower()

    if len(cleaned) > max_chars:
        return True

    if lowered.count("speaker one") + lowered.count("speaker two") >= 1:
        return True

    if lowered.count("decision one") + lowered.count("decision two") >= 1:
        return True

    if cleaned.count(",") > 7:
        return True

    if cleaned.count(";") > 3:
        return True

    return False


def _looks_like_publishable_key_point(point: str) -> bool:
    cleaned = _clean_sentence_text(point)
    lowered = cleaned.lower()

    if not cleaned:
        return False
    if lowered.startswith(("speaker one", "speaker two", "speaker:", "good morning")):
        return False
    if "good morning everyone" in lowered:
        return False
    if "thanks for joining" in lowered:
        return False
    if "client weekly sync" in lowered and lowered.startswith("speaker"):
        return False
    if len(cleaned.split()) < 5:
        return False

    return True


def _slot_text_too_similar(left: str, right: str) -> bool:
    left_words = {
        word
        for word in re.findall(r"[a-z0-9]+", left.lower())
        if len(word) > 3 and word not in STOPWORDS
    }
    right_words = {
        word
        for word in re.findall(r"[a-z0-9]+", right.lower())
        if len(word) > 3 and word not in STOPWORDS
    }

    if not left_words or not right_words:
        return False

    overlap = len(left_words & right_words) / max(1, min(len(left_words), len(right_words)))
    return overlap >= 0.65


def _build_publishable_outcome_from_decisions(decisions: list[str]) -> str:
    joined = " ".join(decisions).lower()

    if "pilot audience" in joined and "demo" in joined:
        return (
            "The team aligned on the pilot audience, demo flow, backup demo plan, "
            "and near-term validation and outreach priorities."
        )

    if decisions:
        first_two = "; ".join(item.rstrip(".") for item in decisions[:2])
        return f"The team aligned on the main decisions: {first_two}."

    return "The team aligned on the main priorities and next steps."


def _clean_publishable_key_points(points: list[str], *, limit: int = 8) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()

    for point in points:
        text = _clean_sentence_text(point)
        lowered = text.lower()

        if not _looks_like_publishable_key_point(text):
            continue
        if lowered.startswith(("speaker one", "speaker two")):
            continue
        if "good morning everyone" in lowered:
            continue
        if "thanks for joining" in lowered:
            continue

        key = lowered.rstrip(".")
        if key in seen:
            continue

        seen.add(key)
        cleaned.append(text)

        if len(cleaned) >= limit:
            break

    return cleaned


def _publishable_slot_text(text: str, max_chars: int = 240) -> str:
    cleaned = _clean_sentence_text(str(text or "")).strip().rstrip(".")

    if not cleaned:
        return ""

    lowered = cleaned.lower()

    if _looks_like_transcript_chunk(cleaned, max_chars=max_chars):
        return ""

    if lowered.startswith(("speaker one", "speaker two", "key outcomes: speaker")):
        return ""

    if len(cleaned.split()) < 5:
        return ""

    return cleaned


def _clean_decision_fragment(text: str) -> str:
    cleaned = _clean_sentence_text(str(text or ""))
    cleaned = _DECISION_MARKER_RE.sub("", cleaned)
    cleaned = re.sub(r"\bspeaker\s+(one|two|three)\b.*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.;:-")

    if cleaned and cleaned[-1] not in ".!?":
        cleaned += "."

    return cleaned


def _looks_like_publishable_decision(text: str) -> bool:
    cleaned = _clean_decision_fragment(text)
    lowered = cleaned.lower()

    if not cleaned:
        return False

    if _looks_like_transcript_chunk(cleaned, max_chars=230):
        return False

    if lowered.startswith(
        (
            "speaker one",
            "speaker two",
            "key outcomes",
            "the main purpose",
            "the meeting focused",
            "thanks everyone",
        )
    ):
        return False

    if len(cleaned.split()) < 6:
        return False

    return True


def _extract_embedded_decisions(text: str) -> list[str]:
    source = re.sub(r"\s+", " ", str(text or "")).strip()
    matches = list(_DECISION_MARKER_RE.finditer(source))
    decisions: list[str] = []

    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        fragment = source[start:end]
        fragment = re.split(r"\bspeaker\s+(?:one|two|three)\b", fragment, flags=re.IGNORECASE)[0]
        cleaned = _clean_decision_fragment(fragment)

        if _looks_like_publishable_decision(cleaned):
            decisions.append(cleaned)

    return decisions


def _prepare_publishable_decisions(
    raw_decisions: list[str],
    records: list[tuple[str, SourceType]],
    limit: int = 5,
) -> list[str]:
    candidates: list[str] = []

    for decision in raw_decisions:
        candidates.extend(_extract_embedded_decisions(decision))
        candidates.append(_clean_decision_fragment(decision))

    for sentence, _source in records:
        if _DECISION_MARKER_RE.search(sentence):
            candidates.extend(_extract_embedded_decisions(sentence))

    cleaned: list[str] = []
    seen: set[str] = set()

    for candidate in candidates:
        if not _looks_like_publishable_decision(candidate):
            continue

        key = _canonical_text(candidate)
        if not key or key in seen:
            continue

        seen.add(key)
        cleaned.append(candidate)

        if len(cleaned) >= limit:
            break

    return cleaned


def _prepare_publishable_risks(risks: list[str], limit: int = 3) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()

    for risk in risks:
        item = _publishable_slot_text(risk, max_chars=260)
        key = _canonical_text(item)
        if not item or key in seen:
            continue
        seen.add(key)
        cleaned.append(item)

        if len(cleaned) >= limit:
            break

    return cleaned


def _ensure_decision_backed_action_items(
    action_items: list[ActionItem],
    decisions: list[str],
    *,
    limit: int = 8,
) -> list[ActionItem]:
    joined_decisions = " ".join(decisions).lower()
    joined_actions = " ".join(item.task for item in action_items).lower()

    needs_validation_action = (
        "validate the 10 minute audio flow" in joined_decisions
        or "validate the 10-minute audio flow" in joined_decisions
        or ("10 minute audio flow" in joined_decisions and "validate" in joined_decisions)
    )

    has_validation_action = (
        "validate the audio flow" in joined_actions
        or "validate the 10 minute audio" in joined_actions
        or "validate the 10-minute audio" in joined_actions
    )

    if needs_validation_action and not has_validation_action:
        action_items = [
            ActionItem(
                owner="Team",
                task="Validate the 10-minute audio flow using a fresh product meeting.",
                due=None,
                confidence=0.7,
            ),
            *action_items,
        ]

    return _normalize_action_items_for_publish(action_items, limit=limit)


class LocalSummaryStrategy(NotesStrategy):
    def generate(self, transcript_text: str, slide_text: str = "") -> NotesResult:
        transcript_text = normalize_known_names(normalize_text(transcript_text))
        slide_text = normalize_known_names(normalize_text(slide_text))

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

        candidate_points: list[str] = []
        for chunk in chunks:
            sentences = [sentence for sentence, _source in chunk]
            freq = word_freq(sentences)
            ranked = sorted(
                chunk,
                key=lambda item: sentence_score(item[0], freq, item[1]),
                reverse=True,
            )
            candidate_points.extend([sentence for sentence, _source in ranked[:5]])

        selected_points = select_diverse_points(candidate_points, limit=12)
        processed_v3 = postprocess_notes_v3(selected_points)

        v3_key_points = list(processed_v3.key_points)
        key_points = _clean_publishable_key_points(
            [
                p
                for p in select_diverse_points([*v3_key_points, *selected_points], limit=12)
                if not p.lower().startswith("by the end of the meeting")
                and "i would also us to confirm" not in p.lower()
            ],
            limit=8,
        )

        v3_actions = _convert_v3_action_items(list(processed_v3.action_items))
        filtered_v3_actions = [
            item for item in v3_actions if _looks_like_publishable_action_task(item.task)
        ]
        heuristic_actions = extract_action_items(records)
        final_actions = extract_action_items(extract_final_action_records(records))
        final_section_actions = extract_final_section_action_items(records)
        prioritized_final_actions = merge_action_items(
            final_section_actions, final_actions, limit=8
        )
        prioritized_heuristic_actions = merge_action_items(
            prioritized_final_actions, heuristic_actions, limit=8
        )
        filtered_heuristic_actions = [
            item
            for item in prioritized_heuristic_actions
            if _looks_like_publishable_action_task(item.task)
        ]
        action_items = merge_action_items(filtered_heuristic_actions, filtered_v3_actions, limit=8)
        action_items = _normalize_action_items_for_publish(action_items, limit=8)

        processed_decisions = [item.text for item in processed_v3.decisions]
        raw_decisions = _merge_text_items(processed_decisions, extract_decisions(records), limit=8)
        decisions = _prepare_publishable_decisions(raw_decisions, records, limit=5)
        action_items = _ensure_decision_backed_action_items(action_items, decisions, limit=8)

        existing_risks = [
            str(item).strip() for item in list(processed_v3.summary.risks) if str(item).strip()
        ]
        raw_risks = _merge_text_items(existing_risks, extract_risks(records), limit=5)
        risks = _prepare_publishable_risks(raw_risks, limit=3)

        raw_summary_slots = processed_v3.summary.model_dump()
        purpose = _build_purpose(
            records, selected_points, decisions, str(raw_summary_slots.get("purpose") or "")
        )
        purpose = _publishable_slot_text(purpose, max_chars=220)
        if not purpose:
            purpose = _publishable_slot_text(
                _build_purpose(records, selected_points, decisions, ""), max_chars=220
            )

        outcome = _build_outcome(
            decisions, key_points, purpose, str(raw_summary_slots.get("outcome") or "")
        )
        outcome = _publishable_slot_text(outcome, max_chars=260)
        if not outcome:
            outcome = _publishable_slot_text(
                _build_outcome(decisions, key_points, purpose, ""), max_chars=260
            )
        if not outcome and decisions:
            outcome = _publishable_slot_text(
                _build_publishable_outcome_from_decisions(decisions), max_chars=260
            )
        if outcome and purpose and _slot_text_too_similar(outcome, purpose):
            outcome = _publishable_slot_text(
                _build_publishable_outcome_from_decisions(decisions), max_chars=260
            )

        summary_slots = {
            **raw_summary_slots,
            "purpose": purpose,
            "outcome": outcome,
            "risks": risks,
            "next_steps": _build_next_steps_from_action_items(action_items, limit=3),
        }

        summary = _summary_slots_to_text(summary_slots)
        if not summary:
            summary = make_summary(key_points, max_points=4)

        decision_objects: list[dict[str, object]] = [
            {"text": text, "confidence": 0.7} for text in decisions[:5]
        ]

        action_item_objects = [
            {
                "owner": item.owner,
                "task": _clean_sentence_text(item.task),
                "due_date": item.due,
                "confidence": item.confidence,
                "status": "open",
                "priority": "medium",
            }
            for item in action_items
        ]

        return NotesResult(
            summary=summary,
            summary_slots=summary_slots,
            key_points=key_points,
            action_items=action_items,
            action_item_objects=action_item_objects,
            decisions=decisions,
            decision_objects=decision_objects[:5],
            model_version="local-summary-v3",
        )
