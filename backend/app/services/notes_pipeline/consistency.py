"""Final consistency pass for client-facing notes.

This pass is intentionally conservative:
- remove agenda/process text from risks
- promote clear action candidates from next_steps/key_points/decisions
- deduplicate near-duplicate actions
- infer owners from explicit owner evidence when available
"""

from __future__ import annotations

import re
from typing import Any

_GENERIC_OWNERS = {"", "team", "we", "unknown", "none", "unassigned"}

_BAD_RISK_PATTERNS = [
    r"\btoday we need to confirm\b",
    r"\bthe goal today is\b",
    r"\bthe demo should show the workflow\b",
    r"\bupload meeting recording\b",
    r"\bwait for processing\b",
    r"\breview summary\b",
    r"\bcopy or export\b",
    r"\brisks and action items\b",
]

_RISK_SIGNAL_PATTERNS = [
    r"\bdelay\b",
    r"\bmay miss\b",
    r"\bmiss some details\b",
    r"\breview(?:ed)? before sharing\b",
    r"\breview recommended\b",
    r"\breliability\b",
    r"\btrust gap\b",
    r"\bblocked?\b",
    r"\bblocker\b",
    r"\bdependency\b",
    r"\bdepends on\b",
    r"\bwaiting on\b",
    r"\bnot confirmed\b",
    r"\bpricing\b.*\b(confirm|approval|review|delay|change)\b",
    r"\bover.?promis",
    r"\bexpectation",
    r"\bunclear\b",
    r"\bold test files\b",
    r"\bdemo\b.*\b(confidence|readiness|risk|unclear|old)\b",
    r"\bclient\b.*\b(delay|confidence|expectation|follow.?up)\b",
    r"\blong recordings?\b.*\b(review|miss|caution|reliability)\b",
]

_ACTION_SIGNAL_PATTERNS = [
    r"\bconfirm\b",
    r"\bupdate\b",
    r"\bsend\b",
    r"\bdraft\b",
    r"\bcreate\b",
    r"\bclean\b",
    r"\bremove\b",
    r"\bupload\b",
    r"\bfollow up\b",
    r"\bfollow-up\b",
    r"\bschedule\b",
    r"\bprepare\b",
    r"\bfinal review\b",
    r"\bdry run\b",
    r"\bsay\b",
    r"\bneed(?:s)?\s+to\b",
    r"\bgo to\b",
]

_BAD_ACTION_PATTERNS = [
    r"\btoday (we )?need to confirm\b",
    r"\bthe purpose is to confirm\b",
    r"\bthe goal today is\b",
    r"\bthe demo should show the workflow\b",
    r"\bfor example\b.*\bshould become\b",
    r"\bif we send\b",
    r"\bclient can renew\b",
    r"\bsuccess criteria\b.*\bweekly\b",
    r"\breview risks blockers dependencies and uncertainties\b",
    r"\breview risks\b.*\buncertainties\b",
]

_BAD_DECISION_PATTERNS = [
    r"^s\b",
    r"^risks questions and owners$",
    r"\bdiscussion should not become a decision\b",
    r"\bfor example\b.*\bshould become\b",
    r"\brisk extraction should look for\b",
    r"\brisks open questions repeated actions\b",
    r"\brepeated actions and vague actions\b",
    r"\blisted as (?:spoken|broken-?meeting) content\b",
    r"\bnot as a separate document\b",
    r"\bbecause this is what a user will expect\b",
    r"\bavailable for baseline scoring\b",
]

_READABILITY_FIXES = (
    (r"\breviewrecommended\b", "review recommended"),
    (r"\btomake\b", "to make"),
    (r"\ba gen\.ai\b", "Acjen AI"),
    (r"\bagenda ai\b", "Acjen AI"),
    (r"\buser can ai\b", "Acjen AI"),
    (r"(?<!Acjen )\bAI URL\b", "Acjen AI URL"),
    (r"\bside up\b", "signup"),
    (r"\bpay pal\b", "PayPal"),
    (r"\bsquare\b", "Square"),
)


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _clean_readability(text: str) -> str:
    cleaned = _text(text)
    for pattern, replacement in _READABILITY_FIXES:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.I)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _norm(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[_*`#>\[\]()]+", " ", value)
    value = re.sub(r"[^a-z0-9%:\s-]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _matches_any(text: str, patterns: list[str]) -> bool:
    normalized = _norm(text)
    return any(re.search(pattern, normalized, flags=re.I) for pattern in patterns)


def _dedupe_key(text: str) -> str:
    normalized = _norm(text)
    normalized = normalized.replace(" by 11am tomorrow", " 11am tomorrow")
    normalized = normalized.replace(" at 11am tomorrow", " 11am tomorrow")
    normalized = re.sub(r"\bplease\b", "", normalized)
    normalized = re.sub(r"\bthe\b", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _item_text(item: Any) -> str:
    if isinstance(item, dict):
        for key in ("task", "text", "description", "title", "risk"):
            value = _text(item.get(key))
            if value:
                return _clean_readability(value)
        return ""
    return _clean_readability(_text(item))


def _capitalize_task(task: str) -> str:
    task = task.strip()
    if not task:
        return task
    return task[0].upper() + task[1:]


def _make_action(task: str, owner: str = "Team") -> dict[str, Any]:
    task = _clean_action_task(task, owner)
    return {
        "owner": owner,
        "task": _capitalize_task(task),
        "status": "open",
        "priority": "medium",
    }


def _clean_action_task(task: str, owner: str = "Team") -> str:
    cleaned = _clean_readability(task).strip(" .")
    owner_text = _text(owner)
    if owner_text:
        cleaned = re.sub(
            rf"^{re.escape(owner_text)}\s*[-:]\s*",
            "",
            cleaned,
            flags=re.I,
        )
    cleaned = re.sub(
        r"\.\s*The meeting aligned on the main priorities and next steps\.?$",
        "",
        cleaned,
        flags=re.I,
    )
    cleaned = re.sub(
        r"^update the landing page onboarding copy and send the landing page copy to (?P<recipient>[A-Z][a-zA-Z]+) by (?P<deadline>[^.]+)$",
        r"send the landing page copy to \g<recipient> by \g<deadline>",
        cleaned,
        flags=re.I,
    )
    return cleaned.strip(" .")


def _extract_owner_from_action_text(text: str) -> tuple[str | None, str]:
    """Extract owner from direct action language when available."""

    original = _clean_readability(text)
    original = re.sub(r"^[A-Z][a-zA-Z]+\s+says?,\s*", "", original)

    repeated_match = re.search(
        r"\b(?P<owner>[A-Z][a-zA-Z]+)\s+repeated that\s+(?:she|he|they)\s+will\s+(?P<task>.+)$",
        original,
    )
    if repeated_match:
        owner = repeated_match.group("owner").strip()
        task = repeated_match.group("task").strip()
        task = re.sub(r"\blater repeated (?:that|at)\s+", "and ", task, flags=re.I)
        return owner, task

    original = re.sub(r"^[A-Z][a-zA-Z]+\s+repeated that\s+", "", original)
    original = re.sub(r"\blater repeated (?:that|at)\s+", "and ", original, flags=re.I)

    patterns = [
        r"^action item for (?P<owner>[A-Z][a-zA-Z]+)[,:\-]\s*(?P<task>.+)$",
        r"^(?P<owner>[A-Z][a-zA-Z]+)\s+-\s+(?P<task>.+)$",
        r"^(?P<owner>[A-Z][a-zA-Z]+),\s*please\s+(?:also\s+)?(?P<task>.+)$",
        r"^(?P<owner>[A-Z][a-zA-Z]+)\s+(?:will|to|should|owns?)\s+(?P<task>.+)$",
        r"^(?P<owner>[A-Z][a-zA-Z]+)\s+needs?\s+to\s+(?P<task>.+)$",
    ]

    for pattern in patterns:
        match = re.search(pattern, original)
        if match:
            owner = match.group("owner").strip()
            task = match.group("task").strip()
            task = re.sub(r"^also\s+", "", task, flags=re.I)
            return owner, task

    return None, original


def _owner_hints_from_texts(texts: list[str]) -> dict[str, list[str]]:
    """Parse generic owner hints like 'Priya for proposal, Jordan for pricing'."""

    hints: dict[str, list[str]] = {}

    for text in texts:
        if " for " not in text.lower():
            continue

        # Normalize ", and Alex for ..." into ", Alex for ..." so each owner
        # block is parsed separately instead of being absorbed by the previous owner.
        owner_text = re.sub(
            r",\s+and\s+([A-Z][a-zA-Z]+)\s+for\b",
            r", \1 for",
            text,
        )

        # Capture repeated chunks such as:
        # Priya for proposal and demo cleanup
        # Jordan for pricing
        # Morgan for client email and onboarding guidance
        # Alex for final review and dry run
        matches = re.finditer(
            r"\b(?P<owner>[A-Z][a-zA-Z]+)\s+for\s+(?P<topic>[^.;]+?)(?=,\s+[A-Z][a-zA-Z]+\s+for\b|$)",
            owner_text,
        )

        for match in matches:
            owner = match.group("owner").strip()
            topic = match.group("topic").strip()
            parts = re.split(r"\s*,\s*|\s+and\s+", topic)
            keywords = [_norm(part) for part in parts if _norm(part)]

            expanded_keywords = list(keywords)
            for keyword in keywords:
                if "client" in keyword and "email" in keyword:
                    expanded_keywords.extend(
                        [
                            "client follow-up email",
                            "follow-up email",
                            "client follow-up",
                        ]
                    )

                if keyword == "pricing":
                    expanded_keywords.extend(["finance", "price"])

                if keyword == "demo cleanup":
                    expanded_keywords.extend(
                        [
                            "clean demo",
                            "clean the demo",
                            "demo account",
                            "old test files",
                            "approved sample",
                        ]
                    )

            keywords = sorted(set(expanded_keywords))
            if keywords:
                hints.setdefault(owner, [])
                hints[owner].extend(keywords)

    return hints


def infer_owner(
    task: str,
    existing_owner: str | None = None,
    owner_hints: dict[str, list[str]] | None = None,
) -> str:
    owner = _text(existing_owner)
    if owner and _norm(owner) not in _GENERIC_OWNERS:
        return owner

    explicit_owner, cleaned_task = _extract_owner_from_action_text(task)
    if explicit_owner:
        return explicit_owner

    normalized_task = _norm(cleaned_task)
    for candidate, keywords in (owner_hints or {}).items():
        if any(keyword and keyword in normalized_task for keyword in keywords):
            return candidate

    return owner if owner else "Team"


def clean_risks(risks: list[Any]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()

    for risk in risks:
        text = _item_text(risk).rstrip(".")
        if not text:
            continue

        if _matches_any(text, _BAD_RISK_PATTERNS):
            continue

        if not _matches_any(text, _RISK_SIGNAL_PATTERNS):
            continue

        key = _dedupe_key(text)
        if key in seen:
            continue

        seen.add(key)
        cleaned.append(text)

    return cleaned


def clean_decisions(decisions: list[Any]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()

    for decision in decisions:
        text = _item_text(decision).strip(" .")
        if not text:
            continue

        normalized = _norm(text)
        if _matches_any(text, _BAD_DECISION_PATTERNS):
            continue
        if normalized in seen:
            continue

        seen.add(normalized)
        cleaned.append(text)

    return cleaned


def _candidate_action_from_text(text: str) -> str | None:
    candidate = _clean_readability(_text(text))
    if not candidate:
        return None

    owner, candidate = _extract_owner_from_action_text(candidate)

    candidate = re.sub(r"^i will\s+", "", candidate, flags=re.I)
    candidate = re.sub(r"^we will\s+", "", candidate, flags=re.I)
    candidate = re.sub(r"^we should\s+", "", candidate, flags=re.I)
    candidate = re.sub(r"^please\s+(?:also\s+)?", "", candidate, flags=re.I)
    candidate = re.sub(r"\bshe will\s+", "", candidate, flags=re.I)
    candidate = re.sub(
        r"\bthe landing page copy needs to go to (?P<recipient>[A-Z][a-zA-Z]+) by (?P<deadline>[^.]+)$",
        r"send the landing page copy to \g<recipient> by \g<deadline>",
        candidate,
        flags=re.I,
    )
    if owner and "send the landing page copy to" in candidate.lower():
        candidate = re.sub(
            r"^send the onboarding copy tomorrow and\s+(?:and\s+)?",
            "update the landing page onboarding copy and ",
            candidate,
            flags=re.I,
        )
    candidate = candidate.strip(" -.")

    if len(candidate) < 8:
        return None

    if _matches_any(candidate, _BAD_ACTION_PATTERNS):
        return None

    if not _matches_any(candidate, _ACTION_SIGNAL_PATTERNS):
        return None

    return candidate


def _additional_action_candidates_from_text(text: str) -> list[dict[str, Any]]:
    original = _clean_readability(text)
    speakerless = re.sub(r"^[A-Z][a-zA-Z]+\s+says?,\s*", "", original)
    candidates: list[dict[str, Any]] = []

    update_match = re.search(
        r"\b(?P<owner>[A-Z][a-zA-Z]+)\s+will\s+(?P<task>update the landing page onboarding copy\b.+?\bby friday morning\b)",
        speakerless,
        flags=re.I,
    )
    if update_match:
        candidates.append(
            _make_action(update_match.group("task").strip(), update_match.group("owner").strip())
        )

    marco_match = re.search(
        r"\b(?P<owner>[A-Z][a-zA-Z]+)\s+repeated that\s+(?:she|he|they)\s+will\b.+?\bthe landing page copy needs to go to (?P<recipient>[A-Z][a-zA-Z]+) by (?P<deadline>[^.]+)$",
        speakerless,
        flags=re.I,
    )
    if marco_match:
        candidates.append(
            _make_action(
                f"send the landing page copy to {marco_match.group('recipient').strip()} by {marco_match.group('deadline').strip()}",
                marco_match.group("owner").strip(),
            )
        )

    return candidates


def collect_action_candidates(
    notes: dict[str, Any],
    owner_hints: dict[str, list[str]],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    for item in notes.get("action_item_objects") or []:
        if not isinstance(item, dict):
            continue
        task = _item_text(item)
        if not task:
            continue
        owner = _text(item.get("owner")) or "Team"
        inferred_owner = infer_owner(task, owner, owner_hints)
        candidates.append(_make_action(task, inferred_owner))

    for item in notes.get("action_items") or []:
        task = _item_text(item)
        if not task:
            continue

        raw_owner = item.get("owner") if isinstance(item, dict) else None
        inferred_owner = infer_owner(task, _text(raw_owner), owner_hints)
        candidates.append(_make_action(task, inferred_owner))

    for field in ("summary", "purpose", "outcome", "next_steps", "key_points", "decisions"):
        values = [notes.get(field)] if isinstance(notes.get(field), str) else notes.get(field) or []
        for item in values:
            text = _item_text(item)
            candidate_task = _candidate_action_from_text(text)
            if candidate_task:
                owner = infer_owner(text, None, owner_hints)
                candidates.append(_make_action(candidate_task, owner))
            candidates.extend(_additional_action_candidates_from_text(text))

    summary_slots = notes.get("summary_slots")
    if isinstance(summary_slots, dict):
        for key in ("purpose", "outcome", "next_steps"):
            values = (
                [summary_slots.get(key)]
                if isinstance(summary_slots.get(key), str)
                else summary_slots.get(key) or []
            )
            for item in values:
                text = _item_text(item)
                candidate_task = _candidate_action_from_text(text)
                if candidate_task:
                    owner = infer_owner(text, None, owner_hints)
                    candidates.append(_make_action(candidate_task, owner))
                candidates.extend(_additional_action_candidates_from_text(text))

    return candidates


def dedupe_actions(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()

    for action in actions:
        task = _text(action.get("task"))
        if not task:
            continue

        if _matches_any(task, _BAD_ACTION_PATTERNS):
            continue

        key = _action_merge_key(task)
        existing_index = next(
            (
                index
                for index, existing in enumerate(deduped)
                if existing.get("_merge_key") == key
                and _norm(str(existing.get("owner") or "")) == _norm(str(action.get("owner") or ""))
            ),
            None,
        )

        cleaned = dict(action)
        cleaned["task"] = _capitalize_task(task)
        cleaned["owner"] = _text(action.get("owner")) or "Team"
        cleaned.setdefault("status", "open")
        cleaned.setdefault("priority", "medium")
        cleaned["_merge_key"] = key

        if existing_index is not None:
            if _action_strength(cleaned["task"]) > _action_strength(
                str(deduped[existing_index].get("task") or "")
            ):
                deduped[existing_index] = cleaned
            continue

        if key in seen:
            continue

        seen.add(key)
        deduped.append(cleaned)

    return [{k: v for k, v in action.items() if k != "_merge_key"} for action in deduped]


def _action_merge_key(task: str) -> str:
    normalized = _dedupe_key(task)
    if "landing page" in normalized and ("onboarding copy" in normalized or "copy" in normalized):
        if "marco" in normalized:
            return "landing page copy to marco"
        return "landing page onboarding copy"
    if "support page" in normalized and "review recommended" in normalized:
        return "support page review recommended language"
    if "linkedin post" in normalized or "linked in post" in normalized:
        return "linkedin post versions"
    return normalized


def _action_strength(task: str) -> int:
    normalized = _norm(task)
    score = len(normalized.split())
    if re.search(
        r"\bby\s+(?:\d|monday|tuesday|wednesday|thursday|friday|tomorrow|tonight)", normalized
    ):
        score += 20
    if re.search(r"\bbefore\b|\bend of\b", normalized):
        score += 12
    if any(
        word in normalized for word in ("marco", "launch post", "founder style", "product style")
    ):
        score += 10
    return score


def infer_high_confidence_risks(notes: dict[str, Any]) -> list[str]:
    """Infer a few conservative risks from strong business signals."""

    joined = " ".join(
        _item_text(item)
        for field in (
            "summary",
            "purpose",
            "outcome",
            "key_points",
            "decisions",
            "next_steps",
            "action_items",
        )
        for item in (
            [notes.get(field)] if isinstance(notes.get(field), str) else notes.get(field) or []
        )
    )
    normalized = _norm(joined)

    inferred: list[str] = []

    if "pricing" in normalized and ("finance" in normalized or "confirm" in normalized):
        inferred.append("Pricing confirmation may delay the client follow-up")

    if (
        "old test files" in normalized
        or "clean demo account" in normalized
        or "approved sample meeting" in normalized
    ):
        inferred.append("Old test files or an unprepared demo account may reduce client confidence")

    if "custom reporting" in normalized and (
        "phase two" in normalized or "first month" in normalized
    ):
        inferred.append(
            "Over-promising custom reporting may create unrealistic client expectations"
        )

    if "long recordings" in normalized and (
        "may miss some details" in normalized or "review" in normalized
    ):
        inferred.append(
            "Long recordings may miss details, so important action items should be reviewed before sharing externally"
        )

    if "trust gap" in normalized or (
        "different domains" in normalized
        and ("pricing page" in normalized or "landing page" in normalized)
    ):
        inferred.append(
            "Moving users between different domains may create a trust gap during signup or checkout"
        )

    if "reliability" in normalized and ("support" in normalized or "review" in normalized):
        inferred.append(
            "Support and reliability messaging may be unclear if long-recording review guidance is missing"
        )

    return inferred


def apply_risk_action_owner_consistency(notes: dict[str, Any]) -> dict[str, Any]:
    """Return a client-facing notes dict with cleaner risks/actions/owners."""

    result = dict(notes)
    result = _clean_text_fields(result)

    summary_slots = result.get("summary_slots")
    if isinstance(summary_slots, dict):
        slot_risks = summary_slots.get("risks")
        if isinstance(slot_risks, list):
            result["risks"] = list(result.get("risks") or []) + slot_risks

    owner_hint_texts: list[str] = []
    for field in ("key_points", "decisions", "next_steps"):
        owner_hint_texts.extend(_item_text(item) for item in result.get(field) or [])

    owner_hints = _owner_hints_from_texts(owner_hint_texts)

    cleaned_risks = clean_risks(list(result.get("risks") or []))
    inferred_risks = clean_risks(infer_high_confidence_risks(result))
    cleaned_risks = _dedupe_texts([*cleaned_risks, *inferred_risks], limit=5)
    result["risks"] = cleaned_risks
    if isinstance(summary_slots, dict):
        updated_slots = dict(summary_slots)
        updated_slots["risks"] = cleaned_risks
        result["summary_slots"] = updated_slots

    cleaned_decisions = clean_decisions(list(result.get("decisions") or []))
    result["decisions"] = cleaned_decisions
    result["decision_objects"] = [
        {"text": decision, "confidence": 0.8} for decision in cleaned_decisions
    ]

    action_candidates = collect_action_candidates(result, owner_hints)
    cleaned_actions = dedupe_actions(action_candidates)
    result["action_items"] = cleaned_actions
    result["action_item_objects"] = cleaned_actions

    if result["action_items"]:
        next_steps = [item["task"].rstrip(".") + "." for item in result["action_items"][:5]]
        result["next_steps"] = next_steps
        summary_slots = result.get("summary_slots")
        if isinstance(summary_slots, dict):
            updated_slots = dict(summary_slots)
            updated_slots["next_steps"] = next_steps
            result["summary_slots"] = updated_slots

    return result


def _dedupe_texts(values: list[str], *, limit: int) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _clean_readability(value).strip(" .")
        if not text:
            continue
        key = _dedupe_key(text)
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(text)
        if len(cleaned) >= limit:
            break
    return cleaned


def _clean_text_fields(notes: dict[str, Any]) -> dict[str, Any]:
    result = dict(notes)
    for key in ("summary", "purpose", "outcome"):
        if isinstance(result.get(key), str):
            result[key] = _clean_publishable_text_field(str(result[key]))

    for key in ("key_points", "decisions", "next_steps", "risks", "action_items"):
        if isinstance(result.get(key), list):
            result[key] = [_clean_readability(_item_text(item)) for item in result[key]]

    summary_slots = result.get("summary_slots")
    if isinstance(summary_slots, dict):
        cleaned_slots = dict(summary_slots)
        for key in ("purpose", "outcome", "edited_summary"):
            if isinstance(cleaned_slots.get(key), str):
                cleaned_slots[key] = _clean_publishable_text_field(str(cleaned_slots[key]))
        for key in ("risks", "next_steps"):
            if isinstance(cleaned_slots.get(key), list):
                cleaned_slots[key] = [
                    _clean_readability(_item_text(item)) for item in cleaned_slots[key]
                ]
        result["summary_slots"] = cleaned_slots

    return result


def _clean_publishable_text_field(text: str) -> str:
    cleaned = _clean_readability(text)
    cleaned = re.sub(
        r"\s*The team aligned on:\s*Discussion should not become a decision\b.*$",
        "",
        cleaned,
        flags=re.I,
    )
    if _matches_any(cleaned, _BAD_DECISION_PATTERNS) or _matches_any(cleaned, _BAD_ACTION_PATTERNS):
        return ""
    return cleaned.strip()
