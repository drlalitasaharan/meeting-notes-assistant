from __future__ import annotations

import copy
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

    next_steps = summary_slots.get("next_steps")
    if not isinstance(next_steps, list):
        next_steps = []

    summary_slots["next_steps"] = _sync_next_steps_from_actions(
        next_steps,
        action_items,
    )
    summary_slots["open_questions"] = _merge_open_questions(
        summary_slots.get("open_questions"),
        detect_open_questions(improved, transcript_text),
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
        r"\bopen questions?\s*(?:remains?|is|are)?\s*[:\-]\s*([^.\n?]+(?:\?)?)",
        r"\bunresolved questions?\s*(?:remains?|is|are)?\s*[:\-]\s*([^.\n?]+(?:\?)?)",
        r"\bquestion remains?\s*[:\-]\s*([^.\n?]+(?:\?)?)",
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
        r"\b(?:open|known|confirmed|explicit)?\s*(?:risk|risks)\s*[:\-]\s*([^.\n]+)",
        r"\b(?:open|known|confirmed|explicit)?\s*(?:blocker|blockers)\s*[:\-]\s*([^.\n]+)",
    )

    for pattern in marker_patterns:
        for match in re.finditer(pattern, normalized_text, flags=re.IGNORECASE):
            risk = _normalize_risk(match.group(1))
            if risk and not _looks_like_resolved_or_generic_risk(risk):
                candidates.append(risk)

    return candidates


def _merge_risks(existing: Any, new_risks: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()

    for risk in [*(existing if isinstance(existing, list) else []), *new_risks]:
        text = _normalize_risk(_text(risk))
        if not text or _looks_like_resolved_or_generic_risk(text):
            continue
        key = _dedupe_key(text)
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
    }
    if owner.lower() in blocked:
        return ""
    return owner


def _extract_action_deadline(task: str) -> tuple[str, str]:
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
    patterns = (
        r"\bAction(?:\s+item)?\s+for\s+(?P<owner>[A-Z][A-Za-z]+)\s*[:,]\s*(?P<task>[^.\n]+)",
        r"\b(?P<owner>[A-Z][A-Za-z]+)\s*,\s*please\s+(?P<task>[^.\n]+)",
        r"\b(?P<owner>[A-Z][A-Za-z]+)\s+will\s+(?P<task>[^.\n]+)",
        r"\bassign(?:ed)?\s+to\s+(?P<owner>[A-Z][A-Za-z]+)\s*[:,]\s*(?P<task>[^.\n]+)",
    )

    for pattern in patterns:
        for match in re.finditer(pattern, normalized_text, flags=re.IGNORECASE):
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
        duplicate_index: int | None = None
        for index, existing_item in enumerate(output):
            existing_key = _action_task_key(existing_item)
            if task_key == existing_key or task_key in existing_key or existing_key in task_key:
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
        r"\bready\b",
        r"\bhealthy\b",
        r"\bcomplete\b",
        r"\bcompleted\b",
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


VALID_NOTES_ENGINE_MODES = {"v1", "v2", "shadow"}


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
        return {"notes": notes, "metadata": metadata}

    metadata["applied"] = True
    return {"notes": improved, "metadata": metadata}


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
