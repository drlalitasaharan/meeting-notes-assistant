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


def test_finalizes_uses_transcript_recall_when_pipeline_actions_empty():
    transcript = (
        "The team discussed a remote control and LCD screen cost. "
        "The marketing expert will post the cost information in the project mail folder. "
        "After lunch, the team will fill out the questionnaire."
    )

    cleaned_action_items, action_item_objects, summary_slots = _finalize_persisted_action_contract(
        cleaned_action_items=[],
        action_item_objects=[],
        summary_slots={"next_steps": []},
        raw_transcript_text=transcript,
    )

    joined_items = " ".join(cleaned_action_items).lower()
    joined_tasks = " ".join(str(item.get("task") or "") for item in action_item_objects).lower()

    assert "post or share lcd cost information" in joined_items
    assert "fill out the questionnaire after lunch" in joined_items
    assert "post or share lcd cost information" in joined_tasks
    assert "fill out the questionnaire after lunch" in joined_tasks
    assert summary_slots["next_steps"]


def test_restores_publishable_actions_from_recovered_objects_after_normalization():
    from app.jobs.process_meeting import _restore_publishable_actions_from_objects

    notes = {
        "summary": "Test",
        "key_points": [],
        "action_items": [],
        "summary_slots": {
            "purpose": "Test",
            "outcome": "Test",
            "risks": [],
            "next_steps": [],
        },
        "decisions": [],
        "action_item_objects": [
            {
                "owner": "Speaker C",
                "task": "Create files from delimited segments or otherwise prepare data in a form that can be merged with the annotation structure",
                "due_date": None,
                "confidence": 0.65,
                "status": "open",
                "priority": "medium",
            }
        ],
        "decision_objects": [],
    }

    restored = _restore_publishable_actions_from_objects(notes)

    assert restored["action_items"] == [
        "Speaker C - Create files from delimited segments or otherwise prepare data in a form that can be merged with the annotation structure"
    ]
    assert restored["summary_slots"]["next_steps"] == [
        "Create files from delimited segments or otherwise prepare data in a form that can be merged with the annotation structure."
    ]


def test_finalizes_uses_chunk_recovery_when_existing_actions_are_sparse():
    cleaned_action_items, action_item_objects, summary_slots = _finalize_persisted_action_contract(
        cleaned_action_items=[],
        action_item_objects=[],
        summary_slots={"next_steps": []},
        raw_transcript_text=(
            "The team discussed pricing context. "
            "Priya should review the pricing assumptions next week. "
            "The team discussed non-action background information. "
            "Jordan should send launch notes tomorrow."
        ),
    )

    joined_items = " ".join(cleaned_action_items).lower()
    joined_tasks = " ".join(str(item.get("task") or "") for item in action_item_objects).lower()

    assert "review the pricing assumptions" in joined_items
    assert "send launch notes" in joined_items
    assert "review the pricing assumptions" in joined_tasks
    assert "send launch notes" in joined_tasks

    owner_by_task = {
        str(item.get("task") or "").lower(): item.get("owner") for item in action_item_objects
    }

    assert owner_by_task["review the pricing assumptions next week"] == "Priya"
    assert owner_by_task["send launch notes tomorrow"] == "Jordan"

    assert summary_slots is not None
    assert summary_slots["next_steps"][:2] == [
        "Review the pricing assumptions next week.",
        "Send launch notes tomorrow.",
    ]


def test_finalizes_does_not_need_chunk_recovery_when_existing_actions_are_enough():
    cleaned_action_items, action_item_objects, summary_slots = _finalize_persisted_action_contract(
        cleaned_action_items=[],
        action_item_objects=[
            {"owner": "Priya", "task": "Review pricing assumptions", "status": "open"},
            {"owner": "Jordan", "task": "Send launch notes", "status": "open"},
            {"owner": "Morgan", "task": "Confirm pilot support plan", "status": "open"},
        ],
        summary_slots={"next_steps": []},
        raw_transcript_text=("Alex should investigate a separate late-meeting idea tomorrow."),
    )

    joined_tasks = " ".join(str(item.get("task") or "") for item in action_item_objects).lower()

    assert "review pricing assumptions" in joined_tasks
    assert "send launch notes" in joined_tasks
    assert "confirm pilot support plan" in joined_tasks
    assert "investigate a separate late-meeting idea" not in joined_tasks
    assert len(action_item_objects) == 3
    assert len(cleaned_action_items) == 3
    assert summary_slots is not None
