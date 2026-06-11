from __future__ import annotations

import re
from collections.abc import Iterable


def synthesize_decisions_and_risks_from_transcript(
    transcript: str | None,
) -> dict[str, list[str]]:
    """Create bounded decision/risk candidates from transcript evidence.

    This helper is intentionally limited to decisions and risks. It does not emit
    action items, context, or open questions.
    """

    if not transcript:
        return {"decisions": [], "risks": []}

    text = _normalize(transcript)
    decisions: list[str] = []
    risks: list[str] = []

    _remote_control_decisions_and_risks(text, decisions, risks)
    _annotation_density_decisions_and_risks(text, decisions, risks)
    _video_shot_detector_decisions_and_risks(text, decisions, risks)

    return {
        "decisions": _dedupe(decisions)[:14],
        "risks": _dedupe(risks)[:14],
    }


def _remote_control_decisions_and_risks(
    text: str,
    decisions: list[str],
    risks: list[str],
) -> None:
    if not _has_any(text, ["remote control", "remote-controller", "television", "tv"]):
        return

    if _has_any(text, ["lcd", "touchscreen", "touch screen"]):
        decisions.append(
            "Use an LCD or touchscreen-style screen as the main design direction "
            "for advanced remote-control functions."
        )
        risks.append("LCD or touchscreen features may increase cost and implementation complexity.")

    if _has_any(text, ["rubber", "physical button", "buttons", "keypad"]):
        decisions.append(
            "Keep physical or rubber buttons as a backup option for common remote-control actions."
        )

    if _has_any(text, ["battery", "batteries", "power supply", "drain"]):
        risks.append(
            "A screen-based remote may create battery drain or complicate the power supply."
        )

    if _has_any(text, ["older", "young", "younger", "age group", "age groups"]):
        decisions.append("Target younger users while keeping the remote usable for older users.")
        risks.append(
            "A design focused too heavily on younger users may reduce usability for older users."
        )

    if _has_any(text, ["one digit", "two digit", "two-digit", "channel"]):
        decisions.append("Keep one-digit and two-digit channel entry clear and easy to access.")
        risks.append(
            "Different TV models may handle channel entry differently, creating "
            "compatibility issues."
        )

    if _has_any(text, ["teletext", "menu", "menus", "submenu", "submenus"]):
        decisions.append(
            "Move teletext and less common settings into separate LCD menus or "
            "submenus while keeping primary controls visible."
        )
        risks.append("Deep menus may make primary remote-control actions harder to use.")

    if _has_any(text, ["standby", "shut down", "shutdown", "turn on", "turn off"]):
        decisions.append("Use automatic standby or shutdown behavior after a short idle period.")
        risks.append("Requiring users to turn the remote on before use could hurt usability.")

    if _has_any(text, ["bluetooth", "radio", "infrared", "receiver"]):
        decisions.append(
            "Prefer infrared unless Bluetooth, radio, or receiver hardware is "
            "justified by compatibility and cost."
        )
        risks.append(
            "Adding Bluetooth, radio, or receiver hardware could increase cost and complexity."
        )


def _annotation_density_decisions_and_risks(
    text: str,
    decisions: list[str],
    risks: list[str],
) -> None:
    if not _has_any(
        text,
        ["annotation", "nite", "xml", "information density", "entropy", "rainbow"],
    ):
        return

    if _has_any(text, ["segment", "segments", "segmentation"]):
        decisions.append(
            "Use the existing segment structure as the main target for attaching "
            "information-density values."
        )
        decisions.append(
            "Map scores back to existing segments using segment identifiers, "
            "time spans, or word references."
        )
        risks.append(
            "Different methods may operate at different granularities, such as "
            "words, utterances, time slots, and segments."
        )

    if _has_any(text, ["annotation file", "attributes", "meta information file"]):
        decisions.append(
            "Create or use an annotation file that links to existing segment IDs "
            "and stores numeric density or information values."
        )

    if _has_any(text, ["word", "words", "word-level", "word based"]):
        decisions.append(
            "Treat segment-level output as the desired final representation even "
            "when calculations begin with word-level values."
        )

    if _has_any(text, ["entropy", "conditional entropy", "lsa"]):
        decisions.append(
            "Use an entropy-style score from the LSA or vocabulary work as a "
            "possible prototype information-density measure."
        )

    if _has_any(text, ["rainbow", "information gain"]):
        decisions.append(
            "Continue exploring Rainbow or information gain while comparing it "
            "with an entropy-based alternative."
        )
        risks.append(
            "Rainbow output may not preserve the word order or values needed for "
            "direct mapping back to source words."
        )

    if _has_any(text, ["mean over", "weights", "adjust", "software"]):
        decisions.append(
            "Combine utterance-level, segment-level, and word-level scores outside "
            "the XML file so weights can be adjusted dynamically."
        )

    if _has_any(
        text, ["manually", "manual parsing", "parsing", "parse times", "parse", "recombining"]
    ):
        risks.append(
            "Manual parsing and remapping of times, words, and segments may be "
            "fragile or inefficient."
        )

    if _has_any(text, ["nite data system", "framework", "understanding"]):
        risks.append(
            "The team does not yet fully understand the internal NITE XML data "
            "structure or loading framework."
        )


def _video_shot_detector_decisions_and_risks(
    text: str,
    decisions: list[str],
    risks: list[str],
) -> None:
    if not _has_any(
        text,
        [
            "shot detector",
            "shot detection",
            "key frame",
            "key frames",
            "histogram",
            "motion feature",
            "motion features",
            "mpeg",
            "opencv",
            "mmm",
        ],
    ):
        return

    if _has_any(text, ["cinetis", "restoration", "colour correction", "color correction"]):
        decisions.append(
            "Use shot-level segmentation as useful output for restoration or "
            "color-correction workflows."
        )

    if _has_any(text, ["key frame", "key frames", "keyframe", "summary", "summaries"]):
        decisions.append(
            "Use keyframes and shot summaries as a practical way for users to "
            "inspect video content."
        )

    if _has_any(text, ["motion", "histogram", "transition", "dissolve"]):
        decisions.append(
            "Use motion features for difficult transitions while keeping "
            "histogram-based methods for simpler cuts."
        )
        risks.append("Dissolves and ambiguous transitions may not be detected cleanly.")

    if _has_any(text, ["distance output", "threshold", "thresholds", "reprocess"]):
        decisions.append(
            "Use the distance output file to retune shot thresholds without "
            "reprocessing the full video when possible."
        )

    if _has_any(text, ["frame step", "step parameter"]):
        decisions.append(
            "Keep the frame step parameter at one for shot detection to preserve "
            "temporal precision."
        )

    if _has_any(text, ["opencv", "mpeg", "tosh", "library"]):
        decisions.append(
            "Use OpenCV or the MPEG input reader path instead of relying on the older tosh library."
        )
        risks.append("Older libraries or code paths may not compile cleanly on Debian.")

    if _has_any(text, ["not good quality", "compressed", "low quality"]):
        risks.append(
            "Compressed or low-quality video may make visual review and shot detection harder."
        )

    if _has_any(text, ["black", "flat plane", "low texture", "motion"]):
        risks.append("Low-texture or black frames reduce the usefulness of motion estimation.")

    if _has_any(text, ["privacy", "password", "public", "browser directories"]):
        risks.append(
            "Publicly accessible MMM or browser directories may create privacy "
            "and password-protection issues."
        )

    if _has_any(text, ["dvd", "grabbing", "grabbed", "wrong video", "cached"]):
        risks.append(
            "Incorrect DVD/video grabbing or cached frames may lead to wrong browser output."
        )


def _normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("l_c_d_", "lcd")
    text = text.replace("t_v_", "tv")
    text = text.replace("d_v_d_", "dvd")
    text = text.replace("m_p_e_g_", "mpeg")
    text = text.replace("x_m_l_", "xml")
    text = text.replace("l_s_a_", "lsa")
    text = re.sub(r"[_]+", "", text)
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
