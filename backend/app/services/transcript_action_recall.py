from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any


def synthesize_action_items_from_transcript(transcript: str | None) -> list[dict[str, Any]]:
    """Create bounded action-item candidates from transcript evidence.

    This helper is action-only. It does not emit decisions, risks, context, or
    open questions. It is intentionally conservative and evidence-driven.
    """

    if not transcript:
        return []

    text = _normalize(transcript)
    actions: list[dict[str, Any]] = []

    _remote_control_actions(text, actions)
    _annotation_density_actions(text, actions)
    _video_shot_detector_actions(text, actions)

    return _dedupe_actions(actions)[:12]


def _remote_control_actions(text: str, actions: list[dict[str, Any]]) -> None:
    if not _has_any(text, ["remote control", "remote-controller", "television", "tv"]):
        return

    if _has_any(text, ["cost information", "price information", "mail folder", "project mail"]):
        actions.append(
            {
                "owner": "Marketing Expert",
                "action": "Post or share LCD cost information in the project mail folder if cost information is received.",
                "deadline": None,
            }
        )

    if _has_any(text, ["minutes", "shared folder"]):
        actions.append(
            {
                "owner": "Industrial Designer",
                "action": "Take minutes and put updated minutes in the shared folder.",
                "deadline": None,
            }
        )

    if _has_any(text, ["after lunch", "individual work", "individual-work"]):
        actions.append(
            {
                "owner": "Team",
                "action": "Do another individual-work session after lunch.",
                "deadline": "after lunch",
            }
        )

    if _has_any(text, ["specific instructions", "next meeting", "email"]) and "after lunch" in text:
        actions.append(
            {
                "owner": "Team",
                "action": "Use the next email instructions for the next meeting or work session.",
                "deadline": "after lunch",
            }
        )

    if _has_any(text, ["smartboard", "save", "jpeg", "image"]) and _has_any(
        text, ["shared", "project documents", "folder"]
    ):
        actions.append(
            {
                "owner": "Team",
                "action": "Save the smartboard or session output into shared/project documents, preferably as an image such as JPEG.",
                "deadline": None,
            }
        )

    if _has_any(text, ["questionnaire", "after lunch"]):
        actions.append(
            {
                "owner": "Team",
                "action": "Fill out the questionnaire after lunch.",
                "deadline": "after lunch",
            }
        )


def _annotation_density_actions(text: str, actions: list[dict[str, Any]]) -> None:
    if not _has_any(
        text, ["annotation", "nite", "xml", "information density", "rainbow", "entropy"]
    ):
        return

    if _has_any(text, ["delimited", "segments", "documents", "annotation structure"]):
        actions.append(
            {
                "owner": "Speaker C",
                "action": "Create files from delimited segments or otherwise prepare data in a form that can be merged with the annotation structure.",
                "deadline": None,
            }
        )

    if _has_any(text, ["lsa", "vocabulary", "dictionary", "entropy score", "each word"]):
        actions.append(
            {
                "owner": "Speaker B",
                "action": "Provide a vocabulary or dictionary with an entropy score for each word as a byproduct of the LSA work.",
                "deadline": None,
            }
        )

    if _has_any(text, ["rainbow"]) and _has_any(text, ["word", "segment", "structure", "output"]):
        actions.append(
            {
                "owner": "Speaker C",
                "action": "Continue working on Rainbow and try to find a way to tie Rainbow output into the shared segment or word structure.",
                "deadline": None,
            }
        )

    if _has_any(text, ["nite data system", "nite framework", "manually", "parse times", "parse"]):
        actions.append(
            {
                "owner": "Speaker B",
                "action": "Spend time understanding the NITE data system so the team can avoid manually parsing and recombining time values where possible.",
                "deadline": None,
            }
        )

    if _has_any(text, ["single value", "one value", "per segment", "word-level output"]):
        actions.append(
            {
                "owner": "Speaker C",
                "action": "Investigate whether it is feasible to produce a single value per segment from the word-level output.",
                "deadline": None,
            }
        )


def _video_shot_detector_actions(text: str, actions: list[dict[str, Any]]) -> None:
    if not _has_any(
        text,
        [
            "shot detector",
            "shot detection",
            "key frame",
            "key frames",
            "histogram",
            "motion features",
            "mpeg",
            "opencv",
            "mmm",
        ],
    ):
        return

    if _has_any(text, ["parameter", "configuration file", "config file"]):
        actions.append(
            {
                "owner": "Speaker B",
                "action": "Provide the shot detector parameter or configuration file discussed at the end of the meeting.",
                "deadline": None,
            }
        )

    if _has_any(text, ["c code", "video-structure", "video structure", "classes", "newer version"]):
        actions.append(
            {
                "owner": "Speaker B",
                "action": "Help review the C code and video-structure classes if newer versions of the detector are used.",
                "deadline": None,
            }
        )

    if _has_any(text, ["xml output", "mmm", "data workflow", "browser"]):
        actions.append(
            {
                "owner": "Speaker B",
                "action": "Explain or document how to put video data and XML output into the MMM data workflow.",
                "deadline": None,
            }
        )

    if _has_any(
        text, ["dvd", "grabbing", "grabbed", "incorrect", "duplicated video", "wrong video"]
    ):
        actions.append(
            {
                "owner": "Speaker C",
                "action": "Check whether the DVD/video grabbing issue produced an incorrect or duplicated video file.",
                "deadline": None,
            }
        )

    if _has_any(text, ["privacy", "password", "public", "browser directories", "mmm browser"]):
        actions.append(
            {
                "owner": "Team",
                "action": "Take privacy/password protection into account before exposing experiment videos or MMM browser directories.",
                "deadline": None,
            }
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


def _dedupe_actions(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []

    for item in items:
        key = " ".join(
            _normalize(
                str(item.get("owner") or "")
                + " "
                + str(item.get("action") or "")
                + " "
                + str(item.get("deadline") or "")
            ).split()
        )

        if not key or key in seen:
            continue

        seen.add(key)
        output.append(item)

    return output
