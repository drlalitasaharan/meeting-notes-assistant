from app.services.quality_engine_v3 import (
    apply_quality_engine_v3,
    render_quality_engine_v3_markdown,
    run_quality_engine_v3,
)

A10MINS_TRANSCRIPT = """
I'd like us to leave this meeting with a clear decision on the target audience.
The main purpose of today's meeting is to finalize the demo flow.
The first pilot audience will be consultants, agencies, founders, and small teams.
Lalita will create the clean 10-minute audio test and run it through the product today.
Lalita will prepare the short live demo file and keep one backup processed meeting ready.
If we say it's designed for consultants, we should be careful about the promise.
The live demo will use a short prepared recording.
Do we want to support 3-hour recordings now or later?
"""


def _base_notes() -> dict:
    return {
        "summary": "The team discussed target audience, demo flow, and pilot readiness.",
        "summary_slots": {
            "purpose": "",
            "outcome": "",
            "risks": [],
            "open_questions": [],
            "next_steps": [],
        },
        "action_item_objects": [],
        "decision_objects": [],
    }


def test_qev3_rejects_a10mins_fake_actions_and_keeps_real_actions() -> None:
    improved = apply_quality_engine_v3(_base_notes(), A10MINS_TRANSCRIPT)

    actions = improved["action_item_objects"]
    action_text = " ".join(action["task"] for action in actions).lower()

    assert "create the clean 10-minute audio test" in action_text
    assert "prepare the short live demo file" in action_text

    assert "leave this meeting" not in action_text
    assert "main purpose" not in action_text
    assert "if we say" not in action_text
    assert "live demo will use" not in action_text
    assert "first pilot audience" not in action_text


def test_qev3_places_a10mins_decisions_outside_actions() -> None:
    improved = apply_quality_engine_v3(_base_notes(), A10MINS_TRANSCRIPT)

    decisions = improved["decision_objects"]
    decision_text = " ".join(decision["text"] for decision in decisions).lower()
    action_text = " ".join(action["task"] for action in improved["action_item_objects"]).lower()

    assert "first pilot audience" in decision_text
    assert "live demo will use" in decision_text

    assert "first pilot audience" not in action_text
    assert "live demo will use" not in action_text


def test_qev3_extracts_risks_and_open_questions() -> None:
    improved = apply_quality_engine_v3(_base_notes(), A10MINS_TRANSCRIPT)
    slots = improved["summary_slots"]

    risks = " ".join(slots["risks"]).lower()
    open_questions = " ".join(slots["open_questions"]).lower()

    assert "careful about the promise" in risks
    assert "3-hour recordings" in open_questions


def test_qev3_owner_and_deadline_cleanup() -> None:
    improved = apply_quality_engine_v3(_base_notes(), A10MINS_TRANSCRIPT)

    actions = improved["action_item_objects"]

    create_action = next(
        action
        for action in actions
        if "create the clean 10-minute audio test" in action["task"].lower()
    )
    demo_action = next(
        action for action in actions if "prepare the short live demo file" in action["task"].lower()
    )

    assert create_action["owner"] == "Lalita"
    assert create_action["deadline"] == "today"
    assert demo_action["owner"] == "Lalita"


def test_qev3_removes_invalid_existing_actions() -> None:
    notes = _base_notes()
    notes["action_item_objects"] = [
        {
            "owner": "Team",
            "task": "I'd like us to leave this meeting with a clear decision on the target audience.",
        },
        {
            "owner": "Lalita",
            "task": "Create the clean 10-minute audio test today.",
        },
    ]

    improved = apply_quality_engine_v3(notes, A10MINS_TRANSCRIPT)

    action_text = " ".join(action["task"] for action in improved["action_item_objects"]).lower()

    assert "leave this meeting" not in action_text
    assert "create the clean 10-minute audio test" in action_text


def test_qev3_run_mode_is_safe_when_not_v3() -> None:
    notes = _base_notes()

    result = run_quality_engine_v3(notes, A10MINS_TRANSCRIPT, mode="v1")

    assert result["notes"] == notes
    assert result["metadata"]["applied"] is False
    assert result["metadata"]["engine"] == "qev3"


def test_qev3_run_mode_applies_v3() -> None:
    result = run_quality_engine_v3(_base_notes(), A10MINS_TRANSCRIPT, mode="v3")

    assert result["metadata"]["applied"] is True
    assert result["metadata"]["mode"] == "v3"
    assert result["notes"]["action_item_objects"]


def test_qev3_markdown_renders_commercial_sections() -> None:
    improved = apply_quality_engine_v3(_base_notes(), A10MINS_TRANSCRIPT)
    markdown = render_quality_engine_v3_markdown(improved)

    assert "# Meeting Notes" in markdown
    assert "## Executive Summary" in markdown
    assert "## Key Decisions" in markdown
    assert "## Action Items" in markdown
    assert "## Risks / Concerns" in markdown
    assert "## Open Questions" in markdown
    assert "| Owner | Action | Deadline |" in markdown
