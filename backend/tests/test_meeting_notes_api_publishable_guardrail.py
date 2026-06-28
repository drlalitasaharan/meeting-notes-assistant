from __future__ import annotations

from types import SimpleNamespace

from app.routers.meeting_notes_api import _publishable_action_payload


def test_v3_publishable_guardrail_filters_frontend_and_markdown_actions() -> None:
    notes = SimpleNamespace(
        model_version="local-summary-v3",
        summary_slots={
            "next_steps": [
                "Prepare basic pilot outreach assets for the first pilot audience.",
                "I'd like us to leave this meeting with a clear decision on the target audience.",
                "If we say it's designed for consultants, agencies, founders, and small teams who want fast and structured meeting notes, that's much more specific and stronger.",
                "The main purpose of today's meeting is to review where we are with the meeting notes assistant demo.",
                "The live demo will use a short and clean file, while capability testing will use a separate 10-minute audio sample.",
                "This week's priority is to validate the 10-minute audio flow and prepare basic pilot outreach assets.",
            ],
        },
        action_item_objects=[
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
                "task": "I'd us to leave this meeting with a clear",
            },
            {
                "owner": "Team",
                "task": "If we say it's designed for consultants, agencies, founders, and small teams who want fast and structured meeting notes, that's much more specific and stronger",
            },
            {
                "owner": "Team",
                "task": "The main purpose of today's meeting is to review where we are with the meeting notes assistant demo",
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
        action_items=[
            "Team — Prepare basic pilot outreach assets for the first pilot audience",
            "Team — Prepare basic pilot outreach assets",
            "Team — I'd us to leave this meeting with a clear",
            "Team — If we say it's designed for consultants, agencies, founders, and small teams who want fast and structured meeting notes, that's much more specific and stronger",
            "Team — The main purpose of today's meeting is to review where we are with the meeting notes assistant demo",
            "Team — The live demo will use a short and clean file, while capability testing will use a separate 10-minute audio sample",
            "Team — This week's priority is to validate the 10-minute audio flow and prepare basic pilot outreach assets",
        ],
    )

    payload = _publishable_action_payload(notes, notes.summary_slots)

    action_items_text = " ".join(payload["action_items"]).lower()
    action_objects_text = " ".join(item["task"].lower() for item in payload["action_item_objects"])
    next_steps_text = " ".join(payload["summary_slots"]["next_steps"]).lower()

    for text in (action_items_text, action_objects_text, next_steps_text):
        assert "prepare basic pilot outreach assets" in text

        assert "i'd us to leave this meeting" not in text
        assert "i'd like us to leave this meeting" not in text
        assert "if we say it's designed for consultants" not in text
        assert "the main purpose of today's meeting" not in text
        assert "the live demo will use" not in text
        assert "this week's priority is" not in text


def test_publishable_guardrail_leaves_non_v3_notes_unchanged() -> None:
    notes = SimpleNamespace(
        model_version="local-summary-v2",
        action_items=["Team — Existing v2 item"],
        action_item_objects=[],
    )

    payload = _publishable_action_payload(notes, {"next_steps": ["Keep original."]})

    assert payload["action_items"] == ["Team — Existing v2 item"]
    assert payload["summary_slots"]["next_steps"] == ["Keep original."]
