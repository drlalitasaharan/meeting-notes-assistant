from __future__ import annotations

from app.services.quality_engine_v3 import run_quality_engine_v3


def _a10mins_notes() -> dict[str, object]:
    return {
        "summary": (
            "I'd like us to leave this meeting with a clear decision on the target audience, "
            "a finalized plan for the demo flow, and concrete owners for the follow-up actions. "
            "The team aligned on the pilot audience, demo flow, backup demo plan, and near-term "
            "validation and outreach priorities"
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
            "next_steps": [
                "Prepare basic pilot outreach assets for the first pilot audience.",
                "Prepare basic pilot outreach assets.",
            ],
        },
        "key_points": [
            (
                "I'd like us to leave this meeting with a clear decision on the target audience, "
                "a finalized plan for the demo flow, and concrete owners for the follow-up actions"
            ),
            (
                "If we say it's designed for consultants, agencies, founders, and small teams "
                "who want fast and structured meeting notes, that's much more specific and stronger"
            ),
            (
                "The main purpose of today's meeting is to review where we are with the meeting "
                "notes assistant demo, confirm the pilot outreach plan, discuss a few open issues, "
                "and align on next steps for this week"
            ),
            "A short demo video, a simple landing page, and a concise message would be enough to start",
            "Sixth, if the output is good, preserve that processed meeting as the backup demo asset",
            (
                "Even if you already know the workflow, having it written down makes the demo "
                "feel much calmer and more professional"
            ),
        ],
        "decisions": [
            "the first pilot audience will be consultants, agencies, founders, and small teams",
            (
                "the live demo will use a short and clean file, while capability testing will use "
                "a separate 10-minute audio sample"
            ),
            "we will keep one backup meeting already processed before any live demo",
            (
                "this week's priority is to validate the 10-minute audio flow and prepare basic "
                "pilot outreach assets"
            ),
        ],
        "decision_objects": [
            {
                "text": "the first pilot audience will be consultants, agencies, founders, and small teams"
            },
            {
                "text": (
                    "the live demo will use a short and clean file, while capability testing will "
                    "use a separate 10-minute audio sample"
                )
            },
            {"text": "we will keep one backup meeting already processed before any live demo"},
            {
                "text": (
                    "this week's priority is to validate the 10-minute audio flow and prepare basic "
                    "pilot outreach assets"
                )
            },
        ],
        "action_items": [
            "Team — Prepare basic pilot outreach assets for the first pilot audience",
            "Team — Prepare basic pilot outreach assets",
        ],
        "action_item_objects": [
            {
                "owner": "Team",
                "task": "Prepare basic pilot outreach assets for the first pilot audience",
            },
            {"owner": "Team", "task": "Prepare basic pilot outreach assets"},
        ],
    }


def test_qev3d_key_points_remove_purpose_context_and_section_overlap(monkeypatch) -> None:
    monkeypatch.setenv("MEETIQ_QEV3D_SECTION_SEPARATION", "true")

    result = run_quality_engine_v3(_a10mins_notes(), "", mode="v3")
    notes = result["notes"]

    key_points_text = " ".join(notes.get("key_points", [])).lower()

    assert "i'd like us to leave this meeting" not in key_points_text
    assert "if we say it's designed for consultants" not in key_points_text
    assert "the main purpose of today's meeting" not in key_points_text
    assert "the live demo will use" not in key_points_text
    assert "this week's priority is" not in key_points_text

    assert "short demo video" in key_points_text
    assert "simple landing page" in key_points_text
    assert "backup demo asset" in key_points_text
    assert "demo feel much calmer" in key_points_text

    action_text = " ".join(
        str(item.get("task") or "")
        for item in notes.get("action_item_objects", [])
        if isinstance(item, dict)
    ).lower()
    assert "prepare basic pilot outreach assets" in action_text

    next_steps_text = " ".join(notes.get("summary_slots", {}).get("next_steps", [])).lower()
    assert "prepare basic pilot outreach assets" in next_steps_text


def test_qev3d_key_points_flag_off_preserves_existing_v3_behavior(monkeypatch) -> None:
    monkeypatch.delenv("MEETIQ_QEV3D_SECTION_SEPARATION", raising=False)

    result = run_quality_engine_v3(_a10mins_notes(), "", mode="v3")
    notes = result["notes"]

    key_points_text = " ".join(notes.get("key_points", [])).lower()

    assert "i'd like us to leave this meeting" in key_points_text
    assert "the main purpose of today's meeting" in key_points_text
