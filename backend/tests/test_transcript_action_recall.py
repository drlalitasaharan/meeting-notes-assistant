from __future__ import annotations

from backend.app.services.transcript_action_recall import synthesize_action_items_from_transcript


def test_remote_control_action_recall_from_evidence() -> None:
    transcript = (
        "The team discussed a remote control and LCD screen cost. "
        "The marketing expert will post the cost information in the project mail folder. "
        "After lunch, the team will fill out the questionnaire."
    )

    actions = synthesize_action_items_from_transcript(transcript)
    text = " ".join(str(item) for item in actions).lower()

    assert "marketing expert" in text
    assert "cost information" in text
    assert "project mail folder" in text
    assert "questionnaire" in text
    assert "after lunch" in text


def test_annotation_density_action_recall_from_evidence() -> None:
    transcript = (
        "The group discussed NITE XML annotation files, delimited segments, "
        "Rainbow output, LSA vocabulary, entropy score for each word, and manually parsing times."
    )

    actions = synthesize_action_items_from_transcript(transcript)
    text = " ".join(str(item) for item in actions).lower()

    assert "speaker b" in text
    assert "entropy score" in text
    assert "speaker c" in text
    assert "rainbow" in text
    assert "nite data system" in text


def test_video_shot_detector_action_recall_from_evidence() -> None:
    transcript = (
        "The meeting discussed a shot detector, parameter configuration file, "
        "C code and video-structure classes, XML output in the MMM data workflow, "
        "DVD grabbing issues, privacy, password protection, and browser directories."
    )

    actions = synthesize_action_items_from_transcript(transcript)
    text = " ".join(str(item) for item in actions).lower()

    assert "parameter" in text
    assert "c code" in text
    assert "mmm data workflow" in text
    assert "dvd" in text
    assert "privacy" in text
