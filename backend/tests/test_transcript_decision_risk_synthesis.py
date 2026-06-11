from __future__ import annotations

from backend.app.services.transcript_decision_risk_synthesis import (
    synthesize_decisions_and_risks_from_transcript,
)


def test_remote_control_decision_risk_synthesis() -> None:
    transcript = (
        "The team discussed a remote control for TV users with an LCD screen. "
        "The design needs rubber buttons as backup, easy two digit channel entry, "
        "teletext menus, older users, younger users, battery drain, and cost."
    )

    result = synthesize_decisions_and_risks_from_transcript(transcript)
    text = " ".join(result["decisions"] + result["risks"]).lower()

    assert "lcd" in text
    assert "cost" in text
    assert "battery" in text
    assert "channel" in text
    assert "older users" in text


def test_annotation_density_decision_risk_synthesis() -> None:
    transcript = (
        "The meeting discussed NITE XML annotation files, information density, "
        "segments, word-level values, entropy from LSA, Rainbow output, "
        "manual parsing of times, and mapping values back to segment identifiers."
    )

    result = synthesize_decisions_and_risks_from_transcript(transcript)
    text = " ".join(result["decisions"] + result["risks"]).lower()

    assert "segment" in text
    assert "entropy" in text
    assert "rainbow" in text
    assert "manual parsing" in text
    assert "word" in text


def test_video_shot_detector_decision_risk_synthesis() -> None:
    transcript = (
        "The meeting discussed a shot detector for CINETIS restoration, "
        "key frames, histogram distance, motion features, dissolves, "
        "OpenCV, MPEG input, Debian compile issues, privacy, browser directories, "
        "and DVD grabbing problems."
    )

    result = synthesize_decisions_and_risks_from_transcript(transcript)
    text = " ".join(result["decisions"] + result["risks"]).lower()

    assert "shot" in text
    assert "keyframes" in text
    assert "motion" in text
    assert "privacy" in text
    assert "dvd" in text
