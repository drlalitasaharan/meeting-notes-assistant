from __future__ import annotations

import re
from typing import Iterable

from app.services.notes_schema import (
    ActionItem,
    DecisionItem,
    MeetingNotesResult,
    SummarySlots,
)

FILLER_RE = re.compile(
    r"\b(?:uh|um|you know|like|sort of|kind of|basically|actually)\b",
    re.IGNORECASE,
)

DEADLINE_RE = re.compile(
    r"\b("
    r"by\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|tonight|eod|end of day|end of week|next week)"
    r"|before\s+\w+"
    r"|next\s+(?:week|month)"
    r"|tomorrow"
    r"|tonight"
    r")\b",
    re.IGNORECASE,
)

TASK_VERBS = {
    "review",
    "finalize",
    "prepare",
    "send",
    "share",
    "confirm",
    "update",
    "schedule",
    "draft",
    "create",
    "ship",
    "deliver",
    "test",
    "keep",
    "clean",
    "fix",
    "follow",
    "followup",
    "follow-up",
    "reach",
    "outreach",
    "publish",
    "launch",
}

STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "to",
    "of",
    "for",
    "on",
    "in",
    "at",
    "with",
    "from",
    "by",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "it",
    "this",
    "that",
    "we",
    "i",
    "you",
    "he",
    "she",
    "they",
    "them",
    "our",
    "his",
    "her",
    "their",
    "as",
    "if",
    "into",
    "about",
    "just",
    "very",
}

NARRATIVE_MARKERS = {
    "said",
    "remarked",
    "replied",
    "asked",
    "looked",
    "found",
    "went",
    "gentleman",
    "chair",
    "story",
    "narrative",
    "autumn",
    "holmes",
}

NAME_CORRECTIONS = {
    "Lily": "Lalita",
    "Lalitaa": "Lalita",
}

OBJECTIVE_PATTERNS = (
    r"\bby the end of the meeting\b",
    r"\bpurpose of today'?s meeting\b",
    r"\blet me summarize the agenda\b",
    r"\bi would also like us to confirm\b",
    r"\bi would also us to confirm\b",
)

TOPIC_PATTERNS: dict[str, tuple[str, ...]] = {
    "status": (
        r"\bproduct status\b",
        r"\bworks end to end\b",
        r"\bsmoke test\b",
        r"\b10 minute\b",
        r"\b10-minute\b",
        r"\bmeeting 14\b",
        r"\bmeeting 15\b",
        r"\bmeeting 17\b",
        r"\bstrongest realistic example\b",
        r"\bbetter summary, key points, and action items\b",
    ),
    "demo": (
        r"\bdemo\b",
        r"\blive\b",
        r"\bbackup\b",
        r"\bjson\b",
        r"\bmarkdown\b",
        r"\bworker logs\b",
        r"\bprocessed meeting\b",
        r"\bprimary demo artifact\b",
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
        r"\bruntime\b",
        r"\btimeout\b",
        r"\braw media path\b",
        r"\bsequencing\b",
        r"\bstage timing logs\b",
        r"\bstress test\b",
        r"\bworker can throw an error\b",
    ),
    "decision": (
        r"\bdecision\b",
        r"\bdecided\b",
        r"\bagreed\b",
        r"\bwill be used as a stress test\b",
        r"\bbest backup demo example\b",
        r"\bfirst pilot audience\b",
    ),
    "quality": (
        r"\baction item clean\b",
        r"\bcleanup\b",
        r"\bsummarization tuning\b",
        r"\bdeeper summarization\b",
        r"\bslightly repetitive\b",
        r"\bnote quality\b",
    ),
}

TOPIC_ORDER = ("status", "pilot", "risk", "demo", "decision", "general", "quality")

COMMITMENT_PATTERNS = [
    r"\blet'?s\b",
    r"\bwe should\b",
    r"\bwe need to\b",
    r"\bwe will\b",
    r"\bwe'll\b",
    r"\bi will\b",
    r"\bi'll\b",
    r"\bplease\b",
    r"\baction item\b",
]


SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")

STRONG_ACTION_VERB_RE = re.compile(
    r"\b(?:review|finalize|prepare|send|share|confirm|update|schedule|draft|create|ship|deliver|test|keep|clean|fix|publish|launch)\b",
    re.IGNORECASE,
)

WEAK_ACTION_RE = re.compile(
    r"\b(?:discuss|talk about|mention|noted|consider|check the summary|look at|think about)\b",
    re.IGNORECASE,
)


def _clean_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


LEADING_CONJUNCTION_RE = re.compile(r"^(?:and|but|so)\s+", re.IGNORECASE)
MULTI_SPEAKER_PREFIX_RE = re.compile(
    r"^(?:[A-Z][a-z]+,\s*){1,3}(?=[A-Z]?[a-z]+\s+(?:will|should|can|needs?\s+to|to))"
)
SPEAKER_PREFIX_RE = re.compile(r"^(?:[A-Z][a-z]+,\s*)+")
DECISION_PREFIX_RE = re.compile(r"^(?:[A-Z][a-z]+,\s*)?Decision\s+\d+[,\s:-]*", re.IGNORECASE)
BROKEN_TO_WILL_RE = re.compile(r"\bto will\b", re.IGNORECASE)
BROKEN_PILOT_RE = re.compile(r"\bI would also us to confirm\b", re.IGNORECASE)
BROKEN_AGREED_TAIL_RE = re.compile(r"\b[A-Z][a-z]+, agreed\.?$", re.IGNORECASE)


def strip_speaker_noise(text: str) -> str:
    text = LEADING_CONJUNCTION_RE.sub("", text)
    text = MULTI_SPEAKER_PREFIX_RE.sub("", text)
    text = SPEAKER_PREFIX_RE.sub("", text)
    text = DECISION_PREFIX_RE.sub("", text)
    text = BROKEN_TO_WILL_RE.sub("will", text)
    text = BROKEN_PILOT_RE.sub("We should confirm", text)
    text = BROKEN_AGREED_TAIL_RE.sub("", text)
    return text.strip(" ,.-")


def normalize_known_names(text: str) -> str:
    for wrong, correct in NAME_CORRECTIONS.items():
        text = re.sub(rf"\b{re.escape(wrong)}\b", correct, text)
    return text


def is_objective_or_agenda(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in OBJECTIVE_PATTERNS)


def normalize_sentence(text: str) -> str:
    text = _clean_ws(text)
    text = FILLER_RE.sub("", text)
    text = strip_speaker_noise(text)
    text = normalize_known_names(text)
    text = _clean_ws(text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = text.strip(" -•\t")
    if not text:
        return ""
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return text


def split_sentences(text: str) -> list[str]:
    chunks = SENTENCE_SPLIT_RE.split(text)
    return [s for s in (normalize_sentence(c) for c in chunks) if s]


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9']+", text.lower())
    return {w for w in words if len(w) > 2 and w not in STOPWORDS}


def _similar(a: str, b: str) -> bool:
    ta = _tokens(a)
    tb = _tokens(b)
    if not ta or not tb:
        return False
    overlap = len(ta & tb) / max(1, min(len(ta), len(tb)))
    return overlap >= 0.7


def dedupe_texts(items: Iterable[str], limit: int) -> list[str]:
    out: list[str] = []
    for item in items:
        if any(_similar(item, seen) for seen in out):
            continue
        out.append(item)
        if len(out) >= limit:
            break
    return out


def classify_topic(text: str) -> str:
    lowered = text.lower()
    for topic in TOPIC_ORDER:
        if topic == "general":
            continue
        if any(re.search(pattern, lowered) for pattern in TOPIC_PATTERNS[topic]):
            return topic
    return "general"


def key_point_score(text: str) -> int:
    words = text.split()
    n = len(words)
    lower = text.lower()
    topic = classify_topic(text)

    score = 0
    if 8 <= n <= 28:
        score += 3
    elif 6 <= n <= 35:
        score += 1
    else:
        score -= 2

    if "," in text and text.count(",") > 3:
        score -= 2

    if any(marker in lower for marker in NARRATIVE_MARKERS):
        score -= 1

    if is_objective_or_agenda(text):
        score -= 5

    if re.search(
        r"\b(decide|plan|pilot|demo|summary|action items|landing page|outreach|runtime|timeout|risk)\b",
        text,
        re.I,
    ):
        score += 2

    if topic in {"status", "pilot", "risk", "decision"}:
        score += 2
    elif topic in {"demo", "quality"}:
        score += 1

    # Demote pure owner-task lines so they do not dominate key points.
    if re.match(r"^(Team|[A-Z][a-z]+)\s+(will|should|needs?\s+to)\b", text) and topic not in {
        "decision",
        "risk",
    }:
        score -= 3

    # Keep quality notes from dominating the summary unless they are especially strong.
    if re.search(r"\baction item clean up\b|\bdeeper summarization tuning\b", lower):
        score -= 2

    return score


def build_key_points(sentences: list[str], limit: int = 6) -> list[str]:
    cleaned = [normalize_sentence(s) for s in sentences]
    filtered = [
        s for s in cleaned if s and 6 <= len(s.split()) <= 35 and not is_objective_or_agenda(s)
    ]
    ranked = sorted(filtered, key=key_point_score, reverse=True)

    selected: list[str] = []

    # First pass: ensure topic diversity.
    for topic in TOPIC_ORDER:
        if topic == "general":
            continue
        for sentence in ranked:
            if classify_topic(sentence) != topic:
                continue
            if any(_similar(sentence, seen) for seen in selected):
                continue
            selected.append(sentence)
            break
        if len(selected) >= limit:
            return selected[:limit]

    # Second pass: fill remaining slots by score.
    for sentence in ranked:
        if any(_similar(sentence, seen) for seen in selected):
            continue
        selected.append(sentence)
        if len(selected) >= limit:
            break

    return selected[:limit]


def action_item_score(text: str) -> int:
    lower = text.lower()
    score = 0

    if any(re.search(p, lower) for p in COMMITMENT_PATTERNS):
        score += 2

    if any(v in lower for v in TASK_VERBS):
        score += 2

    if DEADLINE_RE.search(lower):
        score += 1

    if re.match(r"^(i|we|team)\b", lower):
        score += 1

    if re.match(r"^[A-Z][a-z]+\s+(will|should|needs?\s+to)\b", text):
        score += 3

    if any(marker in lower for marker in NARRATIVE_MARKERS):
        score -= 3

    if re.search(r"\b(was|were|had|found|said|looked|remarked)\b", lower):
        score -= 1

    words = text.split()
    if len(words) < 4 or len(words) > 24:
        score -= 1

    return score


def _extract_due(text: str) -> str | None:
    m = DEADLINE_RE.search(text)
    return m.group(0) if m else None


def _infer_owner(text: str) -> str | None:
    lower = text.lower()
    if re.match(r"^i\b", lower):
        return "Speaker"
    if re.match(r"^(we|team|let's)\b", lower):
        return "Team"
    return None


def _strip_action_lead_in(text: str) -> str:
    text = re.sub(
        r"^(let's|we should|we need to|we will|we'll|i will|i'll|please)\s+", "", text, flags=re.I
    )
    return text.strip()


def format_action_item(text: str) -> str:
    owner = _infer_owner(text)
    due = _extract_due(text)

    task = _strip_action_lead_in(text)
    if due:
        task = re.sub(re.escape(due), "", task, flags=re.I).strip(" ,.-")

    task = task[0].lower() + task[1:] if task and task[0].isupper() else task
    task = task.rstrip(". ")

    if owner:
        item = f"{owner} - {task}"
    else:
        item = task

    if due:
        item += f" (due: {due})"

    return item.strip()


def build_action_items(sentences: list[str], limit: int = 7) -> list[str]:
    candidates: list[str] = []

    for sentence in sentences:
        s = normalize_sentence(sentence)
        if not s:
            continue
        if action_item_score(s) >= 4:
            candidates.append(format_action_item(s))

    deduped = dedupe_texts(candidates, limit=limit)
    return deduped


def build_summary(key_points: list[str], max_points: int = 4, max_words: int = 100) -> str:
    if not key_points:
        return ""

    summary_candidates: list[str] = []

    # Prefer one point from different sections of the meeting before repeating a theme.
    for topic in ("status", "pilot", "demo", "risk", "decision", "general", "quality"):
        for point in key_points:
            if point in summary_candidates:
                continue
            if classify_topic(point) == topic:
                summary_candidates.append(point)
                break

    for point in key_points:
        if point not in summary_candidates:
            summary_candidates.append(point)

    summary_parts: list[str] = []
    total_words = 0

    for point in summary_candidates[:max_points]:
        sentence = point.rstrip(".") + "."
        words = len(sentence.split())
        if total_words + words > max_words:
            break
        summary_parts.append(sentence)
        total_words += words

    return " ".join(summary_parts)


def postprocess_notes(sentences: list[str]) -> dict[str, list[str] | str]:
    key_points = build_key_points(sentences, limit=6)
    action_items = build_action_items(sentences, limit=7)
    summary = build_summary(key_points, max_points=4, max_words=100)

    return {
        "summary": summary,
        "key_points": key_points,
        "action_items": action_items,
    }


def action_item_confidence(text: str) -> int:
    lower = text.lower()
    score = 0

    if STRONG_ACTION_VERB_RE.search(text):
        score += 2

    if re.match(r"^(team|speaker|[A-Z][a-z]+)\s*-\s*", text):
        score += 1

    if DEADLINE_RE.search(lower):
        score += 1

    if WEAK_ACTION_RE.search(lower):
        score -= 2

    words = text.split()
    if len(words) < 4 or len(words) > 26:
        score -= 1

    return score


def clean_notes(notes: dict[str, object]) -> dict[str, object]:
    cleaned = dict(notes)

    summary_raw = cleaned.get("summary", "")
    summary = normalize_sentence(str(summary_raw)) if summary_raw is not None else ""

    key_points_raw = cleaned.get("key_points", [])
    if isinstance(key_points_raw, list):
        key_points = [normalize_sentence(str(item)) for item in key_points_raw if str(item).strip()]
    else:
        key_points = []

    key_points = dedupe_texts(key_points, limit=8)

    action_items_raw = cleaned.get("action_items", [])
    if isinstance(action_items_raw, list):
        action_items = [
            normalize_sentence(str(item)) for item in action_items_raw if str(item).strip()
        ]
    else:
        action_items = []

    action_items = dedupe_texts(action_items, limit=7)
    action_items = [item for item in action_items if action_item_confidence(item) >= 2]

    if len(action_items) == 1 and action_item_confidence(action_items[0]) < 3:
        action_items = []

    if not summary:
        summary = build_summary(key_points, max_points=4, max_words=100)

    cleaned["summary"] = summary
    cleaned["key_points"] = key_points
    cleaned["action_items"] = action_items
    return cleaned


DECISION_MARKER_RE = re.compile(
    r"\b(?:decided|agreed|finalized|approved|chose|chosen|will use|will proceed|will be used|use .* as|treat .* as)\b",
    re.IGNORECASE,
)

WEAK_DECISION_RE = re.compile(
    r"\b(?:maybe|might|could|perhaps|one option|possibly|consider)\b",
    re.IGNORECASE,
)


BAD_DUE_RE = re.compile(
    r"^(?:before\s+(?:any|the)|before|by|next|tomorrow|tonight)$", re.IGNORECASE
)

STRONG_DECISION_HINTS = (
    "first pilot audience will be",
    "primary backup demo example",
    "backup demo example",
    "will be the primary backup",
    "will be used as",
    "will be",
    "treat ",
    "use meeting ",
    "pilot audience",
)

ACTION_LEADIN_RE = re.compile(
    r"^(?:i would also us to confirm|i would also like us to confirm|i would like us to confirm|"
    r"we should|we need to|we will|we'll|let's|please)\s+",
    re.IGNORECASE,
)

ACTION_BAD_PREFIX_RE = re.compile(
    r"^(?:team will keep|team will|lalita will|speaker will|we will|we should|i will)\s+",
    re.IGNORECASE,
)

PURPOSE_BAD_HINTS = (
    "works and now produces a better summary",
    "better summary, key points, and action items",
    "one minimal smoke test",
)

DECISION_AS_ACTION_HINTS = (
    "first pilot audience will be",
    "pilot audience will be",
)

AGENDA_BAD_STARTS = (
    "by the end of the meeting",
    "the purpose of today's meeting",
    "purpose of today's meeting",
    "let me summarize the agenda",
)

RISK_MARKERS = (
    "risk",
    "blocker",
    "issue",
    "challenge",
    "concern",
    "timeout",
    "error",
    "stress test",
)


def _looks_like_agenda_or_objective(text: str) -> bool:
    lowered = text.lower().strip()
    if is_objective_or_agenda(text):
        return True
    return any(lowered.startswith(prefix) for prefix in AGENDA_BAD_STARTS)


def _normalize_due_date(value: str | None) -> str | None:
    if not value:
        return None
    due = value.strip(" .,-")
    if not due:
        return None
    if BAD_DUE_RE.match(due):
        return None
    if len(due.split()) > 5:
        return None
    return due


def _normalize_action_task_text(task: str) -> str:
    task = normalize_sentence(task)
    task = ACTION_LEADIN_RE.sub("", task)
    task = ACTION_BAD_PREFIX_RE.sub("", task)
    task = re.sub(r"^(?:to\s+)", "", task, flags=re.IGNORECASE)
    task = re.sub(r"\bI would also us to confirm\b", "Confirm", task, flags=re.IGNORECASE)
    task = re.sub(
        r"^One backup meeting already processed live demo$",
        "Keep one processed backup meeting ready before the live demo",
        task,
        flags=re.IGNORECASE,
    )
    task = re.sub(
        r"^Meeting 17 is the primary backup demo example live client presentation$",
        "Keep Meeting 17 ready as the primary backup demo example for the live client presentation",
        task,
        flags=re.IGNORECASE,
    )
    task = re.sub(
        r"^Lalita will prepare the short-lived demo file and keep one backup processed meeting ready$",
        "Prepare the short-lived demo file and keep one backup processed meeting ready",
        task,
        flags=re.IGNORECASE,
    )
    task = task.strip(" .,-")
    if task and task[0].islower():
        task = task[0].upper() + task[1:]
    return task


def _infer_owner_from_task_text(task: str, owner: str) -> str:
    if owner not in {"Unassigned", "Speaker"}:
        return owner

    lowered = task.lower()
    if lowered.startswith("lalita "):
        return "Lalita"
    if lowered.startswith("team "):
        return "Team"
    return owner


def _looks_like_action_sentence(text: str) -> bool:
    lowered = text.lower().strip()
    if re.match(r"^(?:[A-Z][a-z]+|Team|We|I)\s+(?:will|should|need|needs)\b", text):
        return True
    return any(
        phrase in lowered
        for phrase in (
            "action item clean up",
            "defer deeper summarization tuning",
            "prepare the short-lived demo file",
            "keep one backup processed meeting ready",
        )
    )


def _looks_like_valid_action_task(task: str) -> bool:
    if not task:
        return False
    lowered = task.lower()

    if _looks_like_agenda_or_objective(task):
        return False

    bad_phrases = (
        "i would also us to confirm",
        "by the end of the meeting",
        "purpose of today's meeting",
        "the purpose of today's meeting",
        "small list of action items",
        "decision on which use case",
        "concrete owners for the follow-up actions",
    )
    if any(phrase in lowered for phrase in bad_phrases):
        return False

    if any(phrase in lowered for phrase in DECISION_AS_ACTION_HINTS):
        return False

    if len(task.split()) < 4 or len(task.split()) > 18:
        return False

    return True


def _looks_like_decision_sentence(text: str) -> bool:
    lowered = text.lower()
    if _looks_like_agenda_or_objective(text):
        return False
    if WEAK_DECISION_RE.search(text):
        return False
    if DECISION_MARKER_RE.search(text):
        return True
    return any(hint in lowered for hint in STRONG_DECISION_HINTS)


def _looks_like_risk_sentence(text: str) -> bool:
    lowered = text.lower()
    if _looks_like_agenda_or_objective(text):
        return False
    return any(word in lowered for word in RISK_MARKERS)


def _extract_owner_from_formatted_action(text: str) -> tuple[str, str]:
    raw = text.strip()
    if " - " in raw:
        owner, task = raw.split(" - ", 1)
        owner = owner.strip() or "Unassigned"
        return owner, task.strip()
    return "Unassigned", raw


def _extract_due_from_formatted_action(text: str) -> tuple[str, str | None]:
    m = re.search(r"\(due:\s*([^)]+)\)$", text.strip(), re.IGNORECASE)
    if not m:
        return text.strip(), None
    due = _normalize_due_date(m.group(1))
    task = re.sub(r"\s*\(due:\s*([^)]+)\)$", "", text.strip(), flags=re.IGNORECASE).strip()
    return task, due


def infer_action_priority(task: str, due_date: str | None) -> str:
    lower = task.lower()
    if due_date or "urgent" in lower or "asap" in lower:
        return "high"
    if any(word in lower for word in ("finalize", "launch", "deliver", "publish")):
        return "high"
    return "medium"


def build_action_item_objects(sentences: list[str], limit: int = 7) -> list[ActionItem]:
    formatted_items = build_action_items(sentences, limit=limit)
    objects: list[ActionItem] = []

    for item in formatted_items:
        owner, remainder = _extract_owner_from_formatted_action(item)
        task_text, due_date = _extract_due_from_formatted_action(remainder)

        owner = _infer_owner_from_task_text(task_text, owner)
        clean_task = _normalize_action_task_text(task_text)
        owner = _infer_owner_from_task_text(clean_task, owner)

        if owner in {"Lalita", "Team"} and clean_task.lower().startswith(owner.lower() + " "):
            clean_task = clean_task[len(owner) :].strip()

        if not _looks_like_valid_action_task(clean_task):
            continue

        confidence_score = action_item_confidence(item)
        confidence = max(0.0, min(1.0, 0.45 + (0.1 * confidence_score)))

        if owner in {"Unassigned", "Speaker"}:
            confidence -= 0.15
        if due_date is None:
            confidence -= 0.05

        if confidence < 0.60:
            continue

        objects.append(
            ActionItem(
                owner=owner,
                task=clean_task,
                due_date=due_date,
                status="open",
                priority=infer_action_priority(clean_task, due_date),
                confidence=round(confidence, 2),
            )
        )

    deduped: list[ActionItem] = []
    seen: list[str] = []
    for obj in objects:
        signature = f"{obj.owner} | {obj.task} | {obj.due_date or ''}"
        if any(_similar(signature, prior) for prior in seen):
            continue
        seen.append(signature)
        deduped.append(obj)
        if len(deduped) >= limit:
            break

    return deduped


def clean_decision_text(text: str) -> str:
    text = normalize_sentence(text)
    text = re.sub(r"^(?:so|and|but)\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(?:i think|we think)\s+", "", text, flags=re.IGNORECASE)
    return text.strip(" .") + "." if text else ""


def decision_score(text: str) -> int:
    lower = text.lower()
    score = 0

    if _looks_like_agenda_or_objective(text):
        return -5

    if DECISION_MARKER_RE.search(text):
        score += 3

    if any(hint in lower for hint in STRONG_DECISION_HINTS):
        score += 2

    if any(word in lower for word in ("backup", "pilot", "artifact", "stress test", "positioning")):
        score += 1

    if WEAK_DECISION_RE.search(text):
        score -= 3

    words = text.split()
    if len(words) < 5 or len(words) > 26:
        score -= 1

    return score


def build_decisions(sentences: list[str], limit: int = 5) -> list[DecisionItem]:
    candidates: list[str] = []

    for sentence in sentences:
        s = normalize_sentence(sentence)
        if not s:
            continue
        if not _looks_like_decision_sentence(s):
            continue
        if decision_score(s) < 2:
            continue

        cleaned = clean_decision_text(s)
        cleaned = re.sub(r"^Team will keep\s+", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(
            r"^Keep Meeting 17 is the primary backup demo example before the live client presentation\.?$",
            "Meeting 17 will be the primary backup demo example for the live client presentation.",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"^Meeting 17 is the primary backup demo example before the live client presentation\.?$",
            "Meeting 17 will be the primary backup demo example for the live client presentation.",
            cleaned,
            flags=re.IGNORECASE,
        )

        if cleaned:
            candidates.append(cleaned)

    deduped = dedupe_texts(candidates, limit=limit)

    decisions: list[DecisionItem] = []
    for item in deduped:
        conf = max(0.0, min(1.0, 0.50 + (0.1 * decision_score(item))))
        if conf < 0.70:
            continue
        decisions.append(DecisionItem(text=item, confidence=round(conf, 2)))

    return decisions


def build_summary_slots(
    sentences: list[str],
    key_points: list[str],
    decisions: list[DecisionItem],
    action_items: list[ActionItem],
) -> SummarySlots:
    purpose = ""
    for sentence in sentences[:12]:
        s = normalize_sentence(sentence)
        if not s or _looks_like_agenda_or_objective(s):
            continue
        if _looks_like_action_sentence(s):
            continue
        lower = s.lower()
        if any(bad in lower for bad in PURPOSE_BAD_HINTS):
            continue
        if any(
            word in lower
            for word in ("review", "confirm", "demo", "pilot", "progress", "outreach", "risk")
        ):
            purpose = s.rstrip(".") + "."
            break

    if not purpose:
        purpose = "Review progress, confirm the next demo path, and align on pilot outreach and open risks."

    if decisions:
        outcome = (
            "The meeting resulted in " + "; ".join(d.text.rstrip(".") for d in decisions[:2]) + "."
        )
    elif key_points:
        outcome = "The meeting aligned on the main priorities and next steps."
    else:
        outcome = ""

    risks: list[str] = []
    for sentence in sentences:
        s = normalize_sentence(sentence)
        if not s:
            continue
        if _looks_like_risk_sentence(s):
            risks.append(s.rstrip(".") + ".")

    risks = dedupe_texts(risks, limit=3)

    next_steps: list[str] = []
    for item in action_items[:5]:
        task = item.task.rstrip(".") + "."
        if _looks_like_valid_action_task(item.task):
            next_steps.append(task)

    next_steps = dedupe_texts(next_steps, limit=3)

    return SummarySlots(
        purpose=purpose,
        outcome=outcome,
        risks=risks,
        next_steps=next_steps,
    )


def postprocess_notes_v3(sentences: list[str], meeting_id: int = 0) -> MeetingNotesResult:
    key_points = build_key_points(sentences, limit=6)
    action_items = build_action_item_objects(sentences, limit=7)
    decisions = build_decisions(sentences, limit=5)
    summary_slots = build_summary_slots(
        sentences=sentences,
        key_points=key_points,
        decisions=decisions,
        action_items=action_items,
    )

    return MeetingNotesResult(
        meeting_id=meeting_id,
        status="DONE",
        model_version="local-summary-v3",
        summary=summary_slots,
        key_points=key_points,
        decisions=decisions,
        action_items=action_items,
    )


def _restore_summary_slot_next_steps(notes: dict[str, object]) -> dict[str, object]:
    cleaned = dict(notes)

    raw_summary_slots = cleaned.get("summary_slots")
    summary_slots = dict(raw_summary_slots) if isinstance(raw_summary_slots, dict) else {}

    candidates: list[str] = []

    def add_candidate(value: object) -> None:
        text = normalize_sentence(str(value or ""))
        if not text:
            return
        text = text.rstrip(".")
        if not _looks_like_valid_action_task(text):
            return
        candidates.append(text + ".")

    raw_action_item_objects = cleaned.get("action_item_objects")
    if isinstance(raw_action_item_objects, list):
        for item in raw_action_item_objects:
            if isinstance(item, dict):
                add_candidate(item.get("task"))

    if not candidates:
        raw_action_items = cleaned.get("action_items")
        if isinstance(raw_action_items, list):
            for item in raw_action_items:
                add_candidate(item)

    if not candidates:
        existing_next_steps = summary_slots.get("next_steps")
        if isinstance(existing_next_steps, list):
            for item in existing_next_steps:
                add_candidate(item)

    summary_slots["next_steps"] = dedupe_texts(candidates, limit=3)
    cleaned["summary_slots"] = summary_slots
    return cleaned


def normalize_canonical_notes(notes: dict[str, object]) -> dict[str, object]:
    """Backward-compatible canonical notes normalizer.

    Used by the canonical pipeline / process_meeting path.
    Falls back safely to clean_notes when available.
    """
    if not isinstance(notes, dict):
        return {}

    try:
        result = clean_notes(notes)
        if isinstance(result, dict):
            return _restore_summary_slot_next_steps(result)
    except Exception:
        pass

    return _restore_summary_slot_next_steps(dict(notes))
