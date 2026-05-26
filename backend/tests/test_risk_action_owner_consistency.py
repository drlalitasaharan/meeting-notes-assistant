from app.services.notes_pipeline.consistency import apply_risk_action_owner_consistency


def test_filters_agenda_text_from_risks_and_keeps_real_risks():
    notes = {
        "risks": [
            "Today we need to confirm proposal scope, pricing status, demo readiness, client follow-up, risks, and action items",
            "The demo should show the workflow clearly, upload meeting recording, wait for processing, review summary decisions risks, and action items",
            "Pricing confirmation may delay the client follow-up",
            "Over-promising custom reporting may create unrealistic client expectations",
        ],
        "action_items": [],
        "key_points": [],
        "decisions": [],
        "next_steps": [],
    }

    result = apply_risk_action_owner_consistency(notes)

    assert result["risks"] == [
        "Pricing confirmation may delay the client follow-up",
        "Over-promising custom reporting may create unrealistic client expectations",
    ]


def test_promotes_actions_from_next_steps_key_points_and_decisions():
    notes = {
        "risks": [],
        "action_items": [
            {"owner": "Team", "task": "Update the proposal language today"},
        ],
        "next_steps": [
            "Confirm pricing with finance by 11am tomorrow.",
        ],
        "key_points": [
            "I will draft the client follow-up email tomorrow afternoon with the pilot timeline, success criteria, and a proposed next meeting",
            "Key action owners are Priya for proposal and demo cleanup, Jordan for pricing, Morgan for client email and onboarding guidance, and Alex for final review and dry run",
        ],
        "decisions": [
            "We should remove old test files and upload one approved sample meeting before the client call",
            "I will clean the demo account and upload the approved sample meeting file by Monday morning",
        ],
    }

    result = apply_risk_action_owner_consistency(notes)
    tasks = [item["task"] for item in result["action_items"]]

    assert "Confirm pricing with finance by 11am tomorrow" in tasks
    assert "Update the proposal language today" in tasks
    assert (
        "Draft the client follow-up email tomorrow afternoon with the pilot timeline, success criteria, and a proposed next meeting"
        in tasks
    )
    assert (
        "Remove old test files and upload one approved sample meeting before the client call"
        in tasks
    )
    assert (
        "Clean the demo account and upload the approved sample meeting file by Monday morning"
        in tasks
    )


def test_infers_owners_from_generic_owner_hints():
    notes = {
        "risks": [],
        "action_items": [
            {"owner": "Team", "task": "Confirm pricing with finance by 11am tomorrow"},
            {"owner": "Team", "task": "Update the proposal language today"},
            {"owner": "Team", "task": "Draft the client follow-up email tomorrow afternoon"},
            {"owner": "Team", "task": "Complete final review and dry run"},
        ],
        "key_points": [
            "Key action owners are Priya for proposal and demo cleanup, Jordan for pricing, Morgan for client email and onboarding guidance, and Alex for final review and dry run",
        ],
        "decisions": [],
        "next_steps": [],
    }

    result = apply_risk_action_owner_consistency(notes)
    owner_by_task = {item["task"]: item["owner"] for item in result["action_items"]}

    assert owner_by_task["Confirm pricing with finance by 11am tomorrow"] == "Jordan"
    assert owner_by_task["Update the proposal language today"] == "Priya"
    assert owner_by_task["Draft the client follow-up email tomorrow afternoon"] == "Morgan"
    assert owner_by_task["Complete final review and dry run"] == "Alex"


def test_dedupes_near_duplicate_pricing_actions():
    notes = {
        "risks": [],
        "action_items": [
            {"owner": "Team", "task": "Confirm pricing with finance 11am tomorrow"},
            {"owner": "Team", "task": "Confirm pricing with finance by 11am tomorrow"},
        ],
        "key_points": [],
        "decisions": [],
        "next_steps": [],
    }

    result = apply_risk_action_owner_consistency(notes)
    tasks = [item["task"] for item in result["action_items"]]

    assert len(tasks) == 1
    assert "Confirm pricing with finance" in tasks[0]


def test_infers_high_confidence_risks_when_bad_risks_are_removed():
    notes = {
        "summary": "Custom reporting will stay out of the first month and will be positioned as phase two.",
        "risks": [
            "Today we need to confirm proposal scope, pricing status, demo readiness, client follow-up, risks, and action items",
        ],
        "action_items": [
            {"owner": "Team", "task": "Confirm pricing with finance by 11am tomorrow"},
        ],
        "key_points": [
            "We should remove old test files and upload one approved sample meeting before the client call",
        ],
        "decisions": [],
        "next_steps": [],
    }

    result = apply_risk_action_owner_consistency(notes)

    assert "Pricing confirmation may delay the client follow-up" in result["risks"]
    assert (
        "Old test files or an unprepared demo account may reduce client confidence"
        in result["risks"]
    )
    assert (
        "Over-promising custom reporting may create unrealistic client expectations"
        in result["risks"]
    )
