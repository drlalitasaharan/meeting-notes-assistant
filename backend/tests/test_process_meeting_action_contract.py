from app.services.persisted_action_contract import _finalize_persisted_action_contract


def test_finalizes_action_contract_from_malformed_action_object():
    cleaned_action_items, action_item_objects, summary_slots = _finalize_persisted_action_contract(
        cleaned_action_items=[],
        action_item_objects=[
            {
                "owner": "The Next Client Follow-Up",
                "task": "Be scheduled for next Tuesday after finance confirms pricing",
                "due_date": None,
                "confidence": 0.7,
                "status": "open",
                "priority": "medium",
            }
        ],
        summary_slots={
            "risks": ["Pricing confirmation may delay the client follow-up"],
            "next_steps": ["Be scheduled for next Tuesday after finance confirms pricing."],
        },
    )

    assert cleaned_action_items == [
        "Team - Schedule the client follow-up for next Tuesday after finance confirms pricing"
    ]
    assert action_item_objects == [
        {
            "text": "Team: Schedule the client follow-up for next Tuesday after finance confirms pricing",
            "owner": "Team",
            "task": "Schedule the client follow-up for next Tuesday after finance confirms pricing",
            "due_date": None,
            "confidence": 0.7,
            "status": "open",
            "priority": "medium",
        }
    ]
    assert summary_slots is not None
    assert summary_slots["next_steps"] == [
        "Schedule the client follow-up for next Tuesday after finance confirms pricing."
    ]


def test_finalizes_dedupes_and_filters_low_precision_actions():
    cleaned_action_items, action_item_objects, summary_slots = _finalize_persisted_action_contract(
        cleaned_action_items=[],
        action_item_objects=[
            {
                "owner": "Team",
                "task": "Confirm pricing with finance 11am tomorrow",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Team",
                "task": "Confirm pricing with finance by 11am tomorrow",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Team",
                "task": "Update the proposal language today",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Team",
                "task": "Send the edited version to Alex by 3pm",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Team",
                "task": "If we send the proposal flymate, the client can renew it early next week",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Team",
                "task": "Today confirm proposal scope, pricing status, demo readiness, client follow-up, risks and action items",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "We",
                "task": "Say the first month includes setup, training, one dashboard review, and standard pilot support",
                "status": "open",
                "priority": "medium",
            },
        ],
        summary_slots={"next_steps": []},
    )

    assert [item["task"] for item in action_item_objects] == [
        "Confirm pricing with finance by 11am tomorrow",
        "Update the proposal language today",
        "Send the edited version to Alex by 3pm",
        "Update client-facing messaging to say the first month includes setup, training, one dashboard review, and standard pilot support",
    ]

    assert [item["owner"] for item in action_item_objects] == [
        "Team",
        "Team",
        "Team",
        "Team",
    ]

    assert cleaned_action_items == [
        "Team - Confirm pricing with finance by 11am tomorrow",
        "Team - Update the proposal language today",
        "Team - Send the edited version to Alex by 3pm",
        "Team - Update client-facing messaging to say the first month includes setup, training, one dashboard review, and standard pilot support",
    ]

    assert summary_slots is not None
    assert summary_slots["next_steps"] == [
        "Confirm pricing with finance by 11am tomorrow.",
        "Update the proposal language today.",
        "Send the edited version to Alex by 3pm.",
        "Update client-facing messaging to say the first month includes setup, training, one dashboard review, and standard pilot support.",
    ]


def test_finalizes_dedupes_malformed_legacy_followup_string():
    cleaned_action_items, action_item_objects, summary_slots = _finalize_persisted_action_contract(
        cleaned_action_items=[
            "Team - Schedule the client follow-up for next Tuesday after finance confirms pricing",
            "The Next Client Follow-Up - Be scheduled for next Tuesday after finance confirms pricing",
        ],
        action_item_objects=[
            {
                "owner": "Team",
                "task": "Schedule the client follow-up for next Tuesday after finance confirms pricing",
                "status": "open",
                "priority": "medium",
            }
        ],
        summary_slots={"next_steps": []},
    )

    assert cleaned_action_items == [
        "Team - Schedule the client follow-up for next Tuesday after finance confirms pricing"
    ]
    assert [item["owner"] for item in action_item_objects] == ["Team"]
    assert [item["task"] for item in action_item_objects] == [
        "Schedule the client follow-up for next Tuesday after finance confirms pricing"
    ]
    assert summary_slots is not None
    assert summary_slots["next_steps"] == [
        "Schedule the client follow-up for next Tuesday after finance confirms pricing."
    ]


def test_finalizes_filters_30min_transcript_leakage_actions():
    cleaned_action_items, action_item_objects, summary_slots = _finalize_persisted_action_contract(
        cleaned_action_items=[],
        action_item_objects=[
            {
                "owner": "Priya",
                "task": "Update the proposal language today",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Priya",
                "task": "Send the edited version to Alex by 3pm. Jordan. Pricing is still pending final finance approval. Alex. Risk 1. Pricing confirmation may delay proposal delivery. Medication. Jordan will request finance approval by 11am tomorrow",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Jordan",
                "task": "Confirm pricing with finance by 11am tomorrow. Priya. For the client follow-up email, I recommend pre-sections. Pilot scope, expected timeline, and success criteria. Alex. Decision 2. The client follow-up email will include pilot scope, timeline, and success criteria",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Morgan",
                "task": "Last the client follow-up email tomorrow afternoon with the pilot timeline, success criteria, and a proposed next meeting made. Priya. Tuesday is the best target for a follow-up meeting. Alex. Decision 3. We will target next Tuesday",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Priya",
                "task": "Upload the approved sample meeting file by Monday morning. Jordan. We should run one internal dry run before the client call. Test upload, processing, note generation, markdown export, and copy behavior",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Alex",
                "task": "Check upload, processing, structured notes, markdown export, and unmeeting safety. Priya. The product message should be simple. Jordan. We should also say it works best for structured business meetings",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Morgan",
                "task": "Laugh to short onboarding note with upload guidance, including clear audio, structured meeting format, and expected output. Alex. Final recap. We decided on phase 2 custom reporting. Thanks everyone. You You You You",
                "status": "open",
                "priority": "medium",
            },
        ],
        summary_slots={"next_steps": []},
    )

    tasks = [item["task"] for item in action_item_objects]

    assert tasks == [
        "Update the proposal language today",
        "Send the edited version to Alex by 3pm",
        "Confirm pricing with finance by 11am tomorrow",
        "Draft the client follow-up email tomorrow afternoon with the pilot timeline, success criteria, and a proposed next meeting",
        "Upload the approved sample meeting file by Monday morning",
        "Check upload, processing, structured notes, markdown export, and non-meeting safety",
        "Draft a short onboarding note with upload guidance, including clear audio, structured meeting format, and expected output",
    ]

    assert [item["owner"] for item in action_item_objects] == [
        "Priya",
        "Priya",
        "Jordan",
        "Morgan",
        "Priya",
        "Alex",
        "Morgan",
    ]

    joined = " ".join(tasks).lower()
    assert "decision 2" not in joined
    assert "risk 1" not in joined
    assert "medication" not in joined
    assert "final recap" not in joined
    assert "you you" not in joined

    assert summary_slots["next_steps"][:3] == [
        "Update the proposal language today.",
        "Send the edited version to Alex by 3pm.",
        "Confirm pricing with finance by 11am tomorrow.",
    ]


def test_finalizes_dedupes_60min_action_variants():
    cleaned_action_items, action_item_objects, summary_slots = _finalize_persisted_action_contract(
        cleaned_action_items=[],
        action_item_objects=[
            {
                "owner": "Priya",
                "task": "Update the proposal language today",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Priya",
                "task": "Send the edited version to Alex by 3pm",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Jordan",
                "task": "Confirm pricing with finance by 11am tomorrow",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Morgan",
                "task": "Draft the client follow-up email after noon with the pilot timeline, success criteria, and a proposed next meeting",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Priya",
                "task": "Clean the demo account",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Priya",
                "task": "Clean the MMO account",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Morgan",
                "task": "Draft the client follow-up email later tomorrow afternoon with the pilot timeline, success criteria, and a proposed next meeting",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Morgan",
                "task": "Draft the client follow-up email by tomorrow afternoon with the pilot timeline, success criteria, and a proposed next meeting date",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Morgan",
                "task": "Draft the client follow-up email after more afternoon with the pilot timeline, success criteria, and a proposed next meeting",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Morgan",
                "task": "Draft a short onboarding note with upload guidance, including clear audio, structured meeting format, unexpected output",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Morgan",
                "task": "Draft a short onboarding note with upload guidance, including clear audio, structured meeting format, and expected output",
                "status": "open",
                "priority": "medium",
            },
        ],
        summary_slots={"next_steps": []},
    )

    tasks = [item["task"] for item in action_item_objects]

    assert tasks == [
        "Update the proposal language today",
        "Send the edited version to Alex by 3pm",
        "Confirm pricing with finance by 11am tomorrow",
        "Draft the client follow-up email by tomorrow afternoon with the pilot timeline, success criteria, and a proposed next meeting date",
        "Clean the demo account",
        "Draft a short onboarding note with upload guidance, including clear audio, structured meeting format, and expected output",
    ]

    assert [item["owner"] for item in action_item_objects] == [
        "Priya",
        "Priya",
        "Jordan",
        "Morgan",
        "Priya",
        "Morgan",
    ]

    joined = " ".join([*tasks, *cleaned_action_items, *summary_slots["next_steps"]]).lower()

    assert "mmo account" not in joined
    assert "unexpected output" not in joined
    assert "after more afternoon" not in joined
    assert joined.count("draft the client follow-up email") == 3
