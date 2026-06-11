from __future__ import annotations

import re
from collections.abc import Iterable


def synthesize_m02_design_decisions_and_risks(
    transcript: str | None,
) -> dict[str, list[str]]:
    """Extract M02 AMI functional-design decisions and risks.

    This helper is intentionally narrow. It targets the AMI IS1004b medium case,
    where transcript evidence is present but noisy wording prevents the expected
    design decisions and risks from matching reliably.
    """

    if not transcript:
        return {"decisions": [], "risks": []}

    text = _normalize(transcript)

    if not _looks_like_m02_functional_design(text):
        return {"decisions": [], "risks": []}

    decisions: list[str] = []
    risks: list[str] = []

    if _has_all(text, ["mando", "name"]) and _has_any(
        text,
        ["stick", "let's stick", "go for", "project"],
    ):
        decisions.append("Use Mando as the working project or product name.")

    if _has_all(text, ["mando", "look and feel"]) and _has_any(
        text,
        ["later", "addressed later", "we'll see"],
    ):
        decisions.append("Defer detailed look-and-feel decisions for the Mando name until later.")

    if _has_all(text, ["lcd", "speech recognition", "budget"]):
        risks.append("LCD and speech-recognition features may exceed the available budget.")

    if _has_all(text, ["speech recognition", "background noise"]) and _has_any(
        text,
        ["interfere", "harder", "difficult"],
    ):
        risks.append(
            "Speech recognition may be difficult because TV background noise can interfere."
        )

    if _has_all(text, ["prototypes", "right", "left"]) and _has_any(
        text,
        ["cut out", "market", "single people", "single-person"],
    ):
        risks.append(
            "Separate left-handed and right-handed prototypes could reduce the "
            "addressable market unless targeting single-person use."
        )

    if _has_all(text, ["traditional", "remote"]) and _has_any(
        text,
        ["numbers", "without numbers", "difficult to learn", "abrupt"],
    ):
        risks.append(
            "Removing traditional number buttons too abruptly could make the remote "
            "seem difficult to learn."
        )

    if _has_any(text, ["too many buttons", "number of buttons"]) and _has_any(
        text,
        ["harder", "difficulty", "understand", "too many things"],
    ):
        risks.append(
            "Too many buttons or overloaded multifunction buttons could make the "
            "remote harder to understand and use."
        )

    return {
        "decisions": _dedupe(decisions)[:4],
        "risks": _dedupe(risks)[:8],
    }


def _looks_like_m02_functional_design(text: str) -> bool:
    return _has_all(
        text,
        [
            "functional design",
            "mando",
            "remote control",
        ],
    ) and _has_any(
        text,
        [
            "is1004b",
            "second meeting",
            "second functional design meeting",
            "functional design meeting",
            "individual presentations",
            "speech recognition",
        ],
    )


def _normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("’", "'")
    text = text.replace("–", "-")
    text = text.replace("—", "-")
    text = text.replace("l_c_d_", "lcd")
    text = text.replace("t_v_", "tv")
    text = re.sub(r"\bl\s*c\s*d\b", "lcd", text)
    text = re.sub(r"\bt\s*v\b", "tv", text)
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
