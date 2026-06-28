from __future__ import annotations

from app.services.quality_engine_v3 import run_quality_engine_v3


def _action_texts(notes: dict) -> list[str]:
    return [
        str(item.get("task") or item.get("action") or item.get("text") or "")
        for item in notes.get("action_item_objects", [])
        if isinstance(item, dict)
    ]


def test_qev3_keeps_valid_live_demo_preparation_action() -> None:
    notes = {
        "action_item_objects": [
            {
                "owner": "Lalita",
                "task": "Prepare the short live demo file",
            }
        ],
        "summary_slots": {
            "next_steps": ["Prepare the short live demo file."],
        },
    }

    result = run_quality_engine_v3(notes, "", mode="v3")
    output = result["notes"]
    action_texts = _action_texts(output)

    assert "Prepare the short live demo file" in action_texts
    next_steps_text = " ".join(output.get("summary_slots", {}).get("next_steps", []))
    assert "Prepare the short live demo file" in next_steps_text


def test_qev3_filters_a10mins_summary_sentences_from_actions() -> None:
    notes = {
        "summary": (
            "I'd like us to leave this meeting with a clear decision on the target audience, "
            "a finalized plan for the demo flow, and concrete owners for the follow-up actions. "
            "The team aligned on the pilot audience, demo flow, backup demo plan, and near-term "
            "validation and outreach priorities."
        ),
        "summary_slots": {
            "purpose": (
                "I'd like us to leave this meeting with a clear decision on the target audience, "
                "a finalized plan for the demo flow, and concrete owners for the follow-up actions"
            ),
            "outcome": (
                "The team aligned on the pilot audience, demo flow, backup demo plan, and "
                "near-term validation and outreach priorities"
            ),
            "risks": [],
            "open_questions": [],
            "next_steps": [
                "Prepare basic pilot outreach assets for the first pilot audience.",
                "I'd like us to leave this meeting with a clear decision on the target audience.",
                "If we say it's designed for consultants, agencies, founders, and small teams who want fast and structured meeting notes, that's much more specific and stronger.",
                "The main purpose of today's meeting is to review where we are with the meeting notes assistant demo, confirm the pilot outreach plan, discuss a few open issues, and align on next steps for this week.",
                "The live demo will use a short and clean file, while capability testing will use a separate 10-minute audio sample.",
                "This week's priority is to validate the 10-minute audio flow and prepare basic pilot outreach assets.",
            ],
        },
        "action_item_objects": [
            {
                "owner": "Team",
                "task": "Prepare basic pilot outreach assets for the first pilot audience",
            },
            {
                "owner": "Team",
                "task": "Prepare basic pilot outreach assets",
            },
            {
                "owner": "Team",
                "task": "I'd like us to leave this meeting with a clear decision on the target audience, a finalized plan for the demo flow, and concrete owners for the follow-up actions",
            },
            {
                "owner": "Team",
                "task": "If we say it's designed for consultants, agencies, founders, and small teams who want fast and structured meeting notes, that's much more specific and stronger",
            },
            {
                "owner": "Team",
                "task": "The main purpose of today's meeting is to review where we are with the meeting notes assistant demo, confirm the pilot outreach plan, discuss a few open issues, and align on next steps for this week",
            },
            {
                "owner": "Team",
                "task": "The live demo will use a short and clean file, while capability testing will use a separate 10-minute audio sample",
            },
            {
                "owner": "Team",
                "task": "This week's priority is to validate the 10-minute audio flow and prepare basic pilot outreach assets",
            },
        ],
        "decision_objects": [
            {
                "text": "The first pilot audience will be consultants, agencies, founders, and small teams.",
            },
            {
                "text": "The live demo will use a short and clean file, while capability testing will use a separate 10-minute audio sample.",
            },
        ],
    }

    transcript = """
    I'd like us to leave this meeting with a clear decision on the target audience, a finalized
    plan for the demo flow, and concrete owners for the follow-up actions.
    If we say it's designed for consultants, agencies, founders, and small teams who want fast
    and structured meeting notes, that's much more specific and stronger.
    The main purpose of today's meeting is to review where we are with the meeting notes assistant
    demo, confirm the pilot outreach plan, discuss a few open issues, and align on next steps for this week.
    Decision: the first pilot audience will be consultants, agencies, founders, and small teams.
    Decision: the live demo will use a short and clean file, while capability testing will use a separate
    10-minute audio sample.
    Action: prepare basic pilot outreach assets for the first pilot audience.
    Action: prepare basic pilot outreach assets.
    """

    result = run_quality_engine_v3(notes, transcript, mode="v3")
    output = result["notes"]

    action_texts = _action_texts(output)
    joined_actions = " ".join(action_texts).lower()

    assert "Prepare basic pilot outreach assets for the first pilot audience" in action_texts
    assert "Prepare basic pilot outreach assets" in action_texts

    assert "i'd like us to leave this meeting" not in joined_actions
    assert "if we say it's designed for consultants" not in joined_actions
    assert "the main purpose of today's meeting" not in joined_actions
    assert "the live demo will use" not in joined_actions
    assert "this week's priority is" not in joined_actions

    next_steps = " ".join(output.get("summary_slots", {}).get("next_steps", [])).lower()
    assert "prepare basic pilot outreach assets" in next_steps
    assert "i'd like us to leave this meeting" not in next_steps
    assert "if we say it's designed for consultants" not in next_steps
    assert "the main purpose of today's meeting" not in next_steps
