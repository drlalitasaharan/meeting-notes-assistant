from app.services.action_cleanup_pass import apply_deterministic_action_cleanup
from app.services.note_strategies.local_summary import (
    _extract_embedded_decisions,
    _looks_like_publishable_decision,
    _publishable_slot_text,
)


def test_meeting81_action_cleanup_removes_non_action_fragments():
    raw_actions = [
        "Keep one primary backup demo example ready before the live client presentation.",
        "Team - Concrete owners for the follow-up actions.",
        "Concrete owners for the follow-up actions.",
        "Create the script file directly in the project folder.",
    ]

    cleaned_lines, action_objects = apply_deterministic_action_cleanup(raw_actions, [])

    cleaned_text = " ".join(cleaned_lines).lower()
    object_tasks = " ".join(str(item.get("task", "")) for item in action_objects).lower()

    assert "concrete owners for the follow-up actions" not in cleaned_text
    assert "concrete owners for the follow-up actions" not in object_tasks

    assert (
        "Keep one primary backup demo example ready before the live client presentation."
        in cleaned_lines
    )


def test_meeting81_slot_guard_rejects_giant_transcript_chunk():
    giant_chunk = """
    Speaker One, let's talk about the user facing message. decision one, the first pilot audience
    will be consultants, agencies, founders, and small teams, decision two, the live demo will use
    a short and clean file, while capability testing will use a separate 10 minute audio sample,
    decision three, we will keep one backup meeting already processed before any live demo,
    decision four, this week's priority is to validate the 10 minute audio flow and prepare basic
    pilot outreach assets, speaker two, that sounds final to me.
    """

    assert _publishable_slot_text(giant_chunk, max_chars=220) == ""


def test_meeting81_embedded_decisions_are_extracted_as_short_bullets():
    transcript_chunk = """
    Speaker One, all right, let's lock the decisions, decision one, the first pilot audience
    will be consultants, agencies, founders, and small teams, decision two, the live demo will use
    a short and clean file, while capability testing will use a separate 10 minute audio sample,
    decision three, we will keep one backup meeting already processed before any live demo,
    decision four, this week's priority is to validate the 10 minute audio flow and prepare basic
    pilot outreach assets, speaker two, that sounds final to me.
    """

    decisions = _extract_embedded_decisions(transcript_chunk)

    assert len(decisions) == 4
    assert all(_looks_like_publishable_decision(item) for item in decisions)

    joined = " ".join(decisions).lower()

    assert "first pilot audience" in joined
    assert "live demo will use a short and clean file" in joined
    assert "backup meeting already processed before any live demo" in joined
    assert "validate the 10 minute audio flow" in joined

    assert "speaker one" not in joined
    assert "speaker two" not in joined
