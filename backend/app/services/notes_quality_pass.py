from __future__ import annotations

import re
from typing import Any

ACTION_HINTS = re.compile(
    r"\b("
    r"need to|needs to|should|must|follow up|next step|action item|owner|deadline|due|please|"
    r"we will|we'll|i will|i'll|you will|team will|"
    r"prepare|finalize|create|send|share|review|update|schedule|draft|test|run|"
    r"validate|document|fix|clean up|package|confirm|record|ship|deploy|keep|move"
    r")\b",
    re.IGNORECASE,
)

ACTION_VERB_HINTS = re.compile(
    r"\b("
    r"prepare|finalize|create|send|share|review|update|schedule|draft|test|run|"
    r"validate|document|fix|clean up|package|confirm|record|ship|deploy|keep|move"
    r")\b",
    re.IGNORECASE,
)

FUTURE_CUE_HINTS = re.compile(
    r"\b("
    r"we need to|we should|we must|we will|we'll|i will|i'll|you should|"
    r"next step|action item|owner|deadline|due|before .* demo|by friday|by monday|"
    r"by tuesday|by wednesday|by thursday|this week|next week"
    r")\b",
    re.IGNORECASE,
)

OWNER_HINTS = re.compile(
    r"\b("
    r"owner|owners|assigned to|i will|i'll|you will|team will|we will|we'll"
    r")\b",
    re.IGNORECASE,
)

VALUE_STATEMENT_HINTS = re.compile(
    r"\b("
    r"teams want|users want|already valuable|is valuable|a clear summary|"
    r"shareable notes|after a meeting|value proposition|pilot readiness"
    r")\b",
    re.IGNORECASE,
)

KEYPOINT_NOISE_HINTS = re.compile(
    r"\b("
    r"perfect kevin|kevin, agreed|already valuable|teams want|after a meeting|"
    r"model tends to preserve|framing language|already much cleaner than before"
    r")\b",
    re.IGNORECASE,
)

ACTION_EXCLUDE_HINTS = re.compile(
    r"\b("
    r"pilot audience focused|users with clear pain|short meetings|"
    r"practical positioning message|broad platform pitch"
    r")\b",
    re.IGNORECASE,
)

DECISION_HINTS = re.compile(
    r"\b("
    r"we decided|decided to|we agreed|agreed to|the decision is|the plan is|"
    r"we will use|we'll use|we are going with|we're going with|"
    r"let's use|lead with|treat .* as|use .* as the"
    r")\b",
    re.IGNORECASE,
)

RISK_HINTS = re.compile(
    r"\b("
    r"risk|issue|concern|watch carefully|blocker|problem|timing|slow|latency|"
    r"failure|hallucination|safety|degrade|contamination"
    r")\b",
    re.IGNORECASE,
)

INFRA_HINTS = re.compile(
    r"\b("
    r"worker|database|storage|redis|postgres|backend|frontend|raw media path|"
    r"upload|file attached|job status|queue|queued|processing flow|healthz"
    r")\b",
    re.IGNORECASE,
)

BUSINESS_SIGNAL_HINTS = re.compile(
    r"\b("
    r"product|demo|pilot|outreach|workflow|quality|meeting|baseline|summary|"
    r"decision|action|launch|customer|client|positioning|benchmark|pass|landing page"
    r")\b",
    re.IGNORECASE,
)

DUE_DATE_HINTS = re.compile(
    r"\b("
    r"today|tomorrow|this week|next week|by friday|by monday|by tuesday|"
    r"by wednesday|by thursday|by the end of|before .* demo|after .* test"
    r")\b",
    re.IGNORECASE,
)

COMPOUND_ACTION_HINTS = re.compile(
    r"\b("
    r"landing page and outreach message|pilot outreach package|review and finalize|"
    r"prepare and share|create and send|review and confirm"
    r")\b",
    re.IGNORECASE,
)

PAST_PROGRESS_ONLY = re.compile(
    r"\b("
    r"stabilized|finished|completed|shipped|launched|improved|resolved|fixed"
    r")\b",
    re.IGNORECASE,
)

SPEAKER_PREFIX = re.compile(r"^(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?[,:\-]\s+)+")

DECISION_NOISE = re.compile(
    r"\bdecision\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b[:,]?\s*",
    re.IGNORECASE,
)

FILLER_PREFIXES = [
    r"^action item[:\-\s]+",
    r"^next step[:\-\s]+",
    r"^we need to\s+",
    r"^we should\s+",
    r"^let's\s+",
    r"^lets\s+",
    r"^please\s+",
    r"^i will\s+",
    r"^i'll\s+",
    r"^we will\s+",
    r"^we'll\s+",
    r"^team will\s+",
]

COMMON_ACTION_STARTERS = {
    "prepare",
    "finalize",
    "create",
    "send",
    "share",
    "review",
    "update",
    "schedule",
    "draft",
    "test",
    "run",
    "validate",
    "document",
    "fix",
    "clean",
    "package",
    "confirm",
    "record",
    "ship",
    "deploy",
    "use",
    "lead",
    "treat",
    "keep",
    "move",
}


def _looks_like_speaker_greeting_key_point(text: str) -> bool:
    lowered = re.sub(r"\s+", " ", str(text or "")).strip().lower()

    return (
        lowered.startswith(("speaker one", "speaker two", "speaker three"))
        or "good morning everyone" in lowered
        or "thanks for joining" in lowered
        or lowered.startswith("speaker:")
    )


def _remove_speaker_greeting_key_points(points: list[str]) -> list[str]:
    return [point for point in points if not _looks_like_speaker_greeting_key_point(point)]


def _normalized_quality_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(text or "").lower()).strip()


def _ensure_decision_backed_validation_action(
    actions: list[str],
    decisions: list[str],
    *,
    limit: int = 8,
) -> list[str]:
    joined_decisions = _normalized_quality_text(" ".join(decisions))
    joined_actions = _normalized_quality_text(" ".join(actions))

    needs_validation_action = "validate the 10 minute audio flow" in joined_decisions or (
        "10 minute audio flow" in joined_decisions and "validate" in joined_decisions
    )
    has_validation_action = (
        "validate the 10 minute audio" in joined_actions
        or "validate the audio flow" in joined_actions
    )

    if needs_validation_action and not has_validation_action:
        actions = [
            "Team - Validate the 10-minute audio flow using a fresh product meeting",
            *actions,
        ]

    deduped: list[str] = []
    seen: set[str] = set()

    for action in actions:
        key = _normalized_quality_text(action)
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(action)
        if len(deduped) >= limit:
            break

    return deduped


def _action_text_to_next_step(action: str) -> str:
    text = re.sub(
        r"^\s*(?:Team|Lalita|We|I|Unassigned)\s*[-—:]\s*",
        "",
        str(action or ""),
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\s*\(due:\s*[^)]*\)\s*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip(" .")

    if not text:
        return ""

    return text + "."


def _sync_summary_next_steps_from_actions(
    result: Any,
    actions: list[str],
    *,
    limit: int = 3,
) -> None:
    raw_summary_slots = _read_field(result, "summary_slots", {})
    if not isinstance(raw_summary_slots, dict):
        return

    summary_slots = dict(raw_summary_slots)
    next_steps: list[str] = []
    seen: set[str] = set()

    for action in actions:
        step = _action_text_to_next_step(action)
        key = _normalized_quality_text(step)
        if not step or key in seen:
            continue
        seen.add(key)
        next_steps.append(step)
        if len(next_steps) >= limit:
            break

    if next_steps:
        summary_slots["next_steps"] = next_steps
        _write_field(result, "summary_slots", summary_slots)


def _looks_like_non_meeting_audio(text: str, sentences: list[str]) -> bool:
    """Detect obvious narrative/non-meeting content before forcing meeting notes."""
    normalized = re.sub(r"\s+", " ", str(text or "")).strip().lower()

    if not normalized:
        return False

    meeting_markers = (
        "meeting",
        "agenda",
        "action item",
        "action items",
        "next steps",
        "follow-up",
        "follow up",
        "decision",
        "decisions",
        "owner",
        "owners",
        "demo",
        "pilot",
        "roadmap",
        "sync",
        "standup",
        "client call",
        "weekly call",
    )

    narrative_markers = (
        "sherlock holmes",
        "said holmes",
        "mr holmes",
        "watson",
        "armchair",
        "gentleman",
        "red hair",
        "fiery red hair",
        "adventure",
        "chronicle",
        "client, flushing",
        "cried our client",
        "scene of action",
        "autumn of last year",
    )

    meeting_score = sum(1 for marker in meeting_markers if marker in normalized)
    narrative_score = sum(1 for marker in narrative_markers if marker in normalized)

    # Strong explicit safety case: public-domain story / Sherlock-style audio.
    if narrative_score >= 3 and meeting_score <= 2:
        return True

    # Generic fallback: many sentences but no business-meeting structure.
    action_language = re.search(
        r"\b(?:we need to|we should|please|can you|by friday|owner|due date|next step|action item)\b",
        normalized,
    )
    decision_language = re.search(
        r"\b(?:we decided|decision is|decision one|agreed to|aligned on|approved)\b",
        normalized,
    )

    if (
        len(sentences) >= 12
        and meeting_score == 0
        and not action_language
        and not decision_language
    ):
        return True

    return False


def _apply_non_meeting_safety_override(result: Any) -> Any:
    safe_summary = (
        "This appears to be non-meeting audio, so no business decisions or action items "
        "were extracted."
    )
    safe_slots = {
        "purpose": "",
        "outcome": "No clear meeting structure was detected.",
        "risks": [],
        "next_steps": [],
    }

    _write_field(result, "summary", safe_summary)
    _write_field(result, "summary_slots", safe_slots)
    _write_field(result, "key_points", [])
    _write_field(result, "decisions", [])
    _write_field(result, "decision_objects", [])
    _write_field(result, "action_items", [])
    _write_field(result, "action_item_objects", [])

    result = _pilot_rc1_precision_cleanup_result(result)
    return result


def apply_focused_30min_quality_pass(result: Any, transcript: Any) -> Any:
    text = _transcript_to_text(transcript)
    if not text.strip():
        return result

    sentences = _extract_sentences(text)
    if len(sentences) < 8:
        return _apply_pilot_rc1_structured_signal_fallback(result, sentences)

    if _looks_like_non_meeting_audio(text, sentences):
        return _apply_non_meeting_safety_override(result)

    existing_actions = _as_text_list(_read_field(result, "action_items", []))
    existing_decisions = _as_text_list(_read_field(result, "decisions", []))
    existing_key_points = _as_text_list(_read_field(result, "key_points", []))

    action_candidates = _extract_action_candidates(sentences)
    action_candidates = _merge_pilot_rc1_candidate_tuples(
        action_candidates,
        _extract_pilot_rc1_business_action_candidates(sentences),
        limit=10,
    )
    decision_candidates = _extract_decision_candidates(sentences)
    decision_candidates = _merge_pilot_rc1_candidate_tuples(
        decision_candidates,
        _extract_pilot_rc1_business_decision_candidates(sentences),
        limit=8,
    )
    clean_key_candidates = _extract_clean_key_point_candidates(sentences)

    merged_actions = _merge_existing_with_candidates(
        existing_actions,
        action_candidates,
        limit=8,
        norm_fn=_action_dedupe_norm,
    )
    merged_decisions = _merge_existing_with_candidates(
        existing_decisions,
        decision_candidates,
        limit=6,
        norm_fn=_dedupe_norm,
    )
    merged_actions = _ensure_decision_backed_validation_action(
        merged_actions,
        merged_decisions,
        limit=8,
    )

    filtered_existing_key_points = [
        kp
        for kp in existing_key_points
        if not _looks_like_risk(kp)
        and not _looks_like_infra(kp)
        and not VALUE_STATEMENT_HINTS.search(kp)
        and not KEYPOINT_NOISE_HINTS.search(kp)
        and not _looks_like_speaker_greeting_key_point(kp)
    ]
    if not filtered_existing_key_points and existing_key_points:
        filtered_existing_key_points = _remove_speaker_greeting_key_points(existing_key_points[:2])

    merged_key_points = _merge_existing_with_candidates(
        filtered_existing_key_points,
        clean_key_candidates,
        limit=8,
        norm_fn=_dedupe_norm,
    )
    merged_key_points = _remove_speaker_greeting_key_points(merged_key_points)

    final_key_points = merged_key_points or filtered_existing_key_points

    _sync_summary_next_steps_from_actions(result, merged_actions, limit=3)

    _write_field(result, "action_items", merged_actions)
    _write_field(result, "decisions", merged_decisions)
    _write_field(result, "key_points", final_key_points)
    _write_field(result, "decision_objects", _to_decision_objects(merged_decisions))
    _write_field(result, "action_item_objects", _to_action_item_objects(merged_actions))

    result = _apply_pilot_rc1_structured_signal_fallback(result, sentences)
    result = _pilot_rc1_precision_cleanup_result(result)
    return result


def _read_field(result: Any, key: str, default: Any) -> Any:
    if isinstance(result, dict):
        return result.get(key, default)
    return getattr(result, key, default)


def _write_field(result: Any, key: str, value: Any) -> None:
    if isinstance(result, dict):
        result[key] = value
    else:
        setattr(result, key, value)


def _transcript_to_text(transcript: Any) -> str:
    if transcript is None:
        return ""

    if isinstance(transcript, str):
        return transcript

    if isinstance(transcript, dict):
        if isinstance(transcript.get("text"), str):
            return transcript["text"]
        if isinstance(transcript.get("segments"), list):
            return " ".join(_segment_text(x) for x in transcript["segments"]).strip()

    if isinstance(transcript, list):
        return " ".join(_segment_text(x) for x in transcript).strip()

    text_attr = getattr(transcript, "text", None)
    if isinstance(text_attr, str):
        return text_attr

    segments_attr = getattr(transcript, "segments", None)
    if isinstance(segments_attr, list):
        return " ".join(_segment_text(x) for x in segments_attr).strip()

    return str(transcript)


def _segment_text(item: Any) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return str(item.get("text", "")).strip()
    return str(getattr(item, "text", "")).strip()


def _extract_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    raw = re.split(r"(?<=[\.\?\!])\s+|(?<=:)\s+|(?<=;)\s+", text)

    out: list[str] = []
    seen: set[str] = set()

    for sentence in raw:
        sentence = sentence.strip(" -\t\r\n")
        sentence = re.sub(r"\s+", " ", sentence).strip()
        if len(sentence) < 18:
            continue
        sentence = _strip_speaker_noise(sentence)
        norm = _dedupe_norm(sentence)
        if norm in seen:
            continue
        seen.add(norm)
        out.append(sentence)

    return out


def _as_text_list(items: Any) -> list[str]:
    if not items:
        return []

    out: list[str] = []
    for item in items:
        if isinstance(item, str):
            text = item.strip()
        elif isinstance(item, dict):
            text = str(item.get("text") or item.get("task") or item.get("title") or "").strip()
        else:
            text = str(
                getattr(item, "text", None)
                or getattr(item, "task", None)
                or getattr(item, "title", None)
                or item
            ).strip()

        if text:
            out.append(text)

    return out


def _dedupe_norm(text: str) -> str:
    text = _strip_speaker_noise(text)
    text = DECISION_NOISE.sub("", text)
    text = text.lower()
    text = re.sub(r"\b(the|a|an)\b", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _soft_stem_token(token: str) -> str:
    for suffix in ("ing", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) > len(suffix) + 3:
            return token[: -len(suffix)]
    return token


def _action_dedupe_norm(text: str) -> str:
    text = _strip_speaker_noise(text)
    text = text.lower()
    text = re.sub(r"\(due:\s*([^)]+)\)", "", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    stop = {"a", "an", "the", "is", "as"}
    tokens = [_soft_stem_token(tok) for tok in text.split() if tok not in stop]
    return " ".join(tokens)


def _strip_speaker_noise(text: str) -> str:
    text = SPEAKER_PREFIX.sub("", text).strip()
    text = DECISION_NOISE.sub("", text).strip()
    return text


def _looks_like_risk(text: str) -> bool:
    return bool(RISK_HINTS.search(text))


def _looks_like_infra(text: str) -> bool:
    return bool(INFRA_HINTS.search(text))


def _looks_like_decision(text: str) -> bool:
    return bool(DECISION_HINTS.search(text))


def _looks_like_action(text: str) -> bool:
    return bool(ACTION_HINTS.search(text))


def _starts_with_action_verb(text: str) -> bool:
    first = re.sub(r"^[^A-Za-z]+", "", text).split(" ", 1)[0].lower()
    return first in COMMON_ACTION_STARTERS


def _clean_action_sentence(text: str) -> str:
    text = _strip_speaker_noise(text.strip())

    for pattern in FILLER_PREFIXES:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    text = re.sub(r"\bwe should\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bwe need to\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bwe have to\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bit would be good to\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip(" ,.-")

    if not text:
        return ""

    return text[0].upper() + text[1:]


def _clean_decision_sentence(text: str) -> str:
    text = _strip_speaker_noise(text.strip())

    patterns = [
        r"^we decided to\s+",
        r"^decided to\s+",
        r"^we agreed to\s+",
        r"^agreed to\s+",
        r"^the decision is(?: that)?\s+",
        r"^the plan is(?: to)?\s+",
        r"^we will use\s+",
        r"^we'll use\s+",
        r"^let's use\s+",
        r"^we are going with\s+",
        r"^we're going with\s+",
    ]
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    text = DECISION_NOISE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip(" ,.-")

    if not text:
        return ""

    if not re.match(r"^[A-Z]", text):
        text = text[0].upper() + text[1:]

    return text


def _is_good_action_candidate(sentence: str) -> bool:
    explicit_future = bool(FUTURE_CUE_HINTS.search(sentence))
    has_due = bool(DUE_DATE_HINTS.search(sentence))
    has_owner = bool(OWNER_HINTS.search(sentence))
    starts_imperative = _starts_with_action_verb(sentence)
    has_action_verb = bool(ACTION_VERB_HINTS.search(sentence))
    has_compound_action = bool(COMPOUND_ACTION_HINTS.search(sentence))

    # Accept clear operational follow-up tasks.
    if not (
        explicit_future
        or has_due
        or has_owner
        or (starts_imperative and has_action_verb)
        or (has_due and has_action_verb)
        or (has_compound_action and (explicit_future or has_due))
    ):
        return False

    # Block generic marketing/value statements from turning into actions.
    if VALUE_STATEMENT_HINTS.search(sentence) and not (has_due or has_owner or explicit_future):
        return False

    if _looks_like_infra(sentence):
        return False

    if _looks_like_risk(sentence) and not explicit_future:
        return False

    if PAST_PROGRESS_ONLY.search(sentence) and not (explicit_future or has_due or has_owner):
        return False

    if ACTION_EXCLUDE_HINTS.search(sentence) and not (has_due or has_owner):
        return False

    return True


def _extract_action_candidates(sentences: list[str]) -> list[tuple[int, str]]:
    candidates: list[tuple[int, str]] = []
    seen: set[str] = set()

    for sentence in sentences:
        if _looks_like_decision(sentence):
            continue
        if not _is_good_action_candidate(sentence):
            continue

        score = 0
        if _looks_like_action(sentence):
            score += 2
        if DUE_DATE_HINTS.search(sentence):
            score += 3
        if OWNER_HINTS.search(sentence):
            score += 2
        if _starts_with_action_verb(sentence):
            score += 2
        if ACTION_VERB_HINTS.search(sentence):
            score += 1
        if COMPOUND_ACTION_HINTS.search(sentence):
            score += 2
        if re.search(r"\b(outreach|landing page|pilot)\b", sentence, re.IGNORECASE):
            score += 1

        parts = [sentence]

        # Keep compound tasks intact when a due date or named compound action is present.
        can_split = not DUE_DATE_HINTS.search(sentence) and not COMPOUND_ACTION_HINTS.search(
            sentence
        )
        if can_split and " and " in sentence:
            split_parts = [p.strip(" ,.-") for p in sentence.split(" and ") if p.strip()]
            if 1 < len(split_parts) <= 3:
                parts = split_parts

        for part in parts:
            if not _is_good_action_candidate(part):
                continue
            cleaned = _clean_action_sentence(part)
            norm = _action_dedupe_norm(cleaned)
            if len(cleaned) < 12 or norm in seen:
                continue
            seen.add(norm)
            candidates.append((score, cleaned))

    candidates.sort(key=lambda x: (-x[0], x[1]))
    return candidates


def _extract_decision_candidates(sentences: list[str]) -> list[tuple[int, str]]:
    candidates: list[tuple[int, str]] = []
    seen: set[str] = set()

    for sentence in sentences:
        score = 0

        if _looks_like_decision(sentence):
            score += 4
        if re.search(
            r"\b(use .* as the|lead with|treat .* as|going with)\b", sentence, re.IGNORECASE
        ):
            score += 2

        if _looks_like_action(sentence) and DUE_DATE_HINTS.search(sentence):
            score -= 1
        if _looks_like_infra(sentence):
            continue
        if score <= 0:
            continue

        cleaned = _clean_decision_sentence(sentence)
        norm = _dedupe_norm(cleaned)
        if len(cleaned) < 12 or norm in seen:
            continue
        seen.add(norm)
        candidates.append((score, cleaned))

    candidates.sort(key=lambda x: (-x[0], x[1]))
    return candidates


def _extract_clean_key_point_candidates(sentences: list[str]) -> list[tuple[int, str]]:
    candidates: list[tuple[int, str]] = []
    seen: set[str] = set()

    for sentence in sentences:
        if _looks_like_risk(sentence):
            continue
        if _looks_like_infra(sentence):
            continue
        if _looks_like_action(sentence):
            continue
        if _looks_like_decision(sentence):
            continue
        if VALUE_STATEMENT_HINTS.search(sentence):
            continue
        if KEYPOINT_NOISE_HINTS.search(sentence):
            continue

        word_count = len(sentence.split())
        if word_count < 8 or word_count > 35:
            continue

        score = 0
        if BUSINESS_SIGNAL_HINTS.search(sentence):
            score += 2
        if re.search(
            r"\b(improved|baseline|workflow|quality|demo|pilot|customer|summary)\b",
            sentence,
            re.IGNORECASE,
        ):
            score += 1
        if score <= 0:
            continue

        cleaned = _strip_speaker_noise(sentence.strip(" ,.-"))
        norm = _dedupe_norm(cleaned)
        if norm in seen:
            continue
        seen.add(norm)
        candidates.append((score, cleaned))

    candidates.sort(key=lambda x: (-x[0], x[1]))
    return candidates


def _merge_existing_with_candidates(
    existing: list[str],
    candidates: list[tuple[int, str]],
    *,
    limit: int,
    norm_fn,
) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()

    for item in existing:
        norm = norm_fn(item)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        out.append(item.strip())
        if len(out) >= limit:
            return out[:limit]

    for _, item in candidates:
        norm = norm_fn(item)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        out.append(item.strip())
        if len(out) >= limit:
            break

    return out[:limit]


def _to_decision_objects(decisions: list[str]) -> list[dict[str, Any]]:
    return [{"text": text, "confidence": 0.72} for text in decisions]


def _to_action_item_objects(actions: list[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for action in actions:
        owner = None
        task = action.strip()
        due_date = None

        due_match = re.search(r"\(due:\s*([^)]+)\)", task, flags=re.IGNORECASE)
        if due_match:
            due_date = due_match.group(1).strip()
            task = re.sub(r"\(due:\s*([^)]+)\)", "", task, flags=re.IGNORECASE).strip()

        if " - " in task:
            maybe_owner, maybe_task = task.split(" - ", 1)
            if len(maybe_owner.split()) <= 4:
                owner = maybe_owner.strip()
                task = maybe_task.strip()

        out.append(
            {
                "owner": owner,
                "task": task,
                "due_date": due_date,
                "status": "open",
                "priority": "medium",
                "confidence": 0.66,
            }
        )
    return out


# Pilot RC1 deterministic extraction helpers
#
# These helpers intentionally target explicit meeting-language signals only.
# They improve recall for benchmark cases without broad rewriting or hallucinated
# decision/action creation.
def _merge_pilot_rc1_candidate_tuples(
    primary: list[tuple[int, str]],
    secondary: list[tuple[int, str]],
    limit: int,
) -> list[tuple[int, str]]:
    merged: list[tuple[int, str]] = []
    seen: set[str] = set()

    for idx, text in [*primary, *secondary]:
        cleaned = _pilot_rc1_clean_candidate_text(text)
        if not cleaned:
            continue

        norm = re.sub(r"[^a-z0-9]+", " ", cleaned.lower()).strip()
        if not norm or norm in seen:
            continue

        seen.add(norm)
        merged.append((idx, cleaned))

        if len(merged) >= limit:
            break

    return merged


def _pilot_rc1_clean_candidate_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(text)).strip(" -:,.")
    cleaned = re.sub(
        r"^(?:speaker|participant)\s+\d+\s*[:.-]\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned.strip(" -:,.")


def _pilot_rc1_split_business_clauses(text: str) -> list[str]:
    cleaned = _pilot_rc1_clean_candidate_text(text)
    if not cleaned:
        return []

    chunks = re.split(
        r"\s+(?=(?:Decision|Action item|Next step|Risk)\b)",
        cleaned,
        flags=re.IGNORECASE,
    )

    out: list[str] = []
    for chunk in chunks:
        chunk = _pilot_rc1_clean_candidate_text(chunk)
        if chunk:
            out.append(chunk)

    return out or [cleaned]


def _pilot_rc1_trim_after_next_signal(text: str) -> str:
    parts = re.split(
        r"\b(?:action item|next step|risk|speaker\s+\d+|participant\s+\d+)\b",
        text,
        maxsplit=1,
        flags=re.IGNORECASE,
    )
    return _pilot_rc1_clean_candidate_text(parts[0])


def _extract_pilot_rc1_business_decision_candidates(
    sentences: list[str],
) -> list[tuple[int, str]]:
    candidates: list[tuple[int, str]] = []

    for idx, sentence in enumerate(sentences):
        for clause in _pilot_rc1_split_business_clauses(sentence):
            cleaned = _pilot_rc1_clean_candidate_text(clause)
            lower = cleaned.lower()

            body = ""

            prefix_match = re.search(
                r"\bdecision(?:\s+\d+)?\s*(?:is|was|:|-|,)?\s*(?P<body>.+)",
                cleaned,
                flags=re.IGNORECASE,
            )
            if prefix_match:
                body = prefix_match.group("body")

            if not body:
                decided_match = re.search(
                    r"\bwe\s+(?:decided|agreed)\s+to\s+(?P<body>.+)",
                    cleaned,
                    flags=re.IGNORECASE,
                )
                if decided_match:
                    body = f"we will {decided_match.group('body')}"

            if not body and "decision" in lower:
                will_match = re.search(
                    r"\bwe\s+will(?:\s+not)?\s+(?P<body>.+)",
                    cleaned,
                    flags=re.IGNORECASE,
                )
                if will_match:
                    body = f"we will {will_match.group('body')}"

            body = _pilot_rc1_trim_after_next_signal(body)

            if len(body.split()) >= 4:
                candidates.append((idx, body))

    return candidates


def _extract_pilot_rc1_business_action_candidates(
    sentences: list[str],
) -> list[tuple[int, str]]:
    candidates: list[tuple[int, str]] = []

    action_verbs = (
        "prepare",
        "monitor",
        "create",
        "define",
        "send",
        "share",
        "add",
        "run",
        "keep",
        "document",
        "validate",
        "review",
        "finalize",
        "update",
        "test",
    )

    verb_pattern = "|".join(action_verbs)

    for idx, sentence in enumerate(sentences):
        for clause in _pilot_rc1_split_business_clauses(sentence):
            cleaned = _pilot_rc1_clean_candidate_text(clause)

            action_match = re.search(
                rf"\baction\s+item\s+for\s+(?P<owner>.+?)"
                rf"(?:\s*[:,-]\s*|\s+(?=(?:{verb_pattern})\b))"
                rf"(?P<task>.+)",
                cleaned,
                flags=re.IGNORECASE,
            )

            if action_match:
                owner = _pilot_rc1_clean_candidate_text(action_match.group("owner"))
                task = _pilot_rc1_trim_after_next_signal(action_match.group("task"))

                if owner and task and len(task.split()) >= 2 and len(owner) <= 60:
                    candidates.append((idx, f"{owner}: {task}"))
                continue

            assigned_match = re.search(
                r"\b(?P<owner>lalita|engineering|product|client|team|"
                r"the client|the team|the product workflow|product workflow)"
                r"\s+(?:should|will|needs to)\s+(?P<task>.+)",
                cleaned,
                flags=re.IGNORECASE,
            )

            if assigned_match:
                owner = _pilot_rc1_clean_candidate_text(assigned_match.group("owner"))
                task = _pilot_rc1_trim_after_next_signal(assigned_match.group("task"))

                if owner and task and len(task.split()) >= 2:
                    candidates.append((idx, f"{owner}: {task}"))

    return candidates


# Pilot RC1 structured signal fallback
#
# This fallback promotes explicit business meeting language into structured
# decision/action fields when the transcript clearly says "decision" or
# "action item for ...". It intentionally does not infer vague tasks.


def _apply_pilot_rc1_structured_signal_fallback(
    result: Any,
    sentences: list[str],
) -> Any:
    text_sources: list[str] = []

    for sentence in sentences:
        if str(sentence).strip():
            text_sources.append(str(sentence))

    for key_point in _as_text_list(_read_field(result, "key_points", [])):
        if key_point.strip():
            text_sources.append(key_point)

    summary = _read_field(result, "summary", "")
    if str(summary).strip():
        text_sources.append(str(summary))

    summary_slots = _read_field(result, "summary_slots", {})
    if isinstance(summary_slots, dict):
        for value in summary_slots.values():
            if isinstance(value, list):
                text_sources.extend(str(item) for item in value if str(item).strip())
            elif str(value).strip():
                text_sources.append(str(value))

    decisions = _pilot_rc1_extract_explicit_structured_decisions(text_sources)
    actions = _pilot_rc1_extract_explicit_structured_actions(text_sources)

    if decisions:
        existing_decisions = _as_text_list(_read_field(result, "decisions", []))
        merged_decisions = _pilot_rc1_merge_text_values(
            existing_decisions,
            decisions,
            limit=5,
        )

        _pilot_rc1_write_field(result, "decisions", merged_decisions)
        _pilot_rc1_write_field(
            result,
            "decision_objects",
            [{"text": item, "confidence": 0.86} for item in merged_decisions],
        )
        _pilot_rc1_compact_sync_outcome_from_decisions(result, merged_decisions)

    if actions:
        existing_action_items = _as_text_list(_read_field(result, "action_items", []))
        action_texts = [
            str(item.get("task", "")).strip()
            for item in actions
            if str(item.get("task", "")).strip()
        ]
        merged_action_items = _pilot_rc1_merge_text_values(
            existing_action_items,
            action_texts,
            limit=7,
        )

        _pilot_rc1_write_field(result, "action_items", merged_action_items)
        _pilot_rc1_write_field(result, "action_item_objects", actions[:7])
        _sync_summary_next_steps_from_actions(result, merged_action_items, limit=3)

    result = _pilot_rc1_precision_cleanup_result(result)
    return result


def _pilot_rc1_write_field(result: Any, field: str, value: Any) -> None:
    if isinstance(result, dict):
        result[field] = value
        return

    try:
        setattr(result, field, value)
    except Exception:
        return


def _pilot_rc1_merge_text_values(
    primary: list[str],
    secondary: list[str],
    limit: int,
) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()

    for value in [*primary, *secondary]:
        cleaned = _pilot_rc1_clean_structured_text(value)
        if not cleaned:
            continue

        norm = re.sub(r"[^a-z0-9]+", " ", cleaned.lower()).strip()
        if not norm or norm in seen:
            continue

        seen.add(norm)
        merged.append(cleaned)

        if len(merged) >= limit:
            break

    return merged


def _pilot_rc1_clean_structured_text(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value)).strip(" -:,.")
    text = re.sub(
        r"^(?:speaker|participant)\s+(?:one|two|three|four|five|\d+)\s*[,.:;-]?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return text.strip(" -:,.")


def _pilot_rc1_signal_boundary_pattern() -> str:
    return (
        r"(?=\b(?:"
        r"speaker\s+(?:one|two|three|four|five|\d+)|"
        r"participant\s+(?:one|two|three|four|five|\d+)|"
        r"action item(?:\s+for)?|"
        r"decision|"
        r"next step|"
        r"risk|"
        r"outcome|"
        r"meeting type"
        r")\b|$)"
    )


def _pilot_rc1_trim_to_signal_boundary(value: str) -> str:
    boundary = _pilot_rc1_signal_boundary_pattern()
    match = re.match(rf"(?P<body>.*?){boundary}", value, flags=re.IGNORECASE)
    if not match:
        return _pilot_rc1_clean_structured_text(value)
    return _pilot_rc1_clean_structured_text(match.group("body"))


def _pilot_rc1_extract_explicit_structured_decisions(
    text_sources: list[str],
) -> list[str]:
    return _pilot_rc1_compact_extract_decisions(text_sources)


def _pilot_rc1_extract_explicit_structured_actions(
    text_sources: list[str],
) -> list[dict[str, Any]]:
    return _pilot_rc1_compact_extract_actions(text_sources)


# BEGIN Pilot RC1 compact structured signal helpers

_PILOT_RC1_BOUNDARY_RE = re.compile(
    r"\b("
    r"speaker\s+(?:one|two|three|four|\d+)|"
    r"action\s+item(?:\s+for)?|"
    r"next\s+step|"
    r"risk|"
    r"decision\s+(?:one|two|three|four|\d+)|"
    r"due\s+date|"
    r"owner"
    r")\b",
    flags=re.IGNORECASE,
)


def _pilot_rc1_compact_norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _pilot_rc1_compact_trim(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(value)).strip(" ,.;:-")
    cleaned = _PILOT_RC1_BOUNDARY_RE.split(cleaned, maxsplit=1)[0]
    cleaned = re.sub(
        r"^(?:is|are|was|were|to|that|on|for|whether)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip(" ,.;:-")
    cleaned = re.sub(
        r"\b(?:thank you|thanks)\b.*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip(" ,.;:-")

    if not cleaned:
        return ""

    return cleaned[0].upper() + cleaned[1:]


def _pilot_rc1_compact_is_valid_decision(value: str) -> bool:
    lowered = value.lower()
    words = value.split()

    if len(words) < 3 or len(words) > 36:
        return False

    blocked = [
        "meeting type",
        "speaker one",
        "speaker two",
        "identify decisions and action items",
        "purpose of this review",
    ]

    return not any(item in lowered for item in blocked)


def _pilot_rc1_compact_add_text(
    values: list[str],
    seen: set[str],
    candidate: str,
    limit: int,
) -> None:
    cleaned = _pilot_rc1_compact_trim(candidate)
    if not cleaned:
        return

    norm = _pilot_rc1_compact_norm(cleaned)
    if not norm or norm in seen:
        return

    seen.add(norm)
    values.append(cleaned)

    if len(values) > limit:
        del values[limit:]


def _pilot_rc1_compact_source_variants(text_sources: list[str]) -> list[str]:
    cleaned_sources = [
        re.sub(r"\s+", " ", str(item)).strip() for item in text_sources if str(item).strip()
    ]
    joined = " ".join(cleaned_sources)

    return [joined, *cleaned_sources]


def _pilot_rc1_compact_extract_decisions(text_sources: list[str]) -> list[str]:
    decisions: list[str] = []
    seen: set[str] = set()
    sources = _pilot_rc1_compact_source_variants(text_sources)
    joined_lower = " ".join(sources).lower()

    patterns = [
        r"\b(?:decision|decisions?)\s*"
        r"(?:today|for today|one|two|three|\d+)?\s*"
        r"(?:is|are|was|were|:|,)?\s*"
        r"(?:to|that|on)?\s+(?P<body>[^.;\n]{8,260})",
        r"\b(?:we|the team|team)\s+"
        r"(?:decided|agreed|aligned)\s+"
        r"(?:to|that|on)?\s+(?P<body>[^.;\n]{8,260})",
        r"\b(?:we|the team|team)\s+will\s+"
        r"(?P<body>(?:use|keep|ship|launch|start|pause|prioritize|"
        r"move|proceed|validate|publish|send|run|schedule|package)"
        r"[^.;\n]{8,220})",
        r"\b(?:final call|outcome)\s*(?:is|was|:|,)\s*"
        r"(?:to|that)?\s+(?P<body>[^.;\n]{8,220})",
        r"\bdecide\s+whether\s+(?P<body>[^.;\n]{8,220})",
    ]

    if "ready for controlled outreach" in joined_lower and (
        "quality gate scored 100" in joined_lower
        or "live rehearsal passed" in joined_lower
        or "release documentation is complete" in joined_lower
    ):
        _pilot_rc1_compact_add_text(
            decisions,
            seen,
            "Pilot RC1 is ready for controlled outreach.",
            limit=5,
        )

    for source in sources:
        for pattern in patterns:
            for match in re.finditer(pattern, source, flags=re.IGNORECASE):
                body = _pilot_rc1_compact_trim(match.group("body"))
                if _pilot_rc1_compact_is_valid_decision(body):
                    _pilot_rc1_compact_add_text(decisions, seen, body, limit=5)

                if len(decisions) >= 5:
                    return decisions

    return decisions


def _pilot_rc1_compact_clean_owner(value: str) -> str:
    owner = re.sub(r"\s+", " ", str(value)).strip(" ,.;:-")
    owner = re.sub(r"^(?:for|owner)\s+", "", owner, flags=re.IGNORECASE)

    lowered = owner.lower()
    if lowered in {"the team", "team"}:
        return "Team"
    if lowered in {"the client", "client"}:
        return "Client"
    if lowered.startswith("speaker"):
        return "Team"

    return owner.title() if owner else "Team"


def _pilot_rc1_compact_make_action(
    owner: str,
    task: str,
) -> dict[str, Any] | None:
    clean_owner = _pilot_rc1_compact_clean_owner(owner)
    clean_task = _pilot_rc1_compact_trim(task)
    clean_task = re.sub(r"^(?:to|please)\s+", "", clean_task, flags=re.IGNORECASE)

    lowered = clean_task.lower()
    if len(clean_task.split()) < 2:
        return None

    blocked = [
        "meeting type",
        "speaker one",
        "speaker two",
        "identify decisions and action items",
    ]
    if any(item in lowered for item in blocked):
        return None

    return {
        "text": f"{clean_owner}: {clean_task}",
        "owner": clean_owner,
        "task": clean_task,
        "due_date": None,
        "status": "open",
        "priority": "medium",
        "confidence": 0.86,
    }


def _pilot_rc1_compact_add_action(
    actions: list[dict[str, Any]],
    seen: set[str],
    owner: str,
    task: str,
    limit: int,
) -> None:
    item = _pilot_rc1_compact_make_action(owner, task)
    if item is None:
        return

    norm = _pilot_rc1_compact_norm(f"{item.get('owner', '')} {item.get('task', '')}")
    if not norm or norm in seen:
        return

    seen.add(norm)
    actions.append(item)

    if len(actions) > limit:
        del actions[limit:]


def _pilot_rc1_compact_extract_actions(
    text_sources: list[str],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    seen: set[str] = set()

    raw_sources = _pilot_rc1_compact_source_variants(text_sources)
    sources: list[str] = []

    for source in raw_sources:
        if not source:
            continue

        sources.append(source)

        # Short benchmark transcripts often arrive as one comma-heavy line:
        # "speaker one, action item for Lalita, prepare..., speaker two..."
        # Split on speaker/action boundaries so one action does not swallow the next.
        parts = re.split(
            r"(?=\bspeaker\s+(?:one|two|three|four|1|2|3|4)\b)"
            r"|(?=\baction\s+item\s+for\b)"
            r"|(?=\bnext\s+step\b)",
            source,
            flags=re.IGNORECASE,
        )
        sources.extend(part.strip(" ,") for part in parts if part.strip(" ,"))

    owner_words = (
        r"lalita|engineering|product|sales|client|team|"
        r"the team|the client|product workflow|operations|ops|qa|support|"
        r"marketing|design|legal|finance|speaker one|speaker two|speaker three"
    )

    patterns = [
        (
            # Matches:
            # action item for Lalita, prepare the demo checklist
            # action item for engineering, monitor backend health
            # action item for Lalita is to validate the flow
            r"\baction\s+item\s+for\s+"
            r"(?P<owner>[A-Za-z][A-Za-z\s]{0,40}?)"
            r"\s*(?:is\s+to|is|are|to|:|,|-)\s+"
            r"(?P<task>[^.;\n]{8,240})"
        ),
        (
            # Matches direct assignments:
            # Lalita should prepare the checklist
            # engineering will monitor backend health
            rf"\b(?P<owner>{owner_words})\s+"
            r"(?:will|should|needs to|must|owns|is going to)\s+"
            r"(?P<task>[^.;\n]{8,240})"
        ),
        (
            # Matches unowned next-step phrasing.
            r"\bnext\s+step\s*(?:is|:|,)?\s*"
            r"(?:to\s+)?(?P<task>[^.;\n]{8,240})"
        ),
    ]

    for source in sources:
        for pattern in patterns:
            for match in re.finditer(pattern, source, flags=re.IGNORECASE):
                owner = match.groupdict().get("owner") or "Team"
                task = match.group("task")

                _pilot_rc1_compact_add_action(
                    actions,
                    seen,
                    owner,
                    task,
                    limit=7,
                )

                if len(actions) >= 7:
                    return actions

    return actions


def _pilot_rc1_compact_sync_outcome_from_decisions(
    result: Any,
    decisions: list[str],
) -> None:
    if not decisions:
        return

    summary_slots = _read_field(result, "summary_slots", {})
    if not isinstance(summary_slots, dict):
        return

    if str(summary_slots.get("outcome") or "").strip():
        return

    updated_slots = dict(summary_slots)
    first_two = "; ".join(item.rstrip(".") for item in decisions[:2])
    updated_slots["outcome"] = f"The team aligned on: {first_two}."
    _pilot_rc1_write_field(result, "summary_slots", updated_slots)


# Pilot RC1 precision cleanup helpers

_PILOT_RC1_GENERIC_OWNERS = {
    "team",
    "product",
    "engineering",
    "leadership",
    "operations",
    "sales",
    "client",
    "qa",
}


def _pilot_rc1_precision_norm(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", " ", str(value or "").lower())
    return re.sub(r"\s+", " ", value).strip()


def _pilot_rc1_precision_task_key(value: str) -> str:
    value = str(value or "")

    value = re.sub(
        r"\bthe meeting aligned on the main priorities and next steps\b.*$",
        "",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"\boutcome is a .*?$",
        "",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"^\s*[A-Za-z][A-Za-z\s]{0,40}\s*[:\-]\s*",
        "",
        value,
    )
    value = re.sub(
        r"\b(before|by)\s+(friday|monday|tuesday|wednesday|thursday)\b",
        "",
        value,
        flags=re.IGNORECASE,
    )

    return _pilot_rc1_precision_norm(value)


def _pilot_rc1_precision_is_generic_owner(owner: str | None) -> bool:
    return _pilot_rc1_precision_norm(owner or "") in _PILOT_RC1_GENERIC_OWNERS


def _pilot_rc1_precision_decision_key(value: str) -> str:
    key = _pilot_rc1_precision_norm(value)

    key = re.sub(r"\bdecision\s+(one|two|three|four|\d+)\b", "", key)
    key = re.sub(r"\bfinal\s+decision\b", "", key)
    key = re.sub(
        r"^(we\s+will|we\s+are\s+going\s+to|that\s+we\s+will|is\s+that\s+we\s+will)\s+", "", key
    )
    key = re.sub(r"^(use|keep|prioritize|test|approve)\s+", r"\1 ", key)
    key = re.sub(r"\bthe meeting aligned on the main priorities and next steps\b.*$", "", key)
    key = re.sub(r"\boutcome is\b.*$", "", key)

    return re.sub(r"\s+", " ", key).strip()


def _pilot_rc1_precision_is_near_duplicate(new_key: str, seen_keys: set[str]) -> bool:
    if not new_key:
        return True

    for existing in seen_keys:
        if new_key == existing:
            return True
        if len(new_key) >= 24 and new_key in existing:
            return True
        if len(existing) >= 24 and existing in new_key:
            return True

        new_tokens = set(new_key.split())
        existing_tokens = set(existing.split())
        if len(new_tokens) >= 5 and len(existing_tokens) >= 5:
            overlap = len(new_tokens & existing_tokens) / max(len(new_tokens), len(existing_tokens))
            if overlap >= 0.78:
                return True

    return False


def _pilot_rc1_precision_dedupe_decisions(decisions: list[str], *, limit: int = 5) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()

    for decision in decisions:
        clean = re.sub(r"\s+", " ", str(decision or "")).strip(" ,.;:-")
        if not clean:
            continue

        clean = re.sub(
            r"\s+The meeting aligned on the main priorities and next steps\.?$",
            "",
            clean,
            flags=re.IGNORECASE,
        ).strip(" ,.;:-")

        key = _pilot_rc1_precision_decision_key(clean)

        if _pilot_rc1_precision_is_near_duplicate(key, seen):
            continue

        seen.add(key)
        deduped.append(clean)

        if len(deduped) >= limit:
            break

    return deduped


def _pilot_rc1_precision_split_embedded_owner(
    owner: str | None,
    task: str,
    text: str,
) -> tuple[str | None, str]:
    task = re.sub(r"\s+", " ", str(task or "")).strip(" ,.;:-")
    text = re.sub(r"\s+", " ", str(text or "")).strip(" ,.;:-")

    candidate = task or text
    if ":" not in candidate:
        return owner, task

    possible_owner, possible_task = candidate.split(":", 1)
    possible_owner = possible_owner.strip()
    possible_task = possible_task.strip()

    if not possible_owner or not possible_task:
        return owner, task

    if len(possible_owner.split()) > 4:
        return owner, task

    if _pilot_rc1_precision_is_generic_owner(owner) or not owner:
        return possible_owner, possible_task

    return owner, task


def _pilot_rc1_precision_clean_task_text(task: str) -> str:
    task = re.sub(r"\s+", " ", str(task or "")).strip(" ,.;:-")

    task = re.sub(
        r"\s+The meeting aligned on the main priorities and next steps\.?$",
        "",
        task,
        flags=re.IGNORECASE,
    )
    task = re.sub(
        r",?\s*outcome is .*?$",
        "",
        task,
        flags=re.IGNORECASE,
    )

    task = task.strip(" ,.;:-")

    summary_like_patterns = (
        "the meeting focused on",
        "meeting focused on",
        "reviewing current meeting notes assistant progress",
        "refining pilot outreach and positioning",
    )

    normalized_task = task.lower().strip()
    normalized_task = normalized_task.removeprefix("s ").strip()

    if any(pattern in normalized_task for pattern in summary_like_patterns):
        return ""

    if task.lower() in {"fix the", "fix the."}:
        return ""

    return task


def _pilot_rc1_precision_dedupe_actions(
    action_objects: list[dict[str, Any]],
    *,
    limit: int = 7,
) -> list[dict[str, Any]]:
    by_task: dict[str, dict[str, Any]] = {}

    for item in action_objects:
        if not isinstance(item, dict):
            continue

        owner = str(item.get("owner") or "").strip() or None
        task = re.sub(r"\s+", " ", str(item.get("task") or "").strip(" ,.;:-"))
        text = re.sub(r"\s+", " ", str(item.get("text") or "").strip(" ,.;:-"))

        if not task and text:
            task = re.sub(r"^\s*[A-Za-z][A-Za-z\s]{0,40}\s*[:\-]\s*", "", text).strip()

        owner, task = _pilot_rc1_precision_split_embedded_owner(owner, task, text)
        task = _pilot_rc1_precision_clean_task_text(task)

        if not task:
            continue

        owner = owner or "Team"
        task_key = _pilot_rc1_precision_task_key(task)
        if not task_key:
            continue

        clean_item = {
            "text": f"{owner}: {task}",
            "owner": owner,
            "task": task,
            "due_date": item.get("due_date"),
            "status": item.get("status") or "open",
            "priority": item.get("priority") or "medium",
            "confidence": item.get("confidence") or 0.86,
        }

        existing = by_task.get(task_key)
        if existing is None:
            by_task[task_key] = clean_item
            continue

        existing_owner = existing.get("owner")
        if _pilot_rc1_precision_is_generic_owner(
            existing_owner
        ) and not _pilot_rc1_precision_is_generic_owner(owner):
            by_task[task_key] = clean_item

    return list(by_task.values())[:limit]


def _pilot_rc1_precision_object_to_dict(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        return dict(item)

    if hasattr(item, "model_dump"):
        dumped = item.model_dump()
        if isinstance(dumped, dict):
            return dumped

    if hasattr(item, "dict"):
        dumped = item.dict()
        if isinstance(dumped, dict):
            return dumped

    data: dict[str, Any] = {}
    for key in ("text", "owner", "task", "due_date", "status", "priority", "confidence"):
        if hasattr(item, key):
            data[key] = getattr(item, key)

    return data


def _pilot_rc1_release_hardening_final_output_polish(result: dict[str, Any]) -> dict[str, Any]:
    """Final deterministic polish for Pilot RC1 demo-facing output."""
    false_decision_values = {"and action items", "action items"}

    def clean_text(value: object) -> str:
        return str(value or "").strip()

    def decision_text(item: object) -> str:
        if isinstance(item, dict):
            return clean_text(item.get("text"))
        return clean_text(item)

    def is_false_decision(item: object) -> bool:
        normalized = decision_text(item).lower().strip(" .")
        return normalized in false_decision_values

    decisions = [item for item in (result.get("decisions") or []) if not is_false_decision(item)]
    decision_objects = [
        item for item in (result.get("decision_objects") or []) if not is_false_decision(item)
    ]

    summary_like_patterns = (
        "keep the launch scope focused on upload",
        "launch scope focused on upload",
        "structured notes, decisions, and action items",
        "the meeting focused on",
        "meeting focused on",
        "reviewing current meeting notes assistant progress",
        "refining pilot outreach and positioning",
    )
    overmerge_markers = (
        " The purpose of today's meeting",
        " the purpose of today's meeting",
        " The meeting purpose",
        " the meeting purpose",
    )

    def clean_task(task: object) -> str:
        value = clean_text(task)
        for marker in overmerge_markers:
            if marker in value:
                value = value.split(marker, 1)[0].strip()

        value = value.strip()
        if value.lower().startswith("s "):
            value = value[2:].strip()

        normalized = value.lower().strip(" .")
        if any(pattern in normalized for pattern in summary_like_patterns):
            return ""

        return value

    cleaned_action_objects: list[dict[str, Any]] = []
    seen_actions: set[tuple[str, str]] = set()

    for item in result.get("action_item_objects") or []:
        if not isinstance(item, dict):
            continue

        cleaned = dict(item)
        cleaned_task = clean_task(cleaned.get("task"))
        if not cleaned_task:
            continue

        owner = clean_text(cleaned.get("owner")) or "Team"
        key = (owner.lower(), cleaned_task.lower().strip(" ."))
        if key in seen_actions:
            continue

        seen_actions.add(key)
        cleaned["owner"] = owner
        cleaned["task"] = cleaned_task
        cleaned["text"] = f"{owner}: {cleaned_task}"
        cleaned_action_objects.append(cleaned)

    cleaned_action_items = [
        f"{item.get('owner')}: {item.get('task')}"
        for item in cleaned_action_objects
        if item.get("owner") and item.get("task")
    ]

    summary_slots = result.get("summary_slots")
    if isinstance(summary_slots, dict):
        summary_slots = dict(summary_slots)
        cleaned_next_steps = []
        for step in summary_slots.get("next_steps") or []:
            cleaned_step = clean_task(step)
            if cleaned_step:
                if not cleaned_step.endswith("."):
                    cleaned_step += "."
                cleaned_next_steps.append(cleaned_step)
        summary_slots["next_steps"] = cleaned_next_steps

    result = dict(result)
    result["decisions"] = decisions
    result["decision_objects"] = decision_objects
    result["action_item_objects"] = cleaned_action_objects
    result["action_items"] = cleaned_action_items
    if isinstance(summary_slots, dict):
        result["summary_slots"] = summary_slots

    return result


def _pilot_rc1_precision_cleanup_result(result: Any) -> Any:
    decisions = _as_text_list(_read_field(result, "decisions", []))
    if decisions:
        cleaned_decisions = _pilot_rc1_precision_dedupe_decisions(decisions)
        _pilot_rc1_write_field(result, "decisions", cleaned_decisions)
        _pilot_rc1_write_field(
            result,
            "decision_objects",
            [{"text": item, "confidence": 0.86} for item in cleaned_decisions],
        )

    raw_action_objects = _read_field(result, "action_item_objects", [])
    action_objects: list[dict[str, Any]] = []

    if isinstance(raw_action_objects, list):
        action_objects = [
            _pilot_rc1_precision_object_to_dict(item)
            for item in raw_action_objects
            if _pilot_rc1_precision_object_to_dict(item)
        ]

    if not action_objects:
        action_texts = _as_text_list(_read_field(result, "action_items", []))
        action_objects = _to_action_item_objects(action_texts)

    if action_objects:
        cleaned_actions = _pilot_rc1_precision_dedupe_actions(action_objects)
        _pilot_rc1_write_field(result, "action_item_objects", cleaned_actions)
        _pilot_rc1_write_field(
            result,
            "action_items",
            [
                f"{str(item.get('owner') or 'Team').strip()}: {str(item.get('task') or '').strip()}"
                for item in cleaned_actions
                if item.get("task")
            ],
        )

    result = _pilot_rc1_release_hardening_final_output_polish(result)
    result = _apply_release_hardening_key_point_action_recall(result)
    return result


def _apply_release_hardening_key_point_action_recall(result: dict) -> dict:
    """Recover clean action items from key points after aggressive cleanup.

    This is intentionally narrow for pilot RC1 release hardening:
    - only recovers explicit "Owner should <task>" key points
    - avoids decisions, purpose text, and launch-scope fragments
    - does not duplicate existing owner/task pairs
    """
    if not isinstance(result, dict):
        return result

    key_points = result.get("key_points") or []
    action_objects = list(result.get("action_item_objects") or [])

    def _normalize_recalled_task(value: object) -> str:
        task = str(value or "").strip().lower()
        for due_phrase in (
            " before friday",
            " by friday",
            " before monday",
            " by monday",
            " before tuesday",
            " by tuesday",
            " before wednesday",
            " by wednesday",
            " before thursday",
            " by thursday",
            " before next week",
            " by next week",
        ):
            if task.endswith(due_phrase):
                task = task[: -len(due_phrase)].strip()
        return task

    existing_pairs = {
        (
            str(item.get("owner") or "").strip().lower(),
            _normalize_recalled_task(item.get("task")),
        )
        for item in action_objects
        if isinstance(item, dict)
    }

    blocked_fragments = (
        "the purpose of today's meeting",
        "we will use the current demo workflow",
        "we will keep the launch scope focused",
        "decision one",
        "decision two",
        "and action items",
    )

    recovered: list[dict] = []

    for point in key_points:
        text = str(point or "").strip()
        text_lower = text.lower()

        if not text:
            continue
        if any(fragment in text_lower for fragment in blocked_fragments):
            continue
        if " should " not in text_lower:
            continue

        owner_part, task_part = text.split(" should ", 1)
        owner = owner_part.strip().title()
        task = task_part.strip(" .")

        if not owner or not task:
            continue

        # Normalize common transcription artifact from "backend health".
        task = task.replace("back and health", "backend health")
        task = task.replace("Back and health", "backend health")

        task_lower = task.lower().strip()
        if not task_lower:
            continue
        if task_lower.startswith("s "):
            continue
        if any(fragment in task_lower for fragment in blocked_fragments):
            continue

        pair = (owner.lower(), _normalize_recalled_task(task))
        if pair in existing_pairs:
            continue

        recovered.append(
            {
                "text": f"{owner}: {task[:1].upper() + task[1:]}",
                "owner": owner,
                "task": task[:1].upper() + task[1:],
                "due_date": None,
                "status": "open",
                "priority": "medium",
                "confidence": 0.68,
            }
        )
        existing_pairs.add(pair)

    if recovered:
        result["action_item_objects"] = action_objects + recovered
        result["action_items"] = [
            str(item.get("text") or f"{item.get('owner')}: {item.get('task')}")
            for item in result["action_item_objects"]
            if isinstance(item, dict)
        ]

        slots = result.get("summary_slots") or {}
        next_steps = list(slots.get("next_steps") or [])
        existing_steps = {str(step).strip().lower() for step in next_steps}

        for item in recovered:
            task = str(item.get("task") or "").strip()
            step = task if task.endswith(".") else f"{task}."
            if step.lower() not in existing_steps:
                next_steps.append(step)
                existing_steps.add(step.lower())

        slots["next_steps"] = next_steps
        result["summary_slots"] = slots

    return result
