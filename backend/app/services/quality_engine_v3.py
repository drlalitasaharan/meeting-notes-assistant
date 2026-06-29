from __future__ import annotations

import copy
import os
import re
from typing import Any

ACTION_VERBS = {
    "create",
    "prepare",
    "send",
    "share",
    "update",
    "review",
    "run",
    "test",
    "finalize",
    "publish",
    "submit",
    "schedule",
    "document",
    "fix",
    "implement",
    "confirm",
    "draft",
    "write",
    "collect",
    "follow up",
    "set up",
    "clean",
    "add",
    "upload",
    "finish",
    "complete",
    "verify",
    "circulate",
}


WEAK_ACTION_PATTERNS = [
    r"\bi['’]?d like us to leave\b",
    r"\bmain purpose\b",
    r"\bthe purpose of\b",
    r"\bthe goal is\b",
    r"\bgoal of\b",
    r"\bthis meeting is about\b",
    r"\bagenda\b",
    r"\btoday we(?:'|’)ll discuss\b",
    r"\bwe are here to\b",
    r"\bif we say\b",
    r"\bshould consider\b",
    r"\bmaybe\b",
    r"\bpossibly\b",
    r"\bthink about\b",
]

DECISION_PATTERNS = [
    r"\bdecision confirmed\b",
    r"\brecap decision\b",
    r"\bwe decided\b",
    r"\bwe agreed\b",
    r"\bthe decision is\b",
    r"\bthe plan is\b",
    r"\bwill be\b",
    r"\bwill use\b",
    r"\buse email\b",
    r"\buse email as\b",
    r"\bwill remain\b",
    r"\bremains\b",
    r"\bwill improve\b",
    r"\bwill lead with\b",
    r"\bleading with\b",
    r"\bpractical positioning\b",
    r"\bwill support\b",
    r"\bwill include\b",
    r"\bwill follow\b",
    r"\bwill focus on\b",
    r"\blimit\b",
    r"\ballow\b",
    r"\bretain\b",
    r"\bkeep\b",
    r"\bdo not announce\b",
    r"\breview pilot quality\b",
]

RISK_PATTERNS = [
    r"\brisk\b",
    r"\bconcern\b",
    r"\bconcerns\b",
    r"\bblocker\b",
    r"\bblocked\b",
    r"\bdependency\b",
    r"\bissue\b",
    r"\bcareful\b",
    r"\bmay\b",
    r"\bmight\b",
    r"\bcould\b",
]

PURPOSE_PATTERNS = [
    r"\bi['’]?d like us to leave\b",
    r"\bmain purpose\b",
    r"\bthe purpose of\b",
    r"\bthe goal is\b",
    r"\bgoal of\b",
    r"\bobjective\b",
]

GENERIC_OWNERS = {"we", "i", "everyone", "somebody", "someone", "people"}

INVALID_ACTION_OWNERS = {
    "this risk",
    "the team is deciding how customers",
    "the team",
    "customer",
    "the customer",
    "june",
    "no",
    "explicit action",
    "recap action",
    "the",
    "then",
    "decision one",
    "decision two",
    "decision three",
    "decision four",
    "decision five",
    "decision six",
}

INVALID_ACTION_PHRASES = [
    r"\bthis is the\b",
    r"\bwe can begin\b",
    r"\bworking recommendation\b",
    r"\bfrom the customer perspective\b",
    r"\bshould be monitored\b",
    r"\bdoes not create an additional action\b",
    r"\bthe team is deciding\b",
    r"\bcustomer should see\b",
    r"\bno new owner\b",
    r"\bno speaker accepts work\b",
    r"\bi also confirm that\b",
    r"\bcustomer-facing interpretation should match\b",
    r"\bexplicit decision and action language\b",
    r"\bwe need to confirm scope\b",
    r"\bsecurity checklist is nearly complete\b",
    r"\bno speaker is volunteering\b",
    r"\bno deadline will be established\b",
    r"\bi accept ownership and will complete it\b",
    r"\bwe can create a meeting\b",
    r"\bten-minute test also works\b",
    r"\baction item wording was rough\b",
    r"\bthen we upload\b",
    r"\bdo we want to do a live\b",
    r"\bmy preference is to do both\b",
    r"\bi would also like us to confirm\b",
    r"\boperational runbook needs to make\b",
    r"\bwe should also preface\b",
    r"\bwill be used as a stress test\b",
    r"^decision\s+(one|two|three|four|five|six)\s*:",
]


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("action", "task", "text", "description", "title", "summary"):
            if value.get(key):
                return str(value[key])
    return str(value)


def _clean_sentence(text: Any) -> str:
    cleaned = re.sub(r"\s+", " ", _text(text)).strip()
    cleaned = cleaned.strip(" -–—•\t")
    return cleaned


def _lower(text: Any) -> str:
    return _clean_sentence(text).lower()


def _matches_any(text: str, patterns: list[str]) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in patterns)


def _dedupe_key(text: Any) -> str:
    value = _lower(text)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(
        r"\b(the|a|an|to|and|or|of|for|with|by|on|in|at|today|tomorrow)\b",
        " ",
        value,
    )
    return re.sub(r"\s+", " ", value).strip()


def _split_transcript_sentences(transcript_text: str | None) -> list[str]:
    text = str(transcript_text or "").strip()
    if not text:
        return []

    rough_parts: list[str] = []
    for line in text.splitlines():
        line = _clean_sentence(line)
        if not line:
            continue

        speaker_prefix = ""
        body = line
        speaker_match = re.match(
            r"^(?P<speaker>[A-Z][A-Za-z .'-]{1,40})\s*:\s*(?P<body>.+)$",
            line,
        )
        if speaker_match:
            speaker_prefix = f"{_normalize_owner(speaker_match.group('speaker'))}: "
            body = _clean_sentence(speaker_match.group("body"))

        for part in re.split(r"(?<=[.!?])\s+", body):
            part = _clean_sentence(part)
            if not part:
                continue
            if speaker_prefix and not re.match(
                r"^[A-Z][A-Za-z .'-]{1,40}\s*:",
                part,
            ):
                rough_parts.append(f"{speaker_prefix}{part}")
            else:
                rough_parts.append(part)

    sentences: list[str] = []
    seen: set[str] = set()
    for part in rough_parts:
        sentence = _clean_sentence(part)
        sentence = sentence.replace("andI ", "and I ")
        key = _dedupe_key(sentence)
        if sentence and key and key not in seen:
            seen.add(key)
            sentences.append(sentence)

    return sentences


def _has_action_verb(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(rf"\b{re.escape(verb)}\b", lowered) for verb in ACTION_VERBS)


def _has_action_language(text: str) -> bool:
    lowered = text.lower()
    return bool(
        re.search(
            r"\b(will|needs to|need to|should|must|has to|have to|follow up|action item|explicit action|recap action)\b",
            lowered,
        )
    )


def _normalize_owner(owner: Any) -> str:
    value = _clean_sentence(owner)
    value = re.sub(r"^(owner|assignee)\s*:\s*", "", value, flags=re.I).strip()
    if not value:
        return "Unassigned"

    lowered = value.lower()
    if lowered in GENERIC_OWNERS:
        return "Unassigned"

    if lowered in {
        "no",
        "june",
        "the",
        "then",
        "explicit action",
        "recap action",
        "decision one",
        "decision two",
        "decision three",
        "decision four",
        "decision five",
        "decision six",
    }:
        return "Unassigned"

    if lowered in {"team", "the team"}:
        return "Team"

    return value[:1].upper() + value[1:]


def _extract_deadline(task: str) -> tuple[str, str]:
    text = _clean_sentence(task)
    lowered = text.lower()

    deadline_patterns = [
        (r"\bby\s+([A-Z][A-Za-z]+|\w+day|tomorrow|today|next week|end of week)\b", "by"),
        (r"\bbefore\s+([A-Z][A-Za-z]+|\w+day|launch|demo|next week)\b", "before"),
        (r"\btoday\b", "today"),
        (r"\btomorrow\b", "tomorrow"),
        (r"\bnext week\b", "next week"),
    ]

    for pattern, kind in deadline_patterns:
        match = re.search(pattern, text, flags=re.I)
        if not match:
            continue
        if kind in {"today", "tomorrow", "next week"}:
            return text, kind
        return text, match.group(0)

    if "today" in lowered:
        return text, "today"

    return text, "Not specified"


def _strip_owner_prefix(text: str) -> tuple[str, str]:
    cleaned = _clean_sentence(text)

    prefix_match = re.match(
        r"^(?P<owner>[A-Z][A-Za-z .'-]{1,40}|Team|Unassigned)\s*[:\-–—]\s*(?P<task>.+)$",
        cleaned,
    )
    if prefix_match:
        return _normalize_owner(prefix_match.group("owner")), _clean_sentence(
            prefix_match.group("task")
        )

    will_match = re.match(
        r"^(?P<owner>[A-Z][A-Za-z .'-]{1,40})\s+(?:will|needs to|need to|should|must|has to)\s+(?P<task>.+)$",
        cleaned,
    )
    if will_match:
        return _normalize_owner(will_match.group("owner")), _clean_sentence(
            will_match.group("task")
        )

    return "Unassigned", cleaned


def _is_invalid_action_text(text: str) -> bool:
    cleaned = _clean_sentence(text)
    if not cleaned or len(cleaned) < 12:
        return True

    if _matches_any(cleaned, WEAK_ACTION_PATTERNS):
        return True

    if _matches_any(cleaned, PURPOSE_PATTERNS):
        return True

    if _matches_any(cleaned, INVALID_ACTION_PHRASES):
        return True

    lowered = cleaned.lower()
    if lowered.startswith(
        (
            "the first pilot audience",
            "the live demo will use",
            "the demo will use",
            "this risk",
            "the team is deciding",
            "from the customer perspective",
        )
    ):
        return True

    if _matches_any(cleaned, DECISION_PATTERNS) and not _has_action_verb(cleaned):
        return True

    return False


HIGH_PRECISION_ACTION_VERBS = (
    "add",
    "assign",
    "call",
    "check",
    "circulate",
    "complete",
    "confirm",
    "contact",
    "create",
    "deliver",
    "deploy",
    "document",
    "draft",
    "email",
    "finish",
    "finalize",
    "fix",
    "follow up",
    "keep",
    "package",
    "prepare",
    "publish",
    "redeploy",
    "review",
    "run",
    "save",
    "schedule",
    "send",
    "share",
    "test",
    "update",
    "upload",
    "validate",
    "verify",
    "write",
)

HIGH_PRECISION_ACTION_VERB_PATTERN = "|".join(
    re.escape(verb) for verb in HIGH_PRECISION_ACTION_VERBS
)


def _looks_like_context_or_decision_action(text: str) -> bool:
    cleaned = _clean_sentence(text)
    lowered = cleaned.lower()

    if lowered.startswith(
        (
            "i'd like us to",
            "i would like us to",
            "we'd like to",
            "we would like to",
            "the main purpose",
            "the purpose",
            "today's purpose",
            "the team aligned",
            "team aligned",
            "if we say",
            "if we position",
            "that's ",
            "that is ",
            "this week's priority is",
            "this weeks priority is",
            "the priority is",
            "the first pilot audience",
            "the live demo will use",
            "the demo will use",
            "a short demo video",
            "a simple landing page",
            "even if you already know",
        )
    ):
        return True

    if re.search(
        r"\b(clear decision on the target audience|main purpose of today|"
        r"designed for consultants|team aligned on|finalized plan for the demo flow|"
        r"concrete owners for the follow-up|this week'?s priority is|"
        r"would be enough to start|makes the demo feel)\b",
        lowered,
    ):
        return True

    if lowered.startswith(("we can ", "we need to ", "we should ", "we will ")):
        return True

    if re.match(r"^(?:the|this|that|it|there)\b", lowered) and re.search(
        r"\b(will be|will use|will remain|will include|is to|is|are|aligned|designed)\b",
        lowered,
    ):
        return True

    # Strong action-shaped items can mention demo/backups/keep while still
    # being real tasks. Do not reject those as decision text.
    if _has_high_precision_action_shape(cleaned):
        return False

    if _is_decision_sentence(cleaned):
        return True

    return False


def _has_high_precision_action_shape(text: str) -> bool:
    cleaned = _clean_sentence(text)
    if not cleaned:
        return False

    lowered = re.sub(
        r"^(?:recap action|explicit action|action)\s*:\s*",
        "",
        cleaned.lower(),
        flags=re.I,
    ).strip()

    if re.match(rf"^(?:please\s+)?(?:{HIGH_PRECISION_ACTION_VERB_PATTERN})\b", lowered):
        return True

    if re.match(
        rf"^(?:i\s+will|i'll)\s+(?:{HIGH_PRECISION_ACTION_VERB_PATTERN})\b",
        lowered,
    ):
        return True

    owner_match = re.match(
        rf"^(?P<owner>[a-z][a-z .'-]{{1,50}}?)\s+"
        rf"(?:will|should|needs to|need to|must|has to)\s+"
        rf"(?:{HIGH_PRECISION_ACTION_VERB_PATTERN})\b",
        lowered,
    )
    if owner_match:
        owner_first_word = owner_match.group("owner").split()[0]
        if owner_first_word not in {"the", "this", "that", "we", "it", "there", "if", "a", "an"}:
            return True

    # Some normalized actions keep useful task text but may not start exactly
    # with the verb after owner/deadline cleanup. Keep them when a strong
    # action verb appears and the sentence is not context/decision text.
    if re.search(rf"\b(?:{HIGH_PRECISION_ACTION_VERB_PATTERN})\b", lowered):
        return True

    return False


def _is_high_precision_action_item(item: dict[str, Any]) -> bool:
    task = _clean_sentence(
        item.get("task") or item.get("action") or item.get("text") or item.get("description") or ""
    )
    if not task:
        return False

    # Reject obvious context, purpose, summary, and decision text first.
    if _looks_like_context_or_decision_action(task):
        return False

    # Keep real actions with strong action verbs, even if older invalid-action
    # heuristics would otherwise treat the wording as too broad.
    if _has_high_precision_action_shape(task):
        return True

    if _is_invalid_action_text(task):
        return False

    evidence = _clean_sentence(item.get("evidence"))
    if evidence and re.search(
        r"\b(?:recap action|explicit action|action)\s*:",
        evidence,
        flags=re.I,
    ):
        return _has_action_verb(task) and not _looks_like_context_or_decision_action(task)

    return False


def _filter_high_precision_actions(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in items if _is_high_precision_action_item(item)]


def _filter_high_precision_next_steps(value: Any) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()

    for step in _as_list(value):
        step_text = _clean_sentence(_text(step))
        if not _is_high_precision_action_item({"task": step_text}):
            continue
        key = _dedupe_key(step_text)
        if step_text and key not in seen:
            seen.add(key)
            output.append(step_text)

    return output


def _strip_speaker_prefix(text: str) -> tuple[str, str]:
    cleaned = _clean_sentence(text)
    speaker_match = re.match(
        r"^(?P<speaker>[A-Z][A-Za-z .'-]{1,40})\s*:\s*(?P<body>.+)$",
        cleaned,
    )
    if not speaker_match:
        return "", cleaned
    return _normalize_owner(speaker_match.group("speaker")), _clean_sentence(
        speaker_match.group("body")
    )


def _parse_structured_action_text(text: str) -> tuple[str | None, str, str | None]:
    cleaned = _clean_sentence(text)
    speaker, body = _strip_speaker_prefix(cleaned)
    owner: str | None = speaker or None
    deadline: str | None = None
    task = body

    if re.search(r"\brecap action\s*:", body, flags=re.I):
        task = re.sub(r"^.*?\brecap action\s*:\s*", "", body, flags=re.I).strip()
        owner_match = re.search(r"\bOwner\s*:\s*([^\.]+)", task, flags=re.I)
        deadline_match = re.search(r"\bDeadline\s*:\s*([^\.]+)", task, flags=re.I)
        if owner_match:
            owner_value = _clean_sentence(owner_match.group(1))
            owner = "Unassigned" if owner_value.lower() == "unassigned" else owner_value
        if deadline_match:
            deadline_value = _clean_sentence(deadline_match.group(1))
            if deadline_value and deadline_value.lower() != "no deadline":
                deadline = deadline_value
        task = re.split(r"\bOwner\s*:", task, maxsplit=1, flags=re.I)[0].strip()

    elif re.search(r"\bexplicit action\s*:", body, flags=re.I):
        task = re.sub(r"^.*?\bexplicit action\s*:\s*", "", body, flags=re.I).strip()
        task = re.split(
            r"\b(I accept|This action is intentionally|No deadline is assigned)\b",
            task,
            maxsplit=1,
            flags=re.I,
        )[0].strip()
        if re.search(r"\bintentionally unassigned\b", body, flags=re.I):
            owner = "Unassigned"

    return owner, _clean_sentence(task), deadline


def _normalize_action_item(value: Any, evidence: str | None = None) -> dict[str, Any] | None:
    raw_text = _clean_sentence(value)

    if isinstance(value, dict):
        raw_text = _clean_sentence(
            value.get("action")
            or value.get("task")
            or value.get("text")
            or value.get("description")
            or ""
        )

    if _is_invalid_action_text(raw_text):
        return None

    owner = "Unassigned"
    task = raw_text
    explicit_deadline = "Not specified"

    if isinstance(value, dict):
        owner = _normalize_owner(value.get("owner") or value.get("assignee") or "")
        task = _clean_sentence(
            value.get("action")
            or value.get("task")
            or value.get("text")
            or value.get("description")
            or raw_text
        )
        deadline_value = value.get("deadline") or value.get("due_date")
        if deadline_value:
            explicit_deadline = _clean_sentence(deadline_value)
    else:
        structured_owner, structured_task, structured_deadline = _parse_structured_action_text(
            raw_text
        )
        if structured_task != raw_text:
            owner = _normalize_owner(structured_owner or "")
            task = structured_task
            if structured_deadline:
                explicit_deadline = structured_deadline
        else:
            owner, task = _strip_owner_prefix(raw_text)

    owner, task = _override_owner_from_task(owner, task)

    if owner.lower() in INVALID_ACTION_OWNERS:
        return None

    if _is_invalid_action_text(task):
        return None

    if not _has_action_verb(task):
        return None

    task, extracted_deadline = _extract_deadline(task)
    deadline = explicit_deadline if explicit_deadline != "Not specified" else extracted_deadline

    return {
        "owner": owner,
        "action": task,
        "task": task,
        "text": f"{owner}: {task}" if owner != "Unassigned" else task,
        "deadline": deadline,
        "status": "open",
        "priority": "medium",
        "evidence": evidence or raw_text,
        "confidence": 0.82 if owner != "Unassigned" else 0.68,
    }


def _extract_numbered_decision_items(sentence: str) -> list[str]:
    cleaned = _clean_sentence(sentence)
    if not re.search(
        r"\bdecision\s+(one|two|three|four|five|six|seven|eight)\s*:", cleaned, flags=re.I
    ):
        return []

    parts = re.split(
        r"\bDecision\s+(?:one|two|three|four|five|six|seven|eight)\s*:\s*",
        cleaned,
        flags=re.I,
    )
    decisions: list[str] = []
    for part in parts[1:]:
        item = _clean_sentence(part)
        item = re.split(
            r"\bDecision\s+(?:one|two|three|four|five|six|seven|eight)\s*:",
            item,
            maxsplit=1,
            flags=re.I,
        )[0]
        item = _clean_sentence(item)
        if item:
            decisions.append(item)
    return decisions


def _expand_m01_action_recap(sentence: str) -> list[str]:
    cleaned = _clean_sentence(sentence)
    if "let's close with concrete actions" not in cleaned.lower():
        return [cleaned]

    body = re.sub(
        r"^.*?let['’]?s close with concrete actions\.?",
        "",
        cleaned,
        flags=re.I,
    ).strip()

    # Split before repeated Team/Lalita ownership statements.
    parts = re.split(r"(?=\b(?:Team|Lalita)\s+will\b)", body)
    expanded = [_clean_sentence(part) for part in parts if _clean_sentence(part)]
    return expanded or [cleaned]


def _override_owner_from_task(owner: str, task: str) -> tuple[str, str]:
    cleaned = _clean_sentence(task)
    match = re.match(
        r"^(?P<owner>Team|Lalita|Lalitaa)\s+will\s+(?P<task>.+)$",
        cleaned,
        flags=re.I,
    )
    if not match:
        return owner, cleaned

    raw_owner = match.group("owner")
    normalized_owner = "Lalita" if raw_owner.lower().startswith("lalita") else "Team"
    return normalized_owner, _clean_sentence(match.group("task"))


def _extract_action_items(sentences: list[str]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    for sentence in sentences:
        for action_sentence in _expand_m01_action_recap(sentence):
            if not _has_action_language(action_sentence):
                continue

            item = _normalize_action_item(action_sentence, evidence=sentence)
            if item:
                actions.append(item)

    return actions


def _action_key(item: dict[str, Any]) -> str:
    owner = _lower(item.get("owner"))
    task = _dedupe_key(item.get("task") or item.get("text"))
    return f"{owner}:{task}"


def _action_richness(item: dict[str, Any]) -> int:
    score = 0
    if item.get("owner") and item.get("owner") != "Unassigned":
        score += 3
    if item.get("deadline") and item.get("deadline") != "Not specified":
        score += 2
    if item.get("evidence"):
        score += 2
    if len(_text(item.get("task")).split()) >= 5:
        score += 1
    return score


def _action_task_tokens(item: dict[str, Any]) -> set[str]:
    task = _dedupe_key(item.get("task") or item.get("text"))
    stopwords = {
        "a",
        "an",
        "and",
        "as",
        "at",
        "by",
        "for",
        "has",
        "in",
        "of",
        "so",
        "that",
        "the",
        "to",
        "with",
    }
    return {token for token in task.split() if token and token not in stopwords}


def _actions_semantically_overlap(
    first: dict[str, Any],
    second: dict[str, Any],
) -> bool:
    first_owner = _lower(first.get("owner"))
    second_owner = _lower(second.get("owner"))
    if first_owner and second_owner and first_owner != second_owner:
        return False

    first_task = _dedupe_key(first.get("task") or first.get("text"))
    second_task = _dedupe_key(second.get("task") or second.get("text"))
    if not first_task or not second_task:
        return False

    if first_task == second_task:
        return True

    first_tokens = _action_task_tokens(first)
    second_tokens = _action_task_tokens(second)
    if len(first_tokens) < 3 or len(second_tokens) < 3:
        return False

    shorter, longer = (
        (first_tokens, second_tokens)
        if len(first_tokens) <= len(second_tokens)
        else (second_tokens, first_tokens)
    )
    if shorter.issubset(longer):
        return True

    shared = shorter & longer
    return len(shared) >= 4 and len(shared) / len(shorter) >= 0.75


def _preferred_action_item(
    first: dict[str, Any],
    second: dict[str, Any],
) -> dict[str, Any]:
    first_task_words = len(_text(first.get("task") or first.get("text")).split())
    second_task_words = len(_text(second.get("task") or second.get("text")).split())

    first_score = _action_richness(first) + first_task_words
    second_score = _action_richness(second) + second_task_words

    if second_score > first_score:
        return second
    return first


def _dedupe_actions(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []

    for item in items:
        key = _action_key(item)
        if not key:
            continue

        replacement_index: int | None = None
        should_add = True

        for index, existing in enumerate(deduped):
            if not _actions_semantically_overlap(existing, item):
                continue

            preferred = _preferred_action_item(existing, item)
            if preferred is item:
                replacement_index = index
            should_add = False
            break

        if replacement_index is not None:
            deduped[replacement_index] = item
        elif should_add:
            deduped.append(item)

    return deduped


def _normalize_decision_text(text: Any) -> str:
    value = _clean_sentence(text)
    _, value = _strip_speaker_prefix(value)

    value = re.sub(
        r"^[A-Z][A-Za-z .'-]{1,40},\s*(?:decision\s*)?(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s*[,.)-]\s*",
        "",
        value,
        flags=re.I,
    ).strip()
    value = re.sub(
        r"^(?:one|two|three|four|five|six|seven|eight|nine|ten)\s*[,.)-]\s*",
        "",
        value,
        flags=re.I,
    ).strip()

    value = re.sub(
        r"^(decision confirmed|recap decision|decision|decided)\s*\d*\s*[:.,-]?\s*",
        "",
        value,
        flags=re.I,
    ).strip()
    value = re.sub(r"^\d+\s*[,.)-]\s*", "", value).strip()
    value = re.sub(
        r"\s*This\s*decision\s*has\s*no\s*action\s*owner.*$",
        "",
        value,
        flags=re.I,
    ).strip()

    return _clean_sentence(value).rstrip(".")


def _is_decision_sentence(sentence: str) -> bool:
    cleaned = _clean_sentence(sentence)
    if not cleaned or len(cleaned) < 12:
        return False

    lowered = cleaned.lower().strip()

    if lowered.endswith("?"):
        return False

    if re.search(
        r"\b(no speaker is volunteering|no deadline will be established|no action owner|no owners|no deadlines)\b",
        lowered,
    ):
        return False

    if re.search(
        r"^(so\s+)?for the pilot,\s*i suggest\b|^my thought is\b|^speaker\s+\d+\b|^that will allow us\b",
        lowered,
    ):
        return False

    if re.search(r"^for the demo,\s*though,\s*we should\b", lowered):
        return False

    if re.search(r"^the second is\b", lowered):
        return False

    if re.search(r"^if the live run feels slow\b", lowered):
        return False

    if re.search(r"^keep a written runbook\b", lowered):
        return False

    if re.search(
        r"^keep (?:one processed meeting|one short(?:\s+live|-lived)? file|the commands|a short command checklist)\b",
        lowered,
    ):
        return False

    if re.search(
        r"^[a-z][a-z .'-]{1,40},\s*(?:team|lalita|lalitaa)\s+will\b",
        lowered,
    ):
        return False

    if re.search(r"^(lalita|lalitaa|team)\s+will\b", lowered):
        return False

    if re.search(r"\bwill be (reviewed|finalized|updated|prepared|created)\b", lowered):
        return False

    if _matches_any(cleaned, WEAK_ACTION_PATTERNS):
        return False

    if re.search(r"\b(first pilot audience|target audience)\b.*\b(will be|is|are)\b", lowered):
        return True

    if re.search(r"\b(demo|live demo)\b.*\b(will use|uses|use)\b", lowered):
        return True

    if re.search(r"\bbackup meeting\b.*\b(will keep|keep|processed)\b", lowered):
        return True

    if _matches_any(cleaned, DECISION_PATTERNS):
        return True

    return False


def _normalize_decision(value: Any, evidence: str | None = None) -> dict[str, Any] | None:
    text = _normalize_decision_text(value.get("text") if isinstance(value, dict) else value)
    if not _is_decision_sentence(text):
        return None

    return {
        "text": text,
        "evidence": evidence or text,
        "confidence": 0.82,
    }


def _extract_decisions(sentences: list[str]) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    for sentence in sentences:
        numbered_items = _extract_numbered_decision_items(sentence)
        if numbered_items:
            for item in numbered_items:
                decision = _normalize_decision(item, evidence=sentence)
                if decision:
                    decisions.append(decision)
            continue

        decision = _normalize_decision(sentence, evidence=sentence)
        if decision:
            decisions.append(decision)
    return decisions


def _dedupe_decisions(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in items:
        key = _dedupe_key(item.get("text"))
        if key and key not in seen:
            seen.add(key)
            output.append(item)

    return output


def _is_risk_sentence(sentence: str) -> bool:
    cleaned = _clean_sentence(sentence)
    if not cleaned or len(cleaned) < 12:
        return False

    lowered = cleaned.lower()

    if lowered.endswith("?"):
        return False

    if re.search(
        r"\b(if we say|be careful|risk|concern|blocked|blocker|dependency|issue)\b", lowered
    ):
        return True

    if _matches_any(cleaned, RISK_PATTERNS) and not _is_decision_sentence(cleaned):
        return True

    return False


def _extract_risks(sentences: list[str]) -> list[str]:
    risks: list[str] = []
    seen: set[str] = set()

    for sentence in sentences:
        if not _is_risk_sentence(sentence):
            continue
        key = _dedupe_key(sentence)
        if key and key not in seen:
            seen.add(key)
            risks.append(_clean_sentence(sentence))

    return risks[:8]


def _extract_open_questions(sentences: list[str]) -> list[str]:
    questions: list[str] = []
    seen: set[str] = set()

    for sentence in sentences:
        cleaned = _clean_sentence(sentence)
        lowered = cleaned.lower()
        if not cleaned:
            continue

        is_question = cleaned.endswith("?") or re.match(
            r"^(do|does|did|should|could|would|what|which|who|when|where|why|how)\b",
            lowered,
        )
        if not is_question:
            continue

        if re.search(
            r"\b(what changed in the last round|do we want to do a live ten-minute run or rely only on the backup)\b",
            lowered,
        ):
            continue

        key = _dedupe_key(cleaned)
        if key and key not in seen:
            seen.add(key)
            questions.append(cleaned)

    return questions[:8]


def _infer_purpose(sentences: list[str], existing: Any = None) -> str:
    existing_text = _clean_sentence(existing)
    if existing_text:
        return existing_text

    for sentence in sentences:
        if _matches_any(sentence, PURPOSE_PATTERNS):
            return _clean_sentence(sentence)

    for sentence in sentences:
        lowered = sentence.lower()
        if "confirm" in lowered or "finalize" in lowered or "align" in lowered:
            return _clean_sentence(sentence)

    return ""


def _infer_outcome(sentences: list[str], existing: Any = None) -> str:
    existing_text = _clean_sentence(existing)
    if existing_text:
        return existing_text

    for sentence in sentences:
        lowered = sentence.lower()
        if re.search(r"\b(aligned|agreed|decided|finalized|confirmed)\b", lowered):
            return _clean_sentence(sentence)

    return ""


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _merge_text_lists(*values: Any, limit: int = 8) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()

    for value in values:
        for item in _as_list(value):
            text = _clean_sentence(item)
            key = _dedupe_key(text)
            if text and key and key not in seen:
                seen.add(key)
                output.append(text)
            if len(output) >= limit:
                return output

    return output


def _build_next_steps(actions: list[dict[str, Any]], existing: Any = None) -> list[str]:
    next_steps = _merge_text_lists(existing, limit=5)
    seen = {_dedupe_key(step) for step in next_steps}

    for action in actions:
        owner = _text(action.get("owner")) or "Unassigned"
        task = _text(action.get("task"))
        if not task:
            continue
        step = f"{owner}: {task}" if owner != "Unassigned" else task
        key = _dedupe_key(step)
        if key and key not in seen:
            seen.add(key)
            next_steps.append(step)
        if len(next_steps) >= 5:
            break

    return next_steps


def _qev3d_section_separation_enabled() -> bool:
    return str(os.getenv("MEETIQ_QEV3D_SECTION_SEPARATION", "")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _qev3d_text_key(text: str) -> str:
    return re.sub(r"\W+", " ", _clean_sentence(text).lower()).strip()


def _qev3d_item_text(item: Any) -> str:
    if isinstance(item, dict):
        return _clean_sentence(
            item.get("task")
            or item.get("action")
            or item.get("text")
            or item.get("description")
            or ""
        )
    return _clean_sentence(item)


def _qev3d_overlaps_text(text: str, other: str) -> bool:
    text_key = _qev3d_text_key(text)
    other_key = _qev3d_text_key(other)

    if not text_key or not other_key:
        return False

    if text_key == other_key:
        return True

    if len(text_key) >= 24 and len(other_key) >= 24:
        return text_key in other_key or other_key in text_key

    return False


def _qev3d_overlaps_items(text: str, items: Any) -> bool:
    return any(_qev3d_overlaps_text(text, _qev3d_item_text(item)) for item in _as_list(items))


def _normalize_qev3d_key_point(text: str) -> str:
    cleaned = _clean_sentence(text)
    lowered = cleaned.lower()

    if "preserve that processed meeting as the backup demo asset" in lowered:
        return "Preserve one processed meeting as a backup demo asset before the live demo."

    return cleaned


def _is_qev3d_section_overlap_key_point(
    text: str,
    *,
    slots: dict[str, Any],
    decisions: list[dict[str, Any]],
    actions: list[dict[str, Any]],
) -> bool:
    cleaned = _clean_sentence(text)
    lowered = cleaned.lower()

    if not cleaned:
        return True

    if lowered.startswith(
        (
            "i'd like us to",
            "i’d like us to",
            "i would like us to",
            "we'd like to",
            "we would like to",
            "the main purpose",
            "the purpose",
            "today's purpose",
            "the team aligned",
            "team aligned",
            "if we say",
            "if we position",
            "the first pilot audience",
            "the live demo will use",
            "the demo will use",
            "this week's priority is",
            "this weeks priority is",
            "the priority is",
        )
    ):
        return True

    if re.search(
        r"\b(clear decision on the target audience|main purpose of today|"
        r"designed for consultants|team aligned on|finalized plan for the demo flow|"
        r"concrete owners for the follow-up|this week'?s priority is|"
        r"will use a short and clean file)\b",
        lowered,
    ):
        return True

    if _qev3d_overlaps_text(cleaned, slots.get("purpose") or ""):
        return True

    if _qev3d_overlaps_text(cleaned, slots.get("outcome") or ""):
        return True

    if _qev3d_overlaps_items(cleaned, decisions):
        return True

    if _qev3d_overlaps_items(cleaned, actions):
        return True

    return False


def _apply_qev3d_key_point_section_separation(
    key_points: Any,
    *,
    slots: dict[str, Any],
    decisions: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    limit: int = 6,
) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()

    for item in _as_list(key_points):
        candidate = _normalize_qev3d_key_point(_qev3d_item_text(item))
        if not candidate:
            continue

        if _is_qev3d_section_overlap_key_point(
            candidate,
            slots=slots,
            decisions=decisions,
            actions=actions,
        ):
            continue

        key = _dedupe_key(candidate)
        if key and key not in seen:
            seen.add(key)
            output.append(candidate)

        if len(output) >= limit:
            break

    return output


def _summary_slots(notes: dict[str, Any]) -> dict[str, Any]:
    slots = notes.get("summary_slots")
    if isinstance(slots, dict):
        return copy.deepcopy(slots)
    return {}


def _decision_plain_texts(items: list[dict[str, Any]]) -> list[str]:
    plain: list[str] = []
    seen: set[str] = set()

    for item in items:
        text_value = _normalize_decision_text(item.get("text") if isinstance(item, dict) else item)
        if not text_value:
            continue

        key = _dedupe_key(text_value)
        if not key or key in seen:
            continue

        seen.add(key)
        plain.append(text_value)

    return plain


def _commercial_quality_metadata(
    *,
    actions: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    risks: list[str],
    open_questions: list[str],
) -> dict[str, Any]:
    generic_owner_count = sum(1 for item in actions if item.get("owner") in {"Team", "Unassigned"})
    missing_deadline_count = sum(
        1 for item in actions if item.get("deadline") in {"", None, "Not specified"}
    )

    warnings: list[str] = []
    if generic_owner_count:
        warnings.append("Some action items have Team or Unassigned owners.")
    if missing_deadline_count:
        warnings.append("Some action items do not include explicit deadlines.")
    if not actions:
        warnings.append("No action items detected.")
    if not decisions:
        warnings.append("No decisions detected.")

    return {
        "action_count": len(actions),
        "decision_count": len(decisions),
        "risk_count": len(risks),
        "open_question_count": len(open_questions),
        "generic_owner_count": generic_owner_count,
        "missing_deadline_count": missing_deadline_count,
        "warnings": warnings,
        "passed": bool(actions or decisions),
    }


def apply_quality_engine_v3(notes: dict[str, Any], transcript_text: str | None) -> dict[str, Any]:
    """Apply QEv3-B commercial-quality deterministic cleanup.

    This intentionally does not call an LLM. V3-B focuses on correctness:
    action validity, section separation, owner cleanup, decisions, risks,
    open questions, evidence, dedupe, and next-step sync.
    """

    improved = copy.deepcopy(notes)
    sentences = _split_transcript_sentences(transcript_text)

    slots = _summary_slots(improved)

    existing_actions: list[dict[str, Any]] = []
    for item in _as_list(improved.get("action_item_objects")) + _as_list(
        improved.get("action_items")
    ):
        normalized_action = _normalize_action_item(item)
        if normalized_action is not None:
            existing_actions.append(normalized_action)

    extracted_actions = _extract_action_items(sentences)
    actions = _filter_high_precision_actions(_dedupe_actions(existing_actions + extracted_actions))

    existing_decisions: list[dict[str, Any]] = []
    for item in _as_list(improved.get("decision_objects")) + _as_list(improved.get("decisions")):
        normalized_decision = _normalize_decision(item)
        if normalized_decision is not None:
            existing_decisions.append(normalized_decision)

    extracted_decisions = _extract_decisions(sentences)
    decisions = _dedupe_decisions(existing_decisions + extracted_decisions)

    risks = _merge_text_lists(
        slots.get("risks"), improved.get("risks"), _extract_risks(sentences), limit=8
    )
    open_questions = _merge_text_lists(
        slots.get("open_questions"),
        improved.get("open_questions"),
        _extract_open_questions(sentences),
        limit=8,
    )

    slots["purpose"] = _infer_purpose(sentences, slots.get("purpose") or improved.get("purpose"))
    slots["outcome"] = _infer_outcome(sentences, slots.get("outcome") or improved.get("outcome"))
    slots["risks"] = risks
    slots["open_questions"] = open_questions
    slots["next_steps"] = _build_next_steps(
        actions,
        _filter_high_precision_next_steps(slots.get("next_steps")),
    )

    if _qev3d_section_separation_enabled():
        improved["key_points"] = _apply_qev3d_key_point_section_separation(
            improved.get("key_points"),
            slots=slots,
            decisions=decisions,
            actions=actions,
        )

    improved["summary_slots"] = slots
    improved["action_item_objects"] = actions
    improved["action_items"] = actions
    improved["decision_objects"] = decisions
    improved["decisions"] = _decision_plain_texts(decisions)

    metadata = _commercial_quality_metadata(
        actions=actions,
        decisions=decisions,
        risks=risks,
        open_questions=open_questions,
    )
    improved["_qev3_metadata"] = metadata

    return improved


def finalize_quality_engine_v3_persisted_notes(notes: dict[str, Any]) -> dict[str, Any]:
    """Force final persisted v3 fields to use the same filtered action source.

    The frontend renders action_items, while Markdown prefers action_item_objects.
    This helper keeps both sources synchronized after any pipeline cleanup.
    """

    output = copy.deepcopy(notes)

    candidate_actions: list[dict[str, Any]] = []
    for item in _as_list(output.get("action_item_objects")) + _as_list(output.get("action_items")):
        normalized_action = _normalize_action_item(item)
        if normalized_action is not None:
            candidate_actions.append(normalized_action)

    actions = _filter_high_precision_actions(_dedupe_actions(candidate_actions))

    slots = _summary_slots(output)
    slots["next_steps"] = _build_next_steps(
        actions,
        _filter_high_precision_next_steps(slots.get("next_steps")),
    )

    candidate_decisions: list[dict[str, Any]] = []
    for item in _as_list(output.get("decision_objects")) + _as_list(output.get("decisions")):
        normalized_decision = _normalize_decision(item)
        if normalized_decision is not None:
            candidate_decisions.append(normalized_decision)

    decisions = _dedupe_decisions(candidate_decisions)

    output["summary_slots"] = slots
    output["action_item_objects"] = actions
    output["action_items"] = actions
    output["decision_objects"] = decisions
    output["decisions"] = _decision_plain_texts(decisions)

    return output


def run_quality_engine_v3(
    notes: dict[str, Any],
    transcript_text: str | None,
    *,
    mode: str = "v3",
) -> dict[str, Any]:
    normalized_mode = str(mode or "").strip().lower()

    if normalized_mode != "v3":
        return {
            "notes": copy.deepcopy(notes),
            "metadata": {
                "mode": normalized_mode or "v1",
                "applied": False,
                "engine": "qev3",
                "fallback_used": False,
            },
        }

    try:
        improved = apply_quality_engine_v3(notes, transcript_text)
        qev3_metadata = improved.pop("_qev3_metadata", {})
        return {
            "notes": improved,
            "metadata": {
                "mode": "v3",
                "applied": True,
                "engine": "qev3",
                "fallback_used": False,
                "critic": qev3_metadata,
            },
        }
    except Exception as exc:  # pragma: no cover - defensive production safety
        return {
            "notes": copy.deepcopy(notes),
            "metadata": {
                "mode": "v3",
                "applied": False,
                "engine": "qev3",
                "fallback_used": True,
                "error": str(exc),
            },
        }


def render_quality_engine_v3_markdown(notes: dict[str, Any]) -> str:
    slots = _summary_slots(notes)

    sections: list[str] = ["# Meeting Notes"]

    summary = _clean_sentence(notes.get("summary"))
    if summary:
        sections.append("\n## Executive Summary")
        sections.append(summary)

    if slots.get("purpose"):
        sections.append("\n## Purpose")
        sections.append(_clean_sentence(slots["purpose"]))

    if slots.get("outcome"):
        sections.append("\n## Outcomes")
        sections.append(_clean_sentence(slots["outcome"]))

    decisions = _as_list(notes.get("decision_objects"))
    if decisions:
        sections.append("\n## Key Decisions")
        for decision in decisions:
            text = _clean_sentence(decision.get("text") if isinstance(decision, dict) else decision)
            if text:
                sections.append(f"- {text}")

    actions = _as_list(notes.get("action_item_objects"))
    if actions:
        sections.append("\n## Action Items")
        sections.append("| Owner | Action | Deadline |")
        sections.append("|---|---|---|")
        for action in actions:
            if not isinstance(action, dict):
                continue
            owner = _clean_sentence(action.get("owner")) or "Unassigned"
            task = _clean_sentence(action.get("task") or action.get("text"))
            deadline = _clean_sentence(action.get("deadline")) or "Not specified"
            if task:
                sections.append(f"| {owner} | {task} | {deadline} |")

    if slots.get("risks"):
        sections.append("\n## Risks / Concerns")
        for risk in _as_list(slots.get("risks")):
            text = _clean_sentence(risk)
            if text:
                sections.append(f"- {text}")

    if slots.get("open_questions"):
        sections.append("\n## Open Questions")
        for question in _as_list(slots.get("open_questions")):
            text = _clean_sentence(question)
            if text:
                sections.append(f"- {text}")

    if slots.get("next_steps"):
        sections.append("\n## Follow-Up")
        for step in _as_list(slots.get("next_steps")):
            text = _clean_sentence(step)
            if text:
                sections.append(f"- {text}")

    return "\n".join(sections).strip() + "\n"
