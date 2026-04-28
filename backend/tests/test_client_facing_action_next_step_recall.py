from app.services.notes_quality_pass import _apply_client_facing_action_next_step_recall


def test_client_facing_priority_decision_becomes_action_and_next_step() -> None:
    payload = {
        "summary": "The team aligned on the pilot audience, demo flow, backup demo plan, and near-term validation and outreach priorities",
        "summary_slots": {
            "purpose": "Review the Meeting Notes Assistant demo and align on next steps for this week",
            "outcome": "The team aligned on the pilot audience, demo flow, backup demo plan, and near-term validation and outreach priorities",
            "risks": [],
            "next_steps": [
                "Begin sending pilot outreach messages and collecting feedback from early users."
            ],
        },
        "key_points": [
            "The main purpose is to confirm the pilot outreach plan and align on next steps for this week",
        ],
        "decision_objects": [
            {
                "text": "this week's priority is to validate the 10 minute audio flow and prepare basic pilot outreach assets",
                "confidence": 0.86,
            },
            {
                "text": "we will keep one backup meeting already processed before any live demo",
                "confidence": 0.86,
            },
        ],
        "action_item_objects": [
            {
                "text": "Team: Begin sending pilot outreach messages and collecting feedback from early users",
                "owner": "Team",
                "task": "Begin sending pilot outreach messages and collecting feedback from early users",
                "due_date": None,
                "status": "open",
                "priority": "medium",
                "confidence": 0.7,
            },
            {
                "text": "I Also Think We: Be careful with what we claim publicly, for example, the product does handle short files well",
                "owner": "I Also Think We",
                "task": "Be careful with what we claim publicly, for example, the product does handle short files well",
                "due_date": None,
                "status": "open",
                "priority": "medium",
                "confidence": 0.68,
            },
        ],
    }

    result = _apply_client_facing_action_next_step_recall(payload)

    actions = result["action_item_objects"]
    tasks = " ".join(item["task"].lower() for item in actions)
    next_steps = result["summary_slots"]["next_steps"]

    assert len(actions) >= 3
    assert len(next_steps) >= 3
    assert "priority" in tasks
    assert "validate the 10-minute audio flow" in tasks
    assert "backup meeting" in tasks
    assert "i also think we" not in tasks


def test_client_facing_final_sanitizer_removes_claim_warning_action() -> None:
    from app.services.notes_quality_pass import _client_facing_final_action_sanitize

    payload = {
        "summary": "The team aligned on pilot validation and outreach priorities.",
        "summary_slots": {
            "purpose": "Review the pilot demo flow.",
            "outcome": "The team aligned on pilot validation and outreach priorities.",
            "risks": [],
            "next_steps": [],
        },
        "decision_objects": [
            {
                "text": "this week's priority is to validate the 10 minute audio flow and prepare basic pilot outreach assets",
                "confidence": 0.86,
            },
            {
                "text": "we will keep one backup meeting already processed before any live demo",
                "confidence": 0.86,
            },
        ],
        "action_item_objects": [
            {
                "text": "I Also Think We: Be careful with what we claim publicly, for example, the product does handle short files well",
                "owner": "I Also Think We",
                "task": "Be careful with what we claim publicly, for example, the product does handle short files well",
                "due_date": None,
                "status": "open",
                "priority": "medium",
                "confidence": 0.68,
            },
            {
                "text": "Team: Begin sending pilot outreach messages and collecting feedback from early users",
                "owner": "Team",
                "task": "Begin sending pilot outreach messages and collecting feedback from early users",
                "due_date": None,
                "status": "open",
                "priority": "medium",
                "confidence": 0.74,
            },
        ],
        "action_items": [
            "I Also Think We - Be careful with what we claim publicly, for example, the product does handle short files well",
            "Team - Begin sending pilot outreach messages and collecting feedback from early users",
        ],
    }

    result = _client_facing_final_action_sanitize(payload)

    actions = result["action_item_objects"]
    tasks = " ".join(item["task"].lower() for item in actions)
    owners = " ".join(item["owner"].lower() for item in actions)

    assert len(actions) >= 3
    assert "i also think we" not in owners
    assert "be careful with what we claim publicly" not in tasks
    assert "validate the 10-minute audio flow" in tasks
    assert "backup meeting" in tasks
    assert len(result["summary_slots"]["next_steps"]) >= 3


def test_client_facing_final_output_sanitizer_removes_client_visible_defects() -> None:
    from app.services.notes_quality_pass import _client_facing_final_output_sanitize

    payload = {
        "summary": "I'd us to leave this meeting with a clear decision.",
        "summary_slots": {
            "purpose": "I'd us to leave this meeting with a clear decision.",
            "outcome": "The team aligned on the pilot audience.",
            "risks": [],
            "next_steps": [],
        },
        "key_points": [
            "I also think we should be careful with what we claim publicly, for example, the product does handle short files well.",
            "The main purpose of today's meeting is to review the demo and pilot outreach plan.",
        ],
        "decision_objects": [
            {
                "text": "the first pilot audience will be consultants, agencies, founders, and small teams",
                "confidence": 0.86,
            },
            {
                "text": "on the target audience, a finalized plan for the demo flow, and concrete owners for the follow-up actions",
                "confidence": 0.86,
            },
        ],
    }

    result = _client_facing_final_output_sanitize(payload)

    assert "I'd like us" in result["summary"]
    assert "I'd us" not in result["summary"]
    assert result["summary"].startswith("I'd like us")
    assert "The team aligned on the pilot audience" in result["summary"]
    assert "I'd like us" in result["summary_slots"]["purpose"]

    decisions = " ".join(item["text"].lower() for item in result["decision_objects"])
    key_points = " ".join(item.lower() for item in result["key_points"])

    assert "on the target audience" not in decisions
    assert "be careful with what we claim publicly" not in key_points
    assert "product does handle short files well" not in key_points


def test_notes_ai_response_summary_rebuilds_from_clean_slots() -> None:
    from app.routers.meeting_notes_api import (
        _clean_client_facing_json_slots,
        _client_facing_summary_from_slots,
    )

    stale_summary = (
        "I'd us to leave this meeting with a clear decision on the target audience. "
        "The team aligned on the pilot audience"
    )
    slots = {
        "purpose": "I'd like us to leave this meeting with a clear decision on the target audience",
        "outcome": "The team aligned on the pilot audience",
        "risks": [],
        "next_steps": ["Keep one backup meeting already processed before any live demo."],
    }

    cleaned_slots = _clean_client_facing_json_slots(slots)
    summary = _client_facing_summary_from_slots(stale_summary, cleaned_slots)

    assert cleaned_slots is not None
    assert summary is not None
    assert "I'd like us" in summary
    assert "I'd us" not in summary
    assert summary.startswith("I'd like us")
    assert "The team aligned on the pilot audience" in summary


def test_notes_ai_response_cleans_key_points() -> None:
    from app.routers.meeting_notes_api import _clean_client_facing_json_list

    key_points = [
        "I'd us to leave this meeting with a clear decision on the target audience",
        "The main purpose of today's meeting is to review the demo and pilot outreach plan.",
        "I'd us to leave this meeting with a clear decision on the target audience",
    ]

    cleaned = _clean_client_facing_json_list(key_points)

    assert len(cleaned) == 2
    assert "I'd like us" in cleaned[0]
    assert "I'd us" not in " ".join(cleaned)
