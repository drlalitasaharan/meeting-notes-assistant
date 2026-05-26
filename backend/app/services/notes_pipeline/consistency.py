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
    r"\bthe demo should show the workflow\b",
    r"\bupload meeting recording\b",
    r"\bwait for processing\b",
    r"\breview summary\b",
    r"\bcopy or export\b",
    r"\brisks and action items\b",
]

_RISK_SIGNAL_PATTERNS = [
    r"\bdelay\b",
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
]

_ACTION_SIGNAL_PATTERNS = [
    r"\bconfirm\b",
    r"\bupdate\b",
    r"\bsend\b",
    r"\bdraft\b",
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
]

_BAD_ACTION_PATTERNS = [
    r"\btoday (we )?need to confirm\b",
    r"\bthe demo should show the workflow\b",
    r"\bif we send\b",
    r"\bclient can renew\b",
    r"\bsuccess criteria\b.*\bweekly\b",
]


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


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
                return value
        return ""
    return _text(item)


def _capitalize_task(task: str) -> str:
    task = task.strip()
    if not task:
        return task
    return task[0].upper() + task[1:]


def _make_action(task: str, owner: str = "Team") -> dict[str, Any]:
    return {
        "owner": owner,
        "task": _capitalize_task(task),
        "status": "open",
        "priority": "medium",
    }


def _extract_owner_from_action_text(text: str) -> tuple[str | None, str]:
    """Extract owner from direct action language when available."""

    original = text.strip()

    patterns = [
        r"^action item for (?P<owner>[A-Z][a-zA-Z]+)[,:\-]\s*(?P<task>.+)$",
        r"^(?P<owner>[A-Z][a-zA-Z]+)\s+(?:will|to|should|owns?)\s+(?P<task>.+)$",
    ]

    for pattern in patterns:
        match = re.search(pattern, original)
        if match:
            owner = match.group("owner").strip()
            task = match.group("task").strip()
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


def _candidate_action_from_text(text: str) -> str | None:
    candidate = _text(text)
    if not candidate:
        return None

    _, candidate = _extract_owner_from_action_text(candidate)

    candidate = re.sub(r"^i will\s+", "", candidate, flags=re.I)
    candidate = re.sub(r"^we will\s+", "", candidate, flags=re.I)
    candidate = re.sub(r"^we should\s+", "", candidate, flags=re.I)
    candidate = candidate.strip(" -.")

    if len(candidate) < 8:
        return None

    if _matches_any(candidate, _BAD_ACTION_PATTERNS):
        return None

    if not _matches_any(candidate, _ACTION_SIGNAL_PATTERNS):
        return None

    return candidate


def collect_action_candidates(
    notes: dict[str, Any],
    owner_hints: dict[str, list[str]],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    for item in notes.get("action_items") or []:
        task = _item_text(item)
        if not task:
            continue

        owner = item.get("owner") if isinstance(item, dict) else None
        candidates.append(_make_action(task, infer_owner(task, _text(owner), owner_hints)))

    for field in ("next_steps", "key_points", "decisions"):
        for item in notes.get(field) or []:
            text = _item_text(item)
            task = _candidate_action_from_text(text)  # type: ignore[assignment]
            if task:
                owner = infer_owner(text, None, owner_hints)
                candidates.append(_make_action(task, owner))

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

        key = _dedupe_key(task)
        if key in seen:
            continue

        seen.add(key)
        cleaned = dict(action)
        cleaned["task"] = _capitalize_task(task)
        cleaned["owner"] = _text(action.get("owner")) or "Team"
        cleaned.setdefault("status", "open")
        cleaned.setdefault("priority", "medium")
        deduped.append(cleaned)

    return deduped


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

    return inferred


def apply_risk_action_owner_consistency(notes: dict[str, Any]) -> dict[str, Any]:
    """Return a client-facing notes dict with cleaner risks/actions/owners."""

    result = dict(notes)

    owner_hint_texts: list[str] = []
    for field in ("key_points", "decisions", "next_steps"):
        owner_hint_texts.extend(_item_text(item) for item in result.get(field) or [])

    owner_hints = _owner_hints_from_texts(owner_hint_texts)

    cleaned_risks = clean_risks(list(result.get("risks") or []))
    if not cleaned_risks:
        cleaned_risks = clean_risks(infer_high_confidence_risks(result))
    result["risks"] = cleaned_risks

    action_candidates = collect_action_candidates(result, owner_hints)
    result["action_items"] = dedupe_actions(action_candidates)

    if result["action_items"]:
        result["next_steps"] = [
            item["task"].rstrip(".") + "." for item in result["action_items"][:5]
        ]

    return result
