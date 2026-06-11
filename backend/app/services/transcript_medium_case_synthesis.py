from __future__ import annotations

import re
from collections.abc import Iterable


def synthesize_medium_case_decisions_and_risks(
    transcript: str | None,
) -> dict[str, list[str]]:
    """Create bounded decision/risk candidates for medium business transcripts.

    This helper is intentionally focused on medium-length practical meeting cases.
    It does not emit action items or context.
    """

    if not transcript:
        return {"decisions": [], "risks": []}

    text = _normalize(transcript)
    decisions: list[str] = []
    risks: list[str] = []

    _pilot_and_support_signals(text, decisions, risks)
    _proposal_pricing_demo_signals(text, decisions, risks)
    _client_followup_signals(text, decisions, risks)
    _scope_and_reporting_signals(text, decisions, risks)

    return {
        "decisions": _dedupe(decisions)[:10],
        "risks": _dedupe(risks)[:10],
    }


def _pilot_and_support_signals(
    text: str,
    decisions: list[str],
    risks: list[str],
) -> None:
    if not _has_any(text, ["pilot", "early access", "trial", "test users", "beta"]):
        return

    if _has_any(text, ["twenty users", "20 users", "limit", "cap", "small group"]):
        decisions.append("Limit the pilot to a small controlled group of users.")
        risks.append("Expanding the pilot too broadly may make quality issues harder to control.")

    if _has_any(text, ["email support", "support channel", "support inbox", "email"]):
        decisions.append("Use email as the primary support channel during the pilot.")
        risks.append(
            "Support follow-up may be delayed if support ownership or channel expectations are unclear."
        )

    if _has_any(text, ["feedback", "user feedback", "pilot feedback"]):
        decisions.append("Use pilot feedback to guide the next product improvement cycle.")
        risks.append(
            "Insufficient pilot feedback may make it harder to prioritize the next improvements."
        )


def _proposal_pricing_demo_signals(
    text: str,
    decisions: list[str],
    risks: list[str],
) -> None:
    if not _has_any(text, ["proposal", "pricing", "demo", "client", "customer"]):
        return

    if _has_any(text, ["pricing", "price", "cost", "pricing table", "pricing confirmation"]):
        decisions.append(
            "Keep pricing confirmation as a required input before final client follow-up."
        )
        risks.append("Pricing confirmation may delay the client follow-up.")
        risks.append("Unclear pricing may reduce confidence in the proposal.")

    if _has_any(text, ["demo account", "clean demo", "old test", "test files", "sample file"]):
        decisions.append(
            "Use a clean demo account and approved sample file for client-facing demonstrations."
        )
        risks.append("Old test files or an unclean demo account may reduce client confidence.")

    if _has_any(text, ["backup demo", "backup file", "meeting 17", "backup processed"]):
        decisions.append("Keep a backup processed meeting ready for client demonstrations.")
        risks.append("The live demo may fail if no backup processed meeting is ready.")

    if _has_any(text, ["ten minute", "10 minute", "realistic file", "proof of quality"]):
        decisions.append("Use the realistic 10-minute file as the main proof of quality.")
        risks.append("Using an unrealistic demo file may create misleading quality expectations.")


def _client_followup_signals(
    text: str,
    decisions: list[str],
    risks: list[str],
) -> None:
    if not _has_any(text, ["client", "customer", "follow-up", "follow up", "meeting"]):
        return

    if _has_any(text, ["tuesday", "monday", "target client meeting", "client meeting"]):
        decisions.append(
            "Use the agreed client meeting date as the target for follow-up readiness."
        )
        risks.append(
            "Client follow-up may slip if meeting readiness tasks are not completed in time."
        )

    if _has_any(text, ["follow-up message", "follow up message", "short message", "concise"]):
        decisions.append("Use a concise client follow-up message focused on practical value.")
        risks.append("A broad or unclear follow-up message may weaken client confidence.")

    if _has_any(text, ["readiness", "ready", "demo readiness", "launch readiness"]):
        risks.append("Incomplete demo readiness may create a poor first client impression.")


def _scope_and_reporting_signals(
    text: str,
    decisions: list[str],
    risks: list[str],
) -> None:
    if not _has_any(text, ["scope", "reporting", "custom report", "custom reporting", "phase 2"]):
        return

    if _has_any(text, ["phase 2", "later", "not now", "future"]):
        decisions.append("Keep custom reporting or advanced reporting as a phase 2 item.")
        risks.append("Promising custom reporting too early may create unrealistic expectations.")

    if _has_any(text, ["scope", "proposal scope", "out of scope", "in scope"]):
        decisions.append("Keep the proposal scope focused on the agreed pilot deliverables.")
        risks.append("Unclear proposal scope may create delivery risk or client confusion.")

    if _has_any(text, ["over-promising", "over promising", "promise too much"]):
        risks.append("Over-promising custom reporting may create unrealistic expectations.")


def _normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("’", "'")
    text = text.replace("–", "-")
    text = text.replace("—", "-")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _has_any(text: str, terms: Iterable[str]) -> bool:
    return any(term in text for term in terms)


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
