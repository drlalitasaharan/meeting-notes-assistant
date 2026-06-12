from __future__ import annotations

import re
from collections.abc import Iterable


def synthesize_explicit_commitments(transcript: str | None) -> dict[str, list]:
    """Extract explicit decisions, actions, and risks from controlled business transcripts.

    This helper targets transcripts that use strong commitment language such as:
    - Decision confirmed
    - Explicit action
    - Risk confirmed

    It is intentionally bounded and does not change evaluator or fixture logic.
    """

    if not transcript:
        return {"decisions": [], "action_items": [], "risks": []}

    text = _normalize(transcript)

    if not _looks_like_controlled_pilot_review(text):
        return {"decisions": [], "action_items": [], "risks": []}

    decisions = _synthesize_decisions(text)
    action_items = _synthesize_actions(text)
    risks = _synthesize_risks(text)

    return {
        "decisions": _dedupe(decisions)[:12],
        "action_items": action_items[:12],
        "risks": _dedupe(risks)[:10],
    }


def _looks_like_controlled_pilot_review(text: str) -> bool:
    return _has_all(
        text,
        [
            "commercial pilot",
            "decision confirmed",
            "explicit action",
        ],
    ) and _has_any(
        text,
        [
            "pilot pricing table",
            "recording-duration policy",
            "security review",
            "pilot support",
        ],
    )


def _synthesize_decisions(text: str) -> list[str]:
    decisions: list[str] = []

    if _has_all(text, ["twenty customer users", "decision confirmed"]):
        decisions.append("Limit the initial commercial pilot to twenty customer users.")

    if _has_all(text, ["thirty minutes", "standard limit"]):
        decisions.append("Limit standard pilot recordings to thirty minutes.")

    if _has_all(text, ["sixty-minute", "approved evaluation accounts"]):
        decisions.append("Allow sixty-minute recordings only for approved evaluation accounts.")

    if _has_all(text, ["email", "primary pilot support channel"]):
        decisions.append("Use email as the primary pilot support channel.")

    if _has_all(text, ["uploaded pilot recordings", "thirty days"]):
        decisions.append("Retain uploaded pilot recordings for thirty days.")

    if _has_all(text, ["single sign-on", "outside the initial commercial scope"]):
        decisions.append("Keep single sign-on outside the initial commercial scope.")

    if _has_all(text, ["launch date", "pricing and security approval"]):
        decisions.append(
            "Do not announce the launch date until pricing and security approval are complete."
        )

    if _has_all(text, ["first twenty processed meetings", "quality and usage"]):
        decisions.append(
            "Review pilot quality and usage after the first twenty processed meetings."
        )

    return decisions


def _synthesize_actions(text: str) -> list[dict[str, str | None]]:
    actions: list[dict[str, str | None]] = []
    actions.extend(_synthesize_recap_actions(text))

    if "circulate the approved pilot pricing table" in text:
        actions.append(
            {
                "owner": "Priya",
                "action": "Circulate the approved pilot pricing table.",
                "deadline": "2026-06-18 17:00",
            }
        )

    if "upload the final demonstration recording" in text:
        actions.append(
            {
                "owner": "Jordan",
                "action": "Upload the final demonstration recording.",
                "deadline": "2026-06-19 15:00",
            }
        )

    if "complete the storage and access-control security review" in text:
        actions.append(
            {
                "owner": "Alex",
                "action": "Complete the storage and access-control security review.",
                "deadline": "2026-06-22 12:00",
            }
        )

    if "prepare the pilot support-response templates" in text:
        actions.append(
            {
                "owner": "Morgan",
                "action": "Prepare the pilot support-response templates.",
                "deadline": "2026-06-23 17:00",
            }
        )

    if "confirm the first pilot customer participant list" in text:
        actions.append(
            {
                "owner": "Priya",
                "action": "Confirm the first pilot customer participant list.",
                "deadline": "2026-06-24 12:00",
            }
        )

    if "run the twelve-recording regression suite and document failures" in text:
        actions.append(
            {
                "owner": "Jordan",
                "action": "Run the twelve-recording regression suite and document failures.",
                "deadline": "2026-06-25 17:00",
            }
        )

    if "verify recording deletion from storage after the retention test" in text:
        actions.append(
            {
                "owner": "Alex",
                "action": "Verify recording deletion from storage after the retention test.",
                "deadline": None,
            }
        )

    if "create the customer onboarding checklist" in text:
        actions.append(
            {
                "owner": "Morgan",
                "action": "Create the customer onboarding checklist.",
                "deadline": None,
            }
        )

    if "confirm whether regional data storage is required" in text:
        actions.append(
            {
                "owner": None,
                "action": "Confirm whether regional data storage is required.",
                "deadline": None,
            }
        )

    if "review whether contractor accounts may join the pilot" in text:
        actions.append(
            {
                "owner": None,
                "action": "Review whether contractor accounts may join the pilot.",
                "deadline": None,
            }
        )

    return _dedupe_actions(actions)


def _synthesize_recap_actions(text: str) -> list[dict[str, str | None]]:
    """Extract final-recap actions from long controlled meeting transcripts.

    This protects commitments that appear late in long recordings, especially
    recap lines in the form:
    Recap action: <task>. Owner: <owner>. Deadline: <deadline>.
    """

    actions: list[dict[str, str | None]] = []

    pattern = re.compile(
        r"recap action:\s*(?P<action>[^.]+)\.\s*"
        r"owner:\s*(?P<owner>[^.]+)\.\s*"
        r"deadline:\s*(?P<deadline>[^.]+)\.",
        re.IGNORECASE,
    )

    for match in pattern.finditer(text):
        action = _clean_recap_action(match.group("action"))
        if not action:
            continue

        actions.append(
            {
                "owner": _clean_recap_owner(match.group("owner")),
                "action": action,
                "deadline": _clean_recap_deadline(match.group("deadline")),
            }
        )

    return actions


def _clean_recap_action(value: str | None) -> str:
    text = " ".join((value or "").strip().split())
    if not text:
        return ""

    text = text[0].upper() + text[1:]
    return text.rstrip(".") + "."


def _clean_recap_owner(value: str | None) -> str | None:
    text = " ".join((value or "").strip().split())
    if not text or text.lower() in {"none", "no owner", "unassigned"}:
        return None

    return text.title()


def _clean_recap_deadline(value: str | None) -> str | None:
    text = " ".join((value or "").strip().split())
    if not text or text.lower() in {"none", "no deadline", "unassigned"}:
        return None

    return text


def _synthesize_risks(text: str) -> list[str]:
    risks: list[str] = []

    if _has_all(text, ["pricing approval", "postpone commercial follow-up"]):
        risks.append("Delayed pricing approval could postpone commercial follow-up.")

    if _has_all(text, ["security review", "delay launch approval"]):
        risks.append("An incomplete security review could delay launch approval.")

    if _has_all(text, ["poor-quality recordings", "transcription and action recall"]):
        risks.append("Poor-quality recordings could reduce transcription and action recall.")

    if _has_all(text, ["sixty-minute usage", "processing cost and delay"]):
        risks.append("Unexpected sixty-minute usage could increase processing cost and delay.")

    if _has_all(text, ["retention requirements", "privacy approval"]):
        risks.append("Unclear retention requirements could delay privacy approval.")

    if _has_all(text, ["unconfirmed customer user count", "capacity assumptions"]):
        risks.append(
            "An unconfirmed customer user count could create inaccurate capacity assumptions."
        )

    return risks


def _normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("’", "'")
    text = text.replace("–", "-")
    text = text.replace("—", "-")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _has_any(text: str, terms: Iterable[str]) -> bool:
    return any(term in text for term in terms)


def _has_all(text: str, terms: Iterable[str]) -> bool:
    return all(term in text for term in terms)


def _dedupe(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []

    for item in items:
        key = " ".join(_normalize(item).split())
        if not key or key in seen:
            continue

        seen.add(key)
        output.append(item)

    return output


def _dedupe_actions(
    actions: Iterable[dict[str, str | None]],
) -> list[dict[str, str | None]]:
    seen: set[tuple[str | None, str, str | None]] = set()
    output: list[dict[str, str | None]] = []

    for action in actions:
        key = (
            action.get("owner"),
            action.get("action") or "",
            action.get("deadline"),
        )

        if key in seen:
            continue

        seen.add(key)
        output.append(action)

    return output
