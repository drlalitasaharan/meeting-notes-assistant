from __future__ import annotations

from app.services.persisted_action_contract import align_action_items_with_objects
from app.services.quality_engine_v3 import finalize_quality_engine_v3_persisted_notes


def test_qev3_final_persistence_syncs_frontend_and_markdown_action_sources() -> None:
    notes = {
        "summary_slots": {
            "next_steps": [
                "Prepare basic pilot outreach assets for the first pilot audience.",
                "I'd like us to leave this meeting with a clear decision on the target audience.",
                "If we say it's designed for consultants, agencies, founders, and small teams who want fast and structured meeting notes, that's much more specific and stronger.",
                "The main purpose of today's meeting is to review where we are with the meeting notes assistant demo.",
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
                "task": "I'd like us to leave this meeting with a clear decision on the target audience",
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
                "owner": "Lalita",
                "task": "Create the clean 10-minute audio test and run it through the product today",
            },
        ],
        "action_items": [
            "Team — Prepare basic pilot outreach assets for the first pilot audience",
            "Team — I'd like us to leave this meeting with a clear decision on the target audience",
            "Team — If we say it's designed for consultants, agencies, founders, and small teams who want fast and structured meeting notes, that's much more specific and stronger",
            "Team — The main purpose of today's meeting is to review where we are with the meeting notes assistant demo",
            "Team — The live demo will use a short and clean file, while capability testing will use a separate 10-minute audio sample",
            "Lalita — Create the clean 10-minute audio test and run it through the product today",
        ],
    }

    finalized = finalize_quality_engine_v3_persisted_notes(notes)

    frontend_action_items = align_action_items_with_objects(
        [],
        finalized.get("action_item_objects") or [],
    )

    markdown_action_text = " ".join(
        str(item.get("task") or "")
        for item in finalized.get("action_item_objects", [])
        if isinstance(item, dict)
    ).lower()
    frontend_action_text = " ".join(frontend_action_items).lower()
    next_steps_text = " ".join(finalized.get("summary_slots", {}).get("next_steps", [])).lower()

    for text in (markdown_action_text, frontend_action_text, next_steps_text):
        assert "prepare basic pilot outreach assets" in text
        assert "create the clean 10-minute audio test" in text

        assert "i'd like us to leave this meeting" not in text
        assert "if we say it's designed for consultants" not in text
        assert "the main purpose of today's meeting" not in text
        assert "the live demo will use" not in text
        assert "this week's priority is" not in text
