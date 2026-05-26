from app.services.persisted_action_contract import _finalize_persisted_action_contract


def test_persisted_contract_promotes_owner_markers_from_raw_transcript() -> None:
    transcript = """
    Priya. Action item for Priya. I will update the proposal language today, and send the edited version to Alex by 3pm.
    Jordan. Action item for Jordan. I will confirm pricing with finance by 11am tomorrow.
    Morgan. Action item for Morgan. I will draft the client follow-up email tomorrow afternoon with the pilot timeline, success criteria, and a proposed next meeting made.
    Priya. Action item for Priya. I will clean the demo account, and upload the approved sample meeting file by Monday morning.
    Alex. Action item for Alex. I will run the internal demo dry run on Monday afternoon, and check upload, processing, structured notes, markdown export, and unmeeting safety.
    """

    weak_action_items = [
        "Team - Update client-facing messaging to say it works best for structured business meetings and clear audio"
    ]
    weak_objects = [
        {
            "owner": "Team",
            "task": "Update client-facing messaging to say it works best for structured business meetings and clear audio",
            "due_date": None,
            "confidence": 0.68,
            "status": "open",
            "priority": "medium",
        }
    ]
    summary_slots = {
        "risks": ["Pricing confirmation may delay proposal delivery"],
        "next_steps": [],
    }

    action_items, action_objects, final_slots = _finalize_persisted_action_contract(
        weak_action_items,
        weak_objects,
        summary_slots,
        raw_transcript_text=transcript,
    )

    owners = [item["owner"] for item in action_objects]
    tasks = " | ".join(item["task"].lower() for item in action_objects)

    assert len(action_objects) >= 5
    assert "Priya" in owners
    assert "Jordan" in owners
    assert "Morgan" in owners
    assert "Alex" in owners
    assert "update the proposal language" in tasks
    assert "send the edited version to alex" in tasks
    assert "confirm pricing with finance" in tasks
    assert "draft the client follow-up email" in tasks
    assert "run the internal demo dry run" in tasks
    assert len(action_items) == len(action_objects)
    assert final_slots is not None
    assert len(final_slots["next_steps"]) >= 3
