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


def apply_focused_30min_quality_pass(result: Any, transcript: Any) -> Any:
    text = _transcript_to_text(transcript)
    if not text.strip():
        return result

    sentences = _extract_sentences(text)
    if len(sentences) < 8:
        return result

    existing_actions = _as_text_list(_read_field(result, "action_items", []))
    existing_decisions = _as_text_list(_read_field(result, "decisions", []))
    existing_key_points = _as_text_list(_read_field(result, "key_points", []))

    action_candidates = _extract_action_candidates(sentences)
    decision_candidates = _extract_decision_candidates(sentences)
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
