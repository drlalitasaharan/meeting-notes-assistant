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


def test_30_60min_promotes_owner_actions_and_replaces_generic_next_step():
    notes = {
        "summary": "Asia says, Asia will update the landing page onboarding copy by Friday morning, including upload, process, and review steps.",
        "summary_slots": {
            "risks": [],
            "next_steps": ["Review risks, blockers, dependencies, and uncertainties."],
        },
        "risks": [],
        "action_items": [
            {"owner": "Team", "task": "Review risks, blockers, dependencies, and uncertainties"},
        ],
        "key_points": [
            "Lina says, Asia repeated that she will send the onboarding copy tomorrow and later repeated at the landing page copy needs to go to Marco by 5 pm",
            "Sophia says, Sophia will update the support page with reviewrecommended language for long recordings before the launch post goes live",
            "Maya says, Priya, please also create two versions of LinkedIn post, one founder style, and one product style",
        ],
        "decisions": [],
        "next_steps": [],
    }

    result = apply_risk_action_owner_consistency(notes)
    owner_by_task = {item["task"]: item["owner"] for item in result["action_items"]}
    tasks_text = " ".join(owner_by_task)

    assert any("landing page onboarding copy" in task.lower() for task in owner_by_task)
    assert any(
        "support page with review recommended language" in task.lower() for task in owner_by_task
    )
    assert any("LinkedIn post" in task for task in owner_by_task)
    assert "Review risks, blockers, dependencies, and uncertainties" not in owner_by_task
    assert "Asia" in owner_by_task.values()
    assert "Sophia" in owner_by_task.values()
    assert "Priya" in owner_by_task.values()
    assert "landing page" in tasks_text
    assert "Review risks, blockers" not in " ".join(result["summary_slots"]["next_steps"])


def test_30_60min_filters_broken_decisions_and_preserves_real_decisions():
    notes = {
        "risks": [],
        "action_items": [],
        "key_points": [],
        "next_steps": [],
        "decisions": [
            "s, action items, risks, open questions, repeated actions, and vague actions that should be written",
            "risks, questions, and owners",
            "s discussed in this meeting are listed as spoken meeting content, not as a separate document",
            "Use support at a gen.ai as the public support address once the email alias is ready",
            "confirmed, starter checkout is the primary public plan for now",
        ],
    }

    result = apply_risk_action_owner_consistency(notes)

    assert result["decisions"] == [
        "Use support at Acjen AI as the public support address once the email alias is ready",
        "confirmed, starter checkout is the primary public plan for now",
    ]
    assert result["decision_objects"] == [
        {
            "text": "Use support at Acjen AI as the public support address once the email alias is ready",
            "confidence": 0.8,
        },
        {
            "text": "confirmed, starter checkout is the primary public plan for now",
            "confidence": 0.8,
        },
    ]


def test_30_60min_infers_long_recording_trust_and_reliability_risks():
    notes = {
        "summary": "The landing page and app are on different domains, so users may feel a trust gap.",
        "summary_slots": {"risks": []},
        "risks": [],
        "action_items": [],
        "key_points": [
            "Asia says, RISC, long recordings may miss some details, so important action items should be reviewed before sharing externally",
            "Maya says, the goal today is to review support operations, and reliability review, and finish with a marked decision, risks, questions, and owners",
        ],
        "decisions": [],
        "next_steps": [],
    }

    result = apply_risk_action_owner_consistency(notes)
    risk_text = " ".join(result["risks"]).lower()

    assert "long recordings may miss details" in risk_text
    assert "trust gap" in risk_text
    assert "support and reliability messaging" in risk_text
    assert result["summary_slots"]["risks"] == result["risks"]


def test_preserves_existing_strong_m03_action_objects():
    notes = {
        "risks": [],
        "action_items": [
            "Sam - Run a production smoke test for side up, checkout, upload, note generation, download, and usage tracking by noon tomorrow",
        ],
        "action_item_objects": [
            {
                "owner": "Sam",
                "task": "Run a production smoke test for side up, checkout, upload, note generation, download, and usage tracking by noon tomorrow",
            },
            {
                "owner": "Nora",
                "task": "Draft the first support macro for failed uploads and long processing by Wednesday",
            },
        ],
        "key_points": [],
        "decisions": [],
        "next_steps": [],
    }

    result = apply_risk_action_owner_consistency(notes)
    owner_by_task = {item["task"]: item["owner"] for item in result["action_items"]}

    assert (
        "Run a production smoke test for signup, checkout, upload, note generation, download, and usage tracking by noon tomorrow"
        in owner_by_task
    )
    assert (
        owner_by_task[
            "Run a production smoke test for signup, checkout, upload, note generation, download, and usage tracking by noon tomorrow"
        ]
        == "Sam"
    )
    assert (
        owner_by_task[
            "Draft the first support macro for failed uploads and long processing by Wednesday"
        ]
        == "Nora"
    )


def test_preserves_m03_actions_without_owner_prefix_duplicates_or_repeated_url_cleanup():
    notes = {
        "risks": [],
        "action_items": [
            "Sam - Run a production smoke test for signup, checkout, upload, note generation, download, and usage tracking by noon tomorrow",
            "Priya - Prepare the main list submission using the Acjen AI URL by the end of the week",
        ],
        "action_item_objects": [
            {
                "owner": "Sam",
                "task": "Run a production smoke test for signup, checkout, upload, note generation, download, and usage tracking by noon tomorrow",
            },
            {
                "owner": "Priya",
                "task": "Prepare the main list submission using the Acjen AI URL by the end of the week",
            },
        ],
        "key_points": [],
        "decisions": [],
        "next_steps": [],
    }

    result = apply_risk_action_owner_consistency(notes)
    tasks = [item["task"] for item in result["action_item_objects"]]

    assert (
        tasks.count(
            "Run a production smoke test for signup, checkout, upload, note generation, download, and usage tracking by noon tomorrow"
        )
        == 1
    )
    assert (
        tasks.count(
            "Prepare the main list submission using the Acjen AI URL by the end of the week"
        )
        == 1
    )
    assert all(not task.startswith(("Sam -", "Priya -")) for task in tasks)
    assert all("Acjen Acjen" not in task for task in tasks)


def test_30_60min_promotes_m02_landing_page_owner_actions_to_objects():
    notes = {
        "summary": "Asia says, Asia will update the landing page onboarding copy by Friday morning, including upload, process, and review steps.",
        "summary_slots": {
            "purpose": "Asia says, Asia will update the landing page onboarding copy by Friday morning, including upload, process, and review steps",
            "risks": [],
            "next_steps": ["Review risks, blockers, dependencies, and uncertainties."],
        },
        "risks": [],
        "action_items": [
            {"owner": "Team", "task": "Review risks, blockers, dependencies, and uncertainties"},
        ],
        "action_item_objects": [
            {
                "owner": "Team",
                "task": "Review risks, blockers, dependencies, and uncertainties",
            },
        ],
        "key_points": [
            "Lina says, Asia repeated that she will send the onboarding copy tomorrow and later repeated at the landing page copy needs to go to Marco by 5 pm",
        ],
        "decisions": [],
        "next_steps": [],
    }

    result = apply_risk_action_owner_consistency(notes)
    owner_by_task = {item["task"]: item["owner"] for item in result["action_item_objects"]}
    joined = " ".join(owner_by_task).lower()

    assert "update the landing page onboarding copy by friday morning" in joined
    assert "send the landing page copy to marco by 5 pm" in joined
    assert all(owner == "Asia" for owner in owner_by_task.values())
    assert "review risks" not in joined
    assert result["action_items"] == result["action_item_objects"]
    assert "review risks" not in " ".join(result["next_steps"]).lower()


def test_30_60min_promotes_m04_support_page_owner_action_to_objects():
    notes = {
        "summary": "Sophia says, Sophia will update the support page with reviewrecommended language for long recordings before the launch post goes live.",
        "summary_slots": {"risks": [], "next_steps": []},
        "risks": [],
        "action_items": [],
        "action_item_objects": [],
        "key_points": [
            "Sophia says, Sophia will update the support page with reviewrecommended language for long recordings before the launch post goes live",
        ],
        "decisions": [],
        "next_steps": [],
    }

    result = apply_risk_action_owner_consistency(notes)

    assert result["action_item_objects"] == [
        {
            "owner": "Sophia",
            "task": "Update the support page with review recommended language for long recordings before the launch post goes live",
            "status": "open",
            "priority": "medium",
        }
    ]


def test_30_60min_filters_generic_meta_actions_from_actions_and_next_steps():
    notes = {
        "risks": [],
        "action_items": [
            {
                "owner": "Team",
                "task": "The purpose is to confirm what we can launch this week and what should stay out of scope",
            },
            {
                "owner": "Team",
                "task": "For example, Sarah will send pricing and Sarah will send the approved pricing table by 5pm should become one action with the strongest wording",
            },
            {"owner": "Team", "task": "Review risks, blockers, dependencies, and uncertainties"},
        ],
        "action_item_objects": [],
        "key_points": [
            "Maya says, Priya, please also create two versions of LinkedIn post, one founder style, and one product style",
        ],
        "decisions": [],
        "next_steps": ["Review risks, blockers, dependencies, and uncertainties."],
    }

    result = apply_risk_action_owner_consistency(notes)
    joined = " ".join(item["task"] for item in result["action_item_objects"]).lower()

    assert "purpose is to confirm" not in joined
    assert "for example" not in joined
    assert "review risks" not in joined
    assert "create two versions of linkedin post" in joined
    assert "review risks" not in " ".join(result["next_steps"]).lower()


def test_30_60min_filters_instruction_and_example_decisions():
    notes = {
        "risks": [],
        "action_items": [],
        "key_points": [],
        "next_steps": [],
        "decisions": [
            "Discussion should not become a decision unless someone says we agreed, decision confirmed, approved",
            "For example, Sarah will send pricing, Sarah will send the pricing table, and Sarah will send the approved pricing table by 5pm should become one action with the strongest wording",
            "Decision confirmed: Starter checkout remains the primary public plan for now",
        ],
    }

    result = apply_risk_action_owner_consistency(notes)

    assert result["decisions"] == [
        "Decision confirmed: Starter checkout remains the primary public plan for now"
    ]


def test_30_60min_filters_goal_setting_text_from_risks():
    notes = {
        "summary": "Long recordings may miss some details and support guidance should be reviewed.",
        "summary_slots": {
            "risks": [
                "Maya says, the goal today is to review support operations, and reliability review, and finish with a marked decision, risks, questions, and owners",
            ],
        },
        "risks": [
            "Maya says, the goal today is to review support operations, and reliability review, and finish with a marked decision, risks, questions, and owners",
            "Long recordings may miss some details, so important action items should be reviewed before sharing externally",
        ],
        "action_items": [],
        "key_points": [],
        "decisions": [],
        "next_steps": [],
    }

    result = apply_risk_action_owner_consistency(notes)
    risk_text = " ".join(result["risks"]).lower()

    assert "goal today" not in risk_text
    assert "long recordings may miss" in risk_text
