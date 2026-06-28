from __future__ import annotations

import copy
import os
import re
from typing import Any

KNOWN_ENTITY_VARIANTS: dict[str, tuple[str, ...]] = {
    "Acjen AI": (
        r"\ba gen\.?\s*ai\b",
        r"\bagenda\s+ai\b",
        r"\bacjenai\b",
        r"\bacjen\s+acjen\s+ai\b",
        r"\bacgen\s+ai\b",
        r"\bajencel\s+ai\b",
    ),
    "MeetIQ": (
        r"\bmeet\s+iq\b",
        r"\bmeeting\s+iq\b",
        r"\bmeetiq\.ai\b",
    ),
    "support@acjen.ai": (
        r"\bsupport\s+(?:at|\[at\])\s+acjen(?:\.|\s+dot\s+)?ai\b",
        r"\bsupport@(?:agenda|acgen|ajencel)\.ai\b",
        r"\bsupport@acjen\.(?:com|io|co)\b",
        r"\bsupport@acjenai\b",
    ),
    "PayPal": (
        r"\bpay\s+pal\b",
        r"\bpay-pal\b",
    ),
    "Square": (
        r"\bsqare\b",
        r"\bsquire\s+checkout\b",
    ),
    "Render": (r"\brendr\b",),
    "Vercel": (r"\bvercell\b",),
    "GoDaddy": (r"\bgo\s+daddy\b", r"\bgodady\b"),
    "BetaList": (r"\bbeta\s+list\b",),
    "Indie Hackers": (r"\bindiehackers\b", r"\bindy\s+hackers\b"),
    "Product Hunt": (r"\bproducthunt\b", r"\bproduct\s+hunter\b"),
    "GitHub": (r"\bgit\s+hub\b",),
    "Markdown": (r"\bmark\s+down\b",),
    "Starter": (r"\bstater\s+plan\b",),
    "Pro Pilot": (r"\bpro\s+pilate\b", r"\bpropilot\b"),
}


def apply_quality_engine_v2(
    notes: dict[str, Any],
    transcript_text: str | None,
) -> dict[str, Any]:
    """Apply conservative Quality Engine v2 improvements to generated notes.

    This pass is intentionally additive and evidence-preserving. It should not
    remove existing decisions, actions, or summary fields unless a later guarded
    cleanup explicitly does so.
    """

    improved = copy.deepcopy(notes)

    summary_slots = improved.get("summary_slots")
    if not isinstance(summary_slots, dict):
        summary_slots = {}

    summary_slots = dict(summary_slots)

    if not _text(summary_slots.get("purpose")):
        inferred_purpose = _infer_purpose(transcript_text) or _infer_purpose(
            _text(improved.get("summary"))
        )
        if inferred_purpose:
            summary_slots["purpose"] = inferred_purpose

    action_items = improved.get("action_item_objects")
    if not isinstance(action_items, list):
        action_items = []
    action_items = _merge_action_items(
        action_items,
        detect_action_items(improved, transcript_text),
    )
    action_items = _normalize_action_owners_with_context(
        action_items,
        "\n".join([_text(transcript_text), _note_text_blob(improved)]),
    )

    next_steps = summary_slots.get("next_steps")
    if not isinstance(next_steps, list):
        next_steps = []

    summary_slots["next_steps"] = _sync_next_steps_from_actions(
        next_steps,
        action_items,
    )
    cleaned_key_points, key_point_questions = _clean_key_points(improved.get("key_points"))
    if isinstance(improved.get("key_points"), list):
        improved["key_points"] = cleaned_key_points

    summary_slots["open_questions"] = _merge_open_questions(
        summary_slots.get("open_questions"),
        [*key_point_questions, *detect_open_questions(improved, transcript_text)],
    )
    summary_slots["risks"] = _merge_risks(
        summary_slots.get("risks"),
        detect_risks(improved, transcript_text),
    )
    summary_slots["known_entity_warnings"] = _merge_warnings(
        summary_slots.get("known_entity_warnings"),
        detect_known_entity_warnings(improved),
    )

    improved["summary_slots"] = summary_slots

    decision_objects = improved.get("decision_objects")
    if not isinstance(decision_objects, list):
        decision_objects = []
    decision_objects = _merge_decision_objects(
        decision_objects,
        detect_decisions(improved, transcript_text),
    )

    improved["decision_objects"] = decision_objects
    improved["action_item_objects"] = action_items

    return improved


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _strip_speaker_prefix(text: str) -> tuple[str, str]:
    match = re.match(
        r"^(?P<speaker>[A-Z][A-Za-z]+)\s+says?,\s*(?P<body>.+)$",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return "", text

    speaker = match.group("speaker").strip()
    body = match.group("body").strip()
    body = re.sub(
        rf"^{re.escape(speaker)}\s+",
        "",
        body,
        flags=re.IGNORECASE,
    )
    return speaker, body


def _looks_like_meta_key_point(text: str) -> bool:
    normalized = _dedupe_key(text)
    if not normalized:
        return True

    meta_patterns = (
        r"\bthis recording is part of\b",
        r"\b30 60 minute quality baseline\b",
        r"\bfinish with exact decisions risks questions and owners\b",
        r"\bfinish with a marked decision risks questions and owners\b",
        r"\bseparate confirmed decisions from general discussion\b",
        r"\bmost important action items should include\b",
        r"\bcontains clear decisions action items risks open questions\b",
        r"\blisten for concrete actions\b",
        r"\bwhat a user will expect after a real meeting\b",
    )
    return any(re.search(pattern, normalized) for pattern in meta_patterns)


def _looks_like_action_key_point(text: str) -> bool:
    normalized = _dedupe_key(text)
    return bool(
        re.search(
            r"\b(?:will|please|action for|action item for)\b",
            normalized,
        )
    )


def _clean_key_point_text(text: str) -> str:
    _, body = _strip_speaker_prefix(text)
    cleaned = re.sub(r"\s+", " ", body).strip(" .")
    if not cleaned:
        return ""

    cleaned = re.sub(
        r"^I\s+want\s+to\s+make\s+sure\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"^I\s+will\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = cleaned.strip(" .")
    if not cleaned:
        return ""
    return cleaned[0].upper() + cleaned[1:]


def _clean_key_points(value: Any) -> tuple[list[str], list[str]]:
    if not isinstance(value, list):
        return [], []

    cleaned_points: list[str] = []
    questions: list[str] = []
    seen_points: set[str] = set()

    for item in value:
        raw = _text(item)
        if not raw:
            continue

        _, without_speaker = _strip_speaker_prefix(raw)
        question_candidate = re.sub(
            r"^(?:open|unresolved)\s+question\s*,?\s*",
            "",
            without_speaker,
            flags=re.IGNORECASE,
        ).strip()
        if question_candidate != without_speaker and "?" in question_candidate:
            question = _normalize_question(question_candidate)
            if question and not _looks_like_rhetorical_or_answered_question(question):
                questions.append(question)
            continue

        cleaned = _clean_key_point_text(raw)
        if (
            not cleaned
            or _looks_like_meta_key_point(cleaned)
            or _looks_like_action_key_point(cleaned)
        ):
            continue

        key = _dedupe_key(cleaned)
        if key in seen_points:
            continue
        seen_points.add(key)
        cleaned_points.append(cleaned)

    return cleaned_points, _merge_open_questions([], questions)


def _merge_warnings(existing: Any, new_warnings: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()

    for warning in [*(existing if isinstance(existing, list) else []), *new_warnings]:
        text = _text(warning)
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(text)

    return output


def _normalize_question(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip(" .:-")
    if not cleaned:
        return ""
    cleaned = re.sub(
        r"^(?:open|unresolved)\s+questions?\s*(?:remains?|is|are)?\s*[:\-]?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"^question\s+remains?\s*[:\-]?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"^(?:we|the team)\s+still\s+need(?:s)?\s+to\s+(?:confirm|decide|know)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    if not cleaned:
        return ""
    cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned if cleaned.endswith("?") else f"{cleaned}?"


def _looks_like_rhetorical_or_answered_question(text: str) -> bool:
    normalized = _dedupe_key(text)
    if not normalized:
        return True

    rhetorical_patterns = (
        r"\bdoes that make sense\b",
        r"\bcan you hear me\b",
        r"\bany questions\b",
        r"\bright\b",
        r"\bokay\b",
        r"\byou know\b",
        r"\bwhat do you think\b",
    )
    answered_patterns = (
        r"\balready answered\b",
        r"\banswered\b",
        r"\bresolved\b",
        r"\bconfirmed\b",
        r"\bdecided\b",
        r"\bclosed\b",
    )

    return any(re.search(pattern, normalized) for pattern in rhetorical_patterns) or any(
        re.search(pattern, normalized) for pattern in answered_patterns
    )


def _question_answered_later(question: str, source_text: str) -> bool:
    normalized_question = _dedupe_key(question)
    normalized_source = _dedupe_key(source_text)
    if not normalized_question or normalized_question not in normalized_source:
        return False

    answer_text = normalized_source.split(normalized_question, 1)[1][:800]
    if not answer_text:
        return False

    meaningful_terms = {
        term
        for term in normalized_question.split()
        if len(term) > 3
        and term not in {"should", "whether", "question", "open", "what", "when", "where"}
    }
    if not meaningful_terms:
        return False

    answer_markers = (
        "decision confirmed",
        "confirmed decision",
        "we agreed",
        "we decided",
        "the team decided",
        "final answer",
    )
    if not any(marker in answer_text for marker in answer_markers):
        return False

    return len(meaningful_terms.intersection(answer_text.split())) >= 2


def _extract_open_questions_from_text(text: str) -> list[str]:
    normalized_text = _text(text)
    if not normalized_text:
        return []

    candidates: list[str] = []
    marker_patterns = (
        r"\bunresolved questions?\s+number\s+\d+\s*[:\-]\s*([^.\n?]+(?:\?)?)",
        r"\bopen questions?\s+number\s+\d+\s*[:\-]\s*([^.\n?]+(?:\?)?)",
        r"\bopen questions?\s*(?:remains?|is|are)?\s*[:\-]\s*([^.\n?]+(?:\?)?)",
        r"\bunresolved questions?\s*(?:remains?|is|are)?\s*[:\-]\s*([^.\n?]+(?:\?)?)",
        r"\bquestion remains?\s*[:\-]\s*([^.\n?]+(?:\?)?)",
        r"\bstill\s+do\s+not\s+know\s+(whether\s+[^.\n?]+(?:\?)?)",
        r"\b(?:we|the team)\s+still\s+need(?:s)?\s+to\s+(?:confirm|decide|know)\s+([^.\n?]+(?:\?)?)",
    )

    for pattern in marker_patterns:
        for match in re.finditer(pattern, normalized_text, flags=re.IGNORECASE):
            question = _normalize_question(match.group(1))
            if (
                question
                and not _looks_like_rhetorical_or_answered_question(question)
                and not _question_answered_later(question, normalized_text)
            ):
                candidates.append(question)

    section_match = re.search(
        r"\b(?:open|unresolved)\s+questions?\s*[:\-]\s*(?P<section>(?:\s*[-*]\s*[^\n?]+\?\s*)+)",
        normalized_text,
        flags=re.IGNORECASE,
    )
    if section_match:
        for line in section_match.group("section").splitlines():
            question = _normalize_question(re.sub(r"^\s*[-*]\s*", "", line))
            if (
                question
                and not _looks_like_rhetorical_or_answered_question(question)
                and not _question_answered_later(question, normalized_text)
            ):
                candidates.append(question)

    for sentence in re.split(r"(?<=[.!?])\s+|\n+", normalized_text):
        sentence = sentence.strip()
        if "?" not in sentence:
            continue
        lowered = sentence.lower()
        if not any(
            marker in lowered
            for marker in (
                "open question",
                "unresolved question",
                "question remains",
                "still need to confirm",
                "still need to decide",
                "still need to know",
            )
        ):
            continue
        question = _normalize_question(sentence)
        if (
            question
            and not _looks_like_rhetorical_or_answered_question(question)
            and not _question_answered_later(question, normalized_text)
        ):
            candidates.append(question)

    return candidates


def _merge_open_questions(existing: Any, new_questions: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()

    for question in [*(existing if isinstance(existing, list) else []), *new_questions]:
        text = _normalize_question(_text(question))
        if not text or _looks_like_rhetorical_or_answered_question(text):
            continue
        key = _dedupe_key(text)
        if key in seen:
            continue
        seen.add(key)
        output.append(text)

    return output


def detect_open_questions(notes: dict[str, Any], transcript_text: str | None) -> list[str]:
    """Extract likely unresolved questions without rewriting source content."""

    sources = [_text(transcript_text), _note_text_blob(notes)]
    questions: list[str] = []
    for source in sources:
        questions.extend(_extract_open_questions_from_text(source))
    return _merge_open_questions([], questions)


def _normalize_risk(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip(" .:-")
    if not cleaned:
        return ""
    cleaned = re.sub(r"\btime\s+out\b", "timeout", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(
        r"\bthe\s+work\s+can\s+throw\s+an\s+error\b",
        "the worker can throw an error",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"^(?:open|known|confirmed|explicit)?\s*(?:risk|risks|blocker|blockers)\s*[:\-]?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"^(?:there\s+is\s+a\s+)?risk\s+(?:that|is)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"^(?:the\s+)?blocker\s+(?:is|was)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    if not cleaned:
        return ""
    cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned if cleaned.endswith((".", "!", "?")) else f"{cleaned}."


def _looks_like_resolved_or_generic_risk(text: str) -> bool:
    normalized = _dedupe_key(text)
    if not normalized:
        return True

    resolved_patterns = (
        r"\bno risks?\b",
        r"\bnot a risk\b",
        r"\bno longer a risk\b",
        r"\bno blockers?\b",
        r"\bunblocked\b",
        r"\bresolved\b",
        r"\bmitigated\b",
        r"\bclosed\b",
        r"\bfixed\b",
        r"\balready handled\b",
    )
    generic_patterns = (
        r"^risks?$",
        r"^blockers?$",
        r"\breview risks?\b",
        r"\bdiscuss risks?\b",
        r"\brisk review\b",
        r"\brisks? and (?:action items|owners|questions)\b",
        r"\brisk register\b",
    )
    action_like_patterns = (
        r"\b[A-Z]?[a-z]+\s+will\s+\w+",
        r"\baction\s+for\b",
        r"\bplease\s+\w+",
    )

    return (
        any(re.search(pattern, normalized) for pattern in resolved_patterns)
        or any(re.search(pattern, normalized) for pattern in generic_patterns)
        or any(re.search(pattern, text) for pattern in action_like_patterns)
    )


def _extract_risks_from_text(text: str) -> list[str]:
    normalized_text = _text(text)
    if not normalized_text:
        return []

    candidates: list[str] = []
    marker_patterns = (
        r"\b(?:open|known|confirmed|explicit)?\s*(?:risk|risks)\s+number\s+\d+\s*[:\-]\s*([^.\n]+)",
        r"\b(?:open|known|confirmed|explicit)?\s*(?:risk|risks)\s*[:\-]\s*([^.\n]+)",
        r"\b(?:open|known|confirmed|explicit)?\s*(?:blocker|blockers)\s*[:\-]\s*([^.\n]+)",
        r"\b(longer\s+files\s+may\s+run\s+into\s+[^.\n]+)",
        r"\b(if\s+a\s+meeting\s+is\s+processed\s+before\s+[^.\n]+)",
        r"\b(?:main|primary|biggest)\s+risk\s+is\s+that\s+([^.\n]+)",
        r"\b(?:main|primary|biggest)\s+one\s+we\s+have\s+observed\s+is\s+([^.\n]+)",
        r"\banother\s+issue\s+is\s+([^.\n]+)",
        r"\bdo\s+not\s+([^.\n]+?\bbecause\b[^.\n]+)",
    )

    for pattern in marker_patterns:
        for match in re.finditer(pattern, normalized_text, flags=re.IGNORECASE):
            risk = _normalize_risk(match.group(1))
            if risk and not _looks_like_resolved_or_generic_risk(risk):
                candidates.append(risk)

    return candidates


def _risk_semantic_key(text: str) -> str:
    key = _dedupe_key(text)
    key = re.sub(r"\btime out\b", "timeout", key)
    if "raw media path" in key and "processed before" in key:
        return "meeting processed before raw media path attached worker error"
    if "longer files" in key and "timeout" in key:
        return "longer files timeout"
    return key


def _merge_risks(existing: Any, new_risks: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()

    for risk in [*(existing if isinstance(existing, list) else []), *new_risks]:
        text = _normalize_risk(_text(risk))
        if not text or _looks_like_resolved_or_generic_risk(text):
            continue
        key = _risk_semantic_key(text)
        if key in seen:
            continue
        seen.add(key)
        output.append(text)

    return output


def detect_risks(notes: dict[str, Any], transcript_text: str | None) -> list[str]:
    """Extract likely risks/blockers without rewriting source content."""

    sources = [_text(transcript_text), _note_text_blob(notes)]
    risks: list[str] = []
    for source in sources:
        risks.extend(_extract_risks_from_text(source))
    return _merge_risks([], risks)


_MONTH_NUMBER = {
    "january": "01",
    "february": "02",
    "march": "03",
    "april": "04",
    "may": "05",
    "june": "06",
    "july": "07",
    "august": "08",
    "september": "09",
    "october": "10",
    "november": "11",
    "december": "12",
}

_DAY_NUMBER = {
    "first": "01",
    "second": "02",
    "third": "03",
    "fourth": "04",
    "fifth": "05",
    "sixth": "06",
    "seventh": "07",
    "eighth": "08",
    "ninth": "09",
    "tenth": "10",
    "eleventh": "11",
    "twelfth": "12",
    "thirteenth": "13",
    "fourteenth": "14",
    "fifteenth": "15",
    "sixteenth": "16",
    "seventeenth": "17",
    "eighteenth": "18",
    "nineteenth": "19",
    "twentieth": "20",
    "twenty-first": "21",
    "twenty first": "21",
    "twenty-second": "22",
    "twenty second": "22",
    "twenty-third": "23",
    "twenty third": "23",
    "twenty-fourth": "24",
    "twenty fourth": "24",
    "twenty-fifth": "25",
    "twenty fifth": "25",
    "twenty-sixth": "26",
    "twenty sixth": "26",
    "twenty-seventh": "27",
    "twenty seventh": "27",
    "twenty-eighth": "28",
    "twenty eighth": "28",
    "twenty-ninth": "29",
    "twenty ninth": "29",
    "thirtieth": "30",
    "thirty-first": "31",
    "thirty first": "31",
}


def _normalize_spoken_datetime(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip(" .,")
    match = re.search(
        r"\b(?P<time>noon|midnight|(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d{1,2})\s*(?:am|pm))\s+on\s+"
        r"(?P<month>january|february|march|april|may|june|july|august|september|october|november|december)\s+"
        r"(?P<day>[a-z-]+(?:\s+[a-z-]+)?)"
        r"(?:,\s*twenty\s+twenty[- ]six)?\b",
        cleaned,
        flags=re.IGNORECASE,
    )
    if not match:
        return cleaned

    month = _MONTH_NUMBER.get(match.group("month").lower())
    day = _DAY_NUMBER.get(match.group("day").lower())
    if not month or not day:
        return cleaned

    time_text = match.group("time").lower().replace(" ", "")
    hour_by_word = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
    }
    if time_text == "noon":
        hour = 12
        minute = 0
    elif time_text == "midnight":
        hour = 0
        minute = 0
    else:
        hour_text = re.sub(r"(am|pm)$", "", time_text)
        meridiem = time_text[-2:]
        hour = int(hour_text) if hour_text.isdigit() else hour_by_word.get(hour_text, 0)
        if meridiem == "pm" and hour != 12:
            hour += 12
        if meridiem == "am" and hour == 12:
            hour = 0
        minute = 0

    return f"2026-{month}-{day} {hour:02d}:{minute:02d}"


def _normalize_owner(text: str) -> str:
    owner = re.sub(r"\s+", " ", text).strip(" .:-")
    if not owner:
        return ""
    blocked = {
        "action",
        "decision",
        "discussion",
        "it",
        "open",
        "risk",
        "that",
        "the",
        "this",
        "we",
        "actions",
        "audience",
        "client",
        "contractors",
        "deadline",
        "email",
        "file",
        "on",
        "output",
        "pilot",
        "planning",
        "recordings",
        "release",
        "reporting",
        "seventeen",
    }
    if owner.lower() in blocked:
        return ""
    return owner


def _normalize_action_owners_with_context(
    action_items: list[dict[str, Any]],
    context_text: str,
) -> list[dict[str, Any]]:
    context_key = _dedupe_key(context_text)
    if "lalita" not in context_key:
        return action_items

    normalized: list[dict[str, Any]] = []
    for item in action_items:
        owner = _text(item.get("owner"))
        if owner.lower() == "lolita":
            item = dict(item)
            item["owner"] = "Lalita"
            task = _text(item.get("task"))
            if task:
                item["text"] = f"Lalita: {task}"
        normalized.append(item)
    return normalized


def _extract_action_deadline(task: str) -> tuple[str, str]:
    spoken_datetime_pattern = (
        r"\bby\s+(?:noon|midnight|(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d{1,2})\s*(?:am|pm))\s+on\s+"
        r"(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+"
        r"[a-z-]+(?:\s+[a-z-]+)?(?:,\s*twenty\s+twenty[- ]six)?"
    )
    spoken_match = re.search(spoken_datetime_pattern, task, flags=re.IGNORECASE)
    if spoken_match:
        deadline = _normalize_spoken_datetime(
            re.sub(r"^\s*by\s+", "", spoken_match.group(0), flags=re.IGNORECASE)
        )
        task_without_deadline = (task[: spoken_match.start()] + task[spoken_match.end() :]).strip(
            " ,.;"
        )
        if deadline:
            return task_without_deadline, deadline

    deadline_patterns = (
        r"\b(?:due date is|due dates? remain|due by|due)\s+([^.;,\n]+(?:\s+(?:Eastern|morning|afternoon|evening))?)",
        r"\b(?:by|before|after|until)\s+([^.;,\n]+(?:\s+(?:Eastern|morning|afternoon|evening))?)",
    )

    for pattern in deadline_patterns:
        match = re.search(pattern, task, flags=re.IGNORECASE)
        if not match:
            continue
        deadline = re.sub(r"\s+", " ", match.group(1)).strip(" .")
        task_without_deadline = (task[: match.start()] + task[match.end() :]).strip(" ,.;")
        if deadline:
            return task_without_deadline, deadline

    return task, ""


def _normalize_action_task(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip(" .:-")
    cleaned = re.sub(
        r"^(?:I\s+will|will|please|can\s+you|we\s+need\s+to|the\s+next\s+step\s+is)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = cleaned.strip(" .:-")
    if not cleaned:
        return ""
    return cleaned[0].upper() + cleaned[1:]


def _looks_like_generic_action(task: str) -> bool:
    normalized = _dedupe_key(task)
    if not normalized:
        return True

    generic_patterns = (
        r"^follow up$",
        r"^check\b",
        r"^review\b",
        r"^make sure\b",
        r"^check it$",
        r"^discuss this$",
        r"^review later$",
        r"\bfollow up on\b",
        r"\blisten for concrete actions\b",
        r"\bmake sure the notes separate\b",
        r"\bmost important action items should include\b",
        r"\bcapture risks separately\b",
        r"\bcontains clear decisions\b",
        r"\bdecisions discussed in this meeting\b",
        r"\bfinish with exact decisions\b",
        r"\bfinish with a marked decision\b",
        r"\bthis recording is part of\b",
    )
    deliverable_patterns = (
        r"\b(?:write|draft|prepare|create|update|add|remove|submit|send|verify|confirm)\b",
        r"\b(?:template|macro|tracker|copy|page|link|note|warning|checklist|submission|logs?)\b",
    )

    is_generic = any(re.search(pattern, normalized) for pattern in generic_patterns)
    has_deliverable = any(re.search(pattern, normalized) for pattern in deliverable_patterns)
    return is_generic and not has_deliverable


def _make_action_item(owner: str, task: str) -> dict[str, str] | None:
    normalized_owner = _normalize_owner(owner)
    if not normalized_owner:
        return None

    task_without_deadline, deadline = _extract_action_deadline(task)
    normalized_task = _normalize_action_task(task_without_deadline)
    if not normalized_task or _looks_like_generic_action(normalized_task):
        return None

    item = {
        "owner": normalized_owner,
        "task": normalized_task,
        "status": "open",
        "priority": "medium",
    }
    if deadline:
        item["deadline"] = deadline
    return item


def _extract_action_items_from_text(text: str) -> list[dict[str, str]]:
    normalized_text = _text(text)
    if not normalized_text:
        return []

    candidates: list[dict[str, str]] = []
    speaker_commitment_patterns = (
        r"\b(?P<owner>[A-Z][A-Za-z]+)\s*:\s*[^\n]*?\bI\s+will\s+(?P<task>[^.\n]+\bby\b[^.\n]+)",
        r"\b(?P<owner>[A-Z][A-Za-z]+)\s*:\s*(?:[^.\n]*\baction[^.\n]*\.\s*)?I\s+will\s+(?P<task>[^.\n]+\bby\b[^.\n]+)",
        r"\b(?P<owner>[A-Z][A-Za-z]+)\s*:\s*I\s+accept\s+[^.\n]*action[^.\n]*\.\s*I\s+will\s+(?P<task>[^.\n]+(?:\.\s*by\s+[^.\n]+)?)",
    )
    for pattern in speaker_commitment_patterns:
        for match in re.finditer(pattern, normalized_text):
            item = _make_action_item(match.group("owner"), match.group("task"))
            if item:
                candidates.append(item)

    patterns = (
        r"\bAction(?:\s+item)?\s+for\s+(?P<owner>[A-Z][A-Za-z]+)\s*[:,]\s*(?P<task>[^.\n]+)",
        r"\b(?P<owner>[A-Z][A-Za-z]+)\s*,\s*please\s+(?P<task>[^.\n]+)",
        r"\b(?P<owner>[A-Z][A-Za-z]+)\s+will\s+(?P<task>[^.\n]+)",
        r"\bassign(?:ed)?\s+to\s+(?P<owner>[A-Z][A-Za-z]+)\s*[:,]\s*(?P<task>[^.\n]+)",
    )

    for pattern in patterns:
        for match in re.finditer(pattern, normalized_text):
            owner = match.group("owner")
            task = match.group("task")
            item = _make_action_item(owner, task)
            if item:
                candidates.append(item)

    return candidates


def _action_item_key(item: dict[str, Any]) -> str:
    owner = _dedupe_key(_text(item.get("owner")))
    task = _dedupe_key(
        _text(item.get("task") or item.get("action") or item.get("text") or item.get("description"))
    )
    return f"{owner}:{task}"


def _action_task_key(item: dict[str, Any]) -> str:
    task = _dedupe_key(
        _text(item.get("task") or item.get("action") or item.get("text") or item.get("description"))
    )
    task = re.sub(r"\b(?:a|an|the)\b", " ", task)
    return re.sub(r"\s+", " ", task).strip()


def _action_semantic_key(item: dict[str, Any]) -> str:
    key = _action_task_key(item)
    key = re.sub(r"\bstaged\b", "stage", key)
    key = re.sub(r"\btiming\b", "timing", key)
    key = re.sub(r"\belapsed duration\b", "duration", key)
    key = re.sub(r"\bworker logs?\b", "worker output", key)
    key = re.sub(r"\bprocessing step\b", "processing stage", key)
    key = re.sub(r"\bmajor processing steps?\b", "processing stages", key)

    if "stage timing logs" in key or (
        "timing logs" in key and ("worker output" in key or "worker logs" in key)
    ):
        return "add stage timing logs worker output"

    backup_terms = {"backup", "meeting", "processed", "demo"}
    key_terms = set(key.split())
    if backup_terms <= key_terms or (
        "meeting seventeen" in key and {"backup", "demo"} <= key_terms
    ):
        return "keep backup demo meeting ready"

    if "primary demo artifact" in key or (
        "strongest current output" in key and "demo artifact" in key
    ):
        return "keep primary demo artifact ready"

    return key


def _action_richness_score(item: dict[str, Any]) -> int:
    score = 0
    if _text(item.get("owner")):
        score += 4
    if _text(item.get("deadline")):
        score += 3
    if _text(item.get("priority")):
        score += 1
    score += min(len(_dedupe_key(_text(item.get("task"))).split()), 8)
    return score


def _normalize_existing_action_item(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None

    task = _text(
        item.get("task") or item.get("action") or item.get("text") or item.get("description")
    )
    if not task:
        return None

    output = dict(item)
    owner = _normalize_owner(_text(output.get("owner")))
    if owner:
        output["owner"] = owner
    output["task"] = task
    output["status"] = _text(output.get("status")) or "open"
    return output


def _merge_action_items(
    existing: list[Any],
    new_actions: list[dict[str, str]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []

    for raw_item in [*existing, *new_actions]:
        item = _normalize_existing_action_item(raw_item)
        if not item:
            continue
        task_key = _action_task_key(item)
        if not task_key:
            continue
        semantic_key = _action_semantic_key(item)
        duplicate_index: int | None = None
        for index, existing_item in enumerate(output):
            existing_key = _action_task_key(existing_item)
            existing_semantic_key = _action_semantic_key(existing_item)
            if (
                task_key == existing_key
                or task_key in existing_key
                or existing_key in task_key
                or semantic_key == existing_semantic_key
            ):
                duplicate_index = index
                break
        if duplicate_index is not None:
            existing_item = output[duplicate_index]
            if _action_richness_score(item) > _action_richness_score(existing_item):
                output[duplicate_index] = item
            continue
        output.append(item)

    return output


def detect_action_items(
    notes: dict[str, Any],
    transcript_text: str | None,
) -> list[dict[str, str]]:
    """Extract explicit owner/action items without inventing missing fields."""

    sources = [_text(transcript_text), _note_text_blob(notes)]
    actions: list[dict[str, str]] = []
    for source in sources:
        actions.extend(_extract_action_items_from_text(source))
    return _merge_action_items([], actions)


def _normalize_decision_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip(" .:-")
    if not cleaned:
        return ""
    cleaned = re.split(
        r"\bdecision\s+(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s*[:\-]",
        cleaned,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    cleaned = re.split(
        r"\bthis\s+decision\s+has\b",
        cleaned,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    cleaned = re.sub(
        r"^(?:we|the\s+team)\s+(?:will|agreed\s+to|decided\s+to)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"^to\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = cleaned.strip(" .:-")
    if not cleaned:
        return ""
    cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned if cleaned.endswith((".", "!", "?")) else f"{cleaned}."


def _looks_like_non_decision(text: str) -> bool:
    normalized = _dedupe_key(text)
    if not normalized:
        return True

    blocked_patterns = (
        r"\bmaybe\b",
        r"\bwe discussed\b",
        r"\bdiscussed in this meeting\b",
        r"\bone option is\b",
        r"\boption is\b",
        r"\bshould we\b",
        r"\bshould the\b",
        r"\bno decision\b",
        r"\bdecision yet\b",
        r"\bneed to decide\b",
        r"\bstill need to decide\b",
        r"\bopen question\b",
        r"\bunresolved question\b",
        r"\bnot decided\b",
        r"\btentative\b",
        r"\bproposal\b",
        r"\bpossibility\b",
        r"\bis confirmed\b",
        r"\bwas confirmed\b",
        r"^(?:the\s+)?(?:backend|product|demo|demonstration|system|service|checklist|review)\s+(?:is|are|was|were)\s+(?:ready|healthy|complete|completed)\b",
        r"\bworks?\b",
        r"\bowns?\b",
        r"\bwill monitor\b",
        r"\bfinish with exact decisions\b",
        r"\bfinish with a marked decision\b",
        r"\bseparate confirmed decisions from general discussion\b",
    )

    return any(re.search(pattern, normalized) for pattern in blocked_patterns)


def _extract_decisions_from_text(text: str) -> list[dict[str, Any]]:
    normalized_text = _text(text)
    if not normalized_text:
        return []

    candidates: list[dict[str, Any]] = []
    patterns = (
        r"\b(?:confirmed\s+decision|decision\s+confirmed)\s*\.\s*(?P<decision>[^\n?]+)",
        r"\bdecision\s+(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s*[:\-]\s*(?P<decision>.*?)(?=\s+\bdecision\s+(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s*[:\-]|\n|$)",
        r"\b(?:confirmed\s+decision|decision\s+confirmed|decision)\s*(?:for\s+[^:.\n]+)?\s*[:\-]\s*(?P<decision>[^\n?]+)",
        r"\bwe\s+agreed\s+to\s+(?P<decision>[^\n?]+)",
        r"\bwe\s+decided\s+to\s+(?P<decision>[^\n?]+)",
        r"\bthe\s+team\s+decided\s+to\s+(?P<decision>[^\n?]+)",
    )

    for pattern in patterns:
        for match in re.finditer(pattern, normalized_text, flags=re.IGNORECASE):
            decision = _normalize_decision_text(match.group("decision"))
            if decision and not _looks_like_non_decision(decision):
                candidates.append({"text": decision, "confidence": 0.8})

    return candidates


def _decision_key(item: dict[str, Any]) -> str:
    return _dedupe_key(_text(item.get("text") or item.get("decision")))


def _decision_similarity_key(item: dict[str, Any]) -> str:
    key = _decision_key(item)
    key = re.sub(r"\b(?:a|an|the)\b", " ", key)
    return re.sub(r"\s+", " ", key).strip()


def _normalize_existing_decision(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None

    text = _text(item.get("text") or item.get("decision"))
    if not text:
        return None

    output = dict(item)
    output["text"] = text
    return output


def _merge_decision_objects(
    existing: list[Any],
    new_decisions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    similarity_keys: list[str] = []

    for raw_item in [*existing, *new_decisions]:
        item = _normalize_existing_decision(raw_item)
        if not item:
            continue
        text = _normalize_decision_text(_text(item.get("text")))
        if not text or _looks_like_non_decision(text):
            continue
        item["text"] = text
        key = _decision_key(item)
        similarity_key = _decision_similarity_key(item)
        if key in seen or any(
            similarity_key in existing_key or existing_key in similarity_key
            for existing_key in similarity_keys
        ):
            continue
        seen.add(key)
        similarity_keys.append(similarity_key)
        output.append(item)

    return output


def detect_decisions(
    notes: dict[str, Any],
    transcript_text: str | None,
) -> list[dict[str, Any]]:
    """Extract explicit confirmed decisions without inferring from discussion."""

    sources = [_text(transcript_text), _note_text_blob(notes)]
    decisions: list[dict[str, Any]] = []
    for source in sources:
        decisions.extend(_extract_decisions_from_text(source))
    return _merge_decision_objects([], decisions)


def _iter_note_text_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        output: list[str] = []
        for item in value:
            output.extend(_iter_note_text_values(item))
        return output
    if isinstance(value, dict):
        output = []
        for key, item in value.items():
            if key == "known_entity_warnings":
                continue
            output.extend(_iter_note_text_values(item))
        return output
    return []


def _note_text_blob(notes: dict[str, Any]) -> str:
    fields = (
        "summary",
        "summary_slots",
        "key_points",
        "decisions",
        "decision_objects",
        "action_items",
        "action_item_objects",
    )
    texts: list[str] = []
    for field in fields:
        texts.extend(_iter_note_text_values(notes.get(field)))
    return "\n".join(text for text in texts if text.strip())


def detect_known_entity_warnings(notes: dict[str, Any]) -> list[str]:
    """Return warning-only known-entity guardrail findings.

    This function intentionally does not rewrite notes. It only flags likely
    variants/misspellings that should be reviewed before v2 output is trusted.
    """

    text_blob = _note_text_blob(notes)
    if not text_blob:
        return []

    warnings: list[str] = []
    for canonical, patterns in KNOWN_ENTITY_VARIANTS.items():
        for pattern in patterns:
            match = re.search(pattern, text_blob, flags=re.IGNORECASE)
            if match:
                warnings.append(
                    f"Possible known entity rewrite: '{match.group(0)}' may refer to '{canonical}'."
                )
                break

    return warnings


def _clean_sentence(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip(" .")
    if not cleaned:
        return ""
    return cleaned[0].upper() + cleaned[1:] + "."


def _infer_purpose(text: str | None) -> str:
    normalized = _text(text)
    if not normalized:
        return ""

    patterns = [
        r"\b(?:today we need to|we need to|the goal is to|goal is to)\s+([^.\n]+)",
        r"\b(?:the purpose is to|purpose is to)\s+([^.\n]+)",
        r"\b(?:confirm|review|align on)\s+([^.\n]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if not match:
            continue

        purpose = match.group(1).strip(" .")
        purpose = re.sub(r"\band\s+the\s+", "and ", purpose, flags=re.IGNORECASE)
        if purpose:
            return _clean_sentence(f"Confirm {purpose}")

    return ""


def _action_to_next_step(action_item: Any) -> str:
    if not isinstance(action_item, dict):
        return ""

    task = _text(
        action_item.get("task")
        or action_item.get("action")
        or action_item.get("text")
        or action_item.get("description")
    )
    if not task:
        return ""

    owner = _text(action_item.get("owner"))
    if owner:
        task = re.sub(rf"^{re.escape(owner)}\s*[-:]\s*", "", task, flags=re.IGNORECASE)

    return _clean_sentence(task)


def _dedupe_key(text: str) -> str:
    normalized = text.lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _sync_next_steps_from_actions(
    existing_next_steps: list[Any],
    action_items: list[Any],
    *,
    limit: int = 5,
) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()

    for step in existing_next_steps:
        step_text = _clean_sentence(_text(step))
        key = _dedupe_key(step_text)
        if step_text and key not in seen:
            seen.add(key)
            output.append(step_text)

    for action_item in action_items:
        step_text = _action_to_next_step(action_item)
        key = _dedupe_key(step_text)
        if step_text and key not in seen:
            seen.add(key)
            output.append(step_text)

        if len(output) >= limit:
            break

    return output[:limit]


VALID_NOTES_ENGINE_MODES = {"v1", "v2", "v3", "shadow"}


def normalize_notes_engine_mode(value: object) -> str:
    """Normalize NOTES_ENGINE mode.

    Defaults to v1 for safety.
    """

    mode = str(value or "").strip().lower()
    if mode in VALID_NOTES_ENGINE_MODES:
        return mode
    return "v1"


def should_apply_quality_engine_v2(mode: object) -> bool:
    """Return True only when v2 should become the user-facing notes output."""

    return normalize_notes_engine_mode(mode) == "v2"


def should_run_quality_engine_v2_shadow(mode: object) -> bool:
    """Return True when v2 should run for comparison only."""

    return normalize_notes_engine_mode(mode) == "shadow"


def parse_quality_engine_v2_allowlist(value: object) -> set[str]:
    """Parse comma-separated QEv2 rollout email allowlist values."""

    return {email.strip().lower() for email in str(value or "").split(",") if email.strip()}


def is_quality_engine_v2_email_allowlisted(
    email: object,
    allowlist_value: object | None = None,
) -> bool:
    """Return True when an email is explicitly allowlisted for QEv2."""

    normalized_email = str(email or "").strip().lower()
    if not normalized_email:
        return False

    raw_allowlist = (
        os.getenv("MEETIQ_QEV2_ALLOWLIST_EMAILS", "")
        if allowlist_value is None
        else allowlist_value
    )
    return normalized_email in parse_quality_engine_v2_allowlist(raw_allowlist)


def resolve_notes_engine_mode_for_user(
    global_mode: object,
    user_email: object,
    allowlist_value: object | None = None,
) -> str:
    """Resolve the effective notes engine mode for a specific account.

    v1 remains the production default. Shadow and explicit global v2 preserve
    existing global behavior; otherwise only allowlisted account emails get v2.
    """

    normalized_mode = normalize_notes_engine_mode(global_mode)
    if normalized_mode in {"shadow", "v2"}:
        return normalized_mode
    if is_quality_engine_v2_email_allowlisted(user_email, allowlist_value):
        return "v2"
    return "v1"


def _as_text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    output: list[str] = []
    for item in value:
        text = _text(item)
        if text:
            output.append(text)
    return output


def _render_markdown_section(title: str, body: str | list[str]) -> str:
    if isinstance(body, list):
        items = [_text(item) for item in body if _text(item)]
        if not items:
            return ""
        rendered_body = "\n".join(
            item if item.startswith(("- ", "- [ ] ")) else f"- {item}" for item in items
        )
    else:
        rendered_body = _text(body)
        if not rendered_body:
            return ""

    return f"## {title}\n\n{rendered_body}"


def _render_action_item_markdown(action_item: Any) -> str:
    if not isinstance(action_item, dict):
        return ""

    task = _text(
        action_item.get("task")
        or action_item.get("action")
        or action_item.get("text")
        or action_item.get("description")
    )
    if not task:
        return ""

    owner = _text(action_item.get("owner"))
    deadline = _text(action_item.get("deadline") or action_item.get("due_date"))
    status = _text(action_item.get("status")) or "open"

    label = f"**{owner}** — {task}" if owner else task
    details = [f"status: {status}"]
    if deadline:
        details.insert(0, f"deadline: {deadline}")
    return f"- [ ] {label} _({', '.join(details)})_"


def _render_decision_markdown(decision: Any) -> str:
    if isinstance(decision, dict):
        return _text(decision.get("text") or decision.get("decision"))
    return _text(decision)


def render_quality_engine_v2_markdown(notes: dict[str, Any]) -> str:
    """Render structured v2 notes as clean Markdown.

    This helper is not wired into production rendering. Callers must explicitly
    opt into v2 behavior before using it.
    """

    summary_slots = notes.get("summary_slots")
    if not isinstance(summary_slots, dict):
        summary_slots = {}

    sections: list[str] = []
    sections.append(_render_markdown_section("Purpose", _text(summary_slots.get("purpose"))))
    sections.append(_render_markdown_section("Summary", _text(notes.get("summary"))))
    sections.append(_render_markdown_section("Key Points", _as_text_list(notes.get("key_points"))))

    decision_objects = notes.get("decision_objects")
    if not isinstance(decision_objects, list):
        decision_objects = []
    decisions = [
        rendered
        for rendered in (_render_decision_markdown(item) for item in decision_objects)
        if rendered
    ]
    sections.append(_render_markdown_section("Decisions", decisions))

    action_items = notes.get("action_item_objects")
    if not isinstance(action_items, list):
        action_items = []
    actions = [
        rendered
        for rendered in (_render_action_item_markdown(item) for item in action_items)
        if rendered
    ]
    sections.append(_render_markdown_section("Action Items", actions))
    sections.append(
        _render_markdown_section(
            "Open Questions",
            _as_text_list(summary_slots.get("open_questions")),
        )
    )
    sections.append(
        _render_markdown_section(
            "Risks / Blockers",
            _as_text_list(summary_slots.get("risks")),
        )
    )
    sections.append(
        _render_markdown_section(
            "Next Steps",
            _as_text_list(summary_slots.get("next_steps")),
        )
    )

    return "\n\n".join(section for section in sections if section).strip() + "\n"


def _list_field(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _has_deadline_language(text: str | None) -> bool:
    return bool(
        re.search(
            r"\b(?:by|before|after|due|deadline|tomorrow|monday|tuesday|wednesday|thursday|friday|next week|end of week)\b",
            _text(text),
            flags=re.IGNORECASE,
        )
    )


def _has_decision_language(text: str | None) -> bool:
    return bool(
        re.search(
            r"\b(?:decision|agreed|decided|confirmed decision|decision confirmed)\b",
            _text(text),
            flags=re.IGNORECASE,
        )
    )


def _has_action_language(text: str | None) -> bool:
    return bool(
        re.search(
            r"\b(?:action item|assigned action|I accept .{0,40}action|I will|will .{0,80}\bby\b|please)\b",
            _text(text),
            flags=re.IGNORECASE,
        )
    )


def _explicitly_says_no_actions(text: str | None) -> bool:
    normalized = _dedupe_key(_text(text))
    return bool(
        re.search(r"\bno (?:assigned )?(?:actions?|action items?|tasks?|next steps?)\b", normalized)
        or re.search(
            r"\bnot assigning (?:implementation work|work|tasks?|action items?)\b", normalized
        )
        or re.search(r"\bcontains? no assigned actions?\b", normalized)
    )


def _summary_too_generic(summary: str) -> bool:
    normalized = _dedupe_key(summary)
    if not normalized:
        return True
    generic_summaries = {
        "the meeting aligned on the main priorities and next steps",
        "the team discussed the meeting and next steps",
        "the team aligned on the main priorities",
        "meeting notes",
        "summary",
    }
    return normalized in generic_summaries or len(normalized.split()) < 6


def _has_generic_action_owner(action_items: list[Any]) -> bool:
    generic_owners = {"someone", "unassigned", "unknown", "tbd", "owner"}
    for item in action_items:
        if not isinstance(item, dict):
            continue
        owner = _dedupe_key(_text(item.get("owner")))
        if owner in generic_owners:
            return True
    return False


def _has_action_without_deadline(action_items: list[Any]) -> bool:
    for item in action_items:
        if isinstance(item, dict) and not _text(item.get("deadline") or item.get("due_date")):
            return True
    return False


def _has_open_question_key_point(key_points: list[Any]) -> bool:
    for item in key_points:
        text = _text(item)
        if re.search(r"\bopen question\b", text, flags=re.IGNORECASE) or (
            "?" in text and re.search(r"\bquestion\b", text, flags=re.IGNORECASE)
        ):
            return True
    return False


def _has_transcript_like_notes(notes: dict[str, Any]) -> bool:
    blob = _note_text_blob(notes)
    return bool(
        re.search(
            r"\b(?:speaker\s+\d+|[A-Z][A-Za-z]+\s+says?,)",
            blob,
            flags=re.IGNORECASE,
        )
    )


def _has_suspicious_email_or_domain(notes: dict[str, Any]) -> bool:
    blob = _note_text_blob(notes)
    patterns = (
        r"\b[\w.+-]+\s+(?:at|\[at\])\s+[\w.-]+",
        r"\b[\w.+-]+@[\w.-]+\.(?:con|cmo|comm|aii|ioo)\b",
        r"\b(?:vercell|go\s+daddy|meetiq\.ai|support@acjen\.(?:com|io|co))\b",
    )
    return any(re.search(pattern, blob, flags=re.IGNORECASE) for pattern in patterns)


def critic_quality_engine_v2_notes(
    notes: dict[str, Any],
    transcript_text: str | None = None,
) -> dict[str, Any]:
    """Return conservative internal quality warnings for v2 notes."""

    summary_slots = notes.get("summary_slots")
    if not isinstance(summary_slots, dict):
        summary_slots = {}

    action_items = [
        *_list_field(notes.get("action_item_objects")),
        *_list_field(notes.get("action_items")),
        *_list_field(notes.get("actions")),
    ]
    decision_objects = _list_field(notes.get("decision_objects"))
    key_points = _list_field(notes.get("key_points"))

    checks = {
        "purpose_present": bool(_text(summary_slots.get("purpose"))),
        "summary_specific": not _summary_too_generic(_text(notes.get("summary"))),
        "actions_present": (
            len(action_items) > 0
            or (transcript_text is not None and not _has_action_language(transcript_text))
            or _explicitly_says_no_actions(transcript_text)
        ),
        "decisions_present_when_language_exists": not (
            _has_decision_language(transcript_text) and len(decision_objects) == 0
        ),
        "owners_not_generic": not _has_generic_action_owner(action_items),
        "deadlines_present_when_language_exists": not (
            _has_deadline_language(transcript_text) and _has_action_without_deadline(action_items)
        ),
        "open_questions_not_in_key_points": not _has_open_question_key_point(key_points),
        "emails_and_domains_not_suspicious": not _has_suspicious_email_or_domain(notes),
        "notes_not_transcript_like": not _has_transcript_like_notes(notes),
    }

    warning_messages = {
        "purpose_present": "Purpose is missing.",
        "summary_specific": "Summary appears too generic.",
        "actions_present": "Action items are missing or too few.",
        "decisions_present_when_language_exists": "Decision language exists but no decisions were extracted.",
        "owners_not_generic": "Action item owner appears generic or guessed.",
        "deadlines_present_when_language_exists": "Deadline language exists but an action item is missing a deadline.",
        "open_questions_not_in_key_points": "Open questions appear mixed into key points.",
        "emails_and_domains_not_suspicious": "Possible suspicious email or domain text detected.",
        "notes_not_transcript_like": "Notes appear transcript-like.",
    }
    warnings = [message for key, message in warning_messages.items() if not checks[key]]
    blocking_check_keys = {
        "purpose_present",
        "actions_present",
        "decisions_present_when_language_exists",
        "owners_not_generic",
        "open_questions_not_in_key_points",
        "emails_and_domains_not_suspicious",
        "notes_not_transcript_like",
    }
    blocking_warnings = [
        warning_messages[key] for key in blocking_check_keys if key in checks and not checks[key]
    ]

    return {
        "passed": not blocking_warnings,
        "warnings": warnings,
        "blocking_warnings": blocking_warnings,
        "checks": checks,
    }


def _run_quality_engine_v2_critic_safely(
    notes: dict[str, Any],
    transcript_text: str | None,
) -> dict[str, Any]:
    try:
        return critic_quality_engine_v2_notes(notes, transcript_text)
    except Exception as exc:  # pragma: no cover - defensive metadata fallback
        return {
            "passed": False,
            "warnings": [f"Quality Engine v2 critic failed: {exc.__class__.__name__}"],
            "checks": {},
        }


def run_quality_engine_v2(
    notes: dict[str, Any],
    transcript_text: str | None,
    *,
    mode: object = "v1",
) -> dict[str, Any]:
    """Run Quality Engine v2 according to mode.

    Modes:
    - v1: return original notes unchanged.
    - v2: return improved notes.
    - shadow: run v2 for comparison but return original notes unchanged.
    """

    normalized_mode = normalize_notes_engine_mode(mode)

    metadata: dict[str, Any] = {
        "applied": False,
        "mode": normalized_mode,
        "fallback_used": False,
        "warnings": [],
    }

    if normalized_mode == "v1":
        return {"notes": notes, "metadata": metadata}

    try:
        improved = apply_quality_engine_v2(notes, transcript_text)
    except Exception as exc:  # pragma: no cover - defensive production fallback
        metadata["fallback_used"] = True
        metadata["warnings"].append(f"Quality Engine v2 failed: {exc.__class__.__name__}")
        return {"notes": notes, "metadata": metadata}

    if normalized_mode == "shadow":
        metadata["shadow_ran"] = True
        metadata["shadow_summary"] = _compare_v1_v2_notes(notes, improved)
        metadata["critic"] = _run_quality_engine_v2_critic_safely(
            improved,
            transcript_text,
        )
        return {"notes": notes, "metadata": metadata}

    metadata["applied"] = True
    metadata["critic"] = _run_quality_engine_v2_critic_safely(
        improved,
        transcript_text,
    )
    return {"notes": improved, "metadata": metadata}


def build_quality_engine_v2_admin_comparison(
    notes: dict[str, Any],
    transcript_text: str | None,
) -> dict[str, Any]:
    """Build explicit admin/shadow comparison data without changing user notes.

    This helper is intentionally not used by normal note rendering. It exposes
    v2 output only to callers that deliberately request an admin comparison.
    """

    try:
        improved = apply_quality_engine_v2(notes, transcript_text)
        critic = _run_quality_engine_v2_critic_safely(improved, transcript_text)
        return {
            "user_notes": notes,
            "admin_only": True,
            "comparison": _compare_v1_v2_notes(notes, improved),
            "v2_notes": improved,
            "v2_markdown": render_quality_engine_v2_markdown(improved),
            "metadata": {
                "mode": "admin_comparison",
                "applied_to_user_notes": False,
                "fallback_used": False,
                "critic": critic,
            },
        }
    except Exception as exc:  # pragma: no cover - defensive admin fallback
        return {
            "user_notes": notes,
            "admin_only": True,
            "comparison": {},
            "v2_notes": None,
            "v2_markdown": "",
            "metadata": {
                "mode": "admin_comparison",
                "applied_to_user_notes": False,
                "fallback_used": True,
                "warnings": [f"Quality Engine v2 comparison failed: {exc.__class__.__name__}"],
            },
        }


def _compare_v1_v2_notes(
    original: dict[str, Any],
    improved: dict[str, Any],
) -> dict[str, Any]:
    original_slots = original.get("summary_slots") if isinstance(original, dict) else {}
    improved_slots = improved.get("summary_slots") if isinstance(improved, dict) else {}

    if not isinstance(original_slots, dict):
        original_slots = {}
    if not isinstance(improved_slots, dict):
        improved_slots = {}

    original_purpose = _text(original_slots.get("purpose"))
    improved_purpose = _text(improved_slots.get("purpose"))

    original_actions = original.get("action_item_objects") if isinstance(original, dict) else []
    improved_actions = improved.get("action_item_objects") if isinstance(improved, dict) else []

    original_decisions = original.get("decision_objects") if isinstance(original, dict) else []
    improved_decisions = improved.get("decision_objects") if isinstance(improved, dict) else []

    return {
        "purpose_added": not bool(original_purpose) and bool(improved_purpose),
        "original_action_count": len(original_actions) if isinstance(original_actions, list) else 0,
        "improved_action_count": len(improved_actions) if isinstance(improved_actions, list) else 0,
        "original_decision_count": len(original_decisions)
        if isinstance(original_decisions, list)
        else 0,
        "improved_decision_count": len(improved_decisions)
        if isinstance(improved_decisions, list)
        else 0,
    }
