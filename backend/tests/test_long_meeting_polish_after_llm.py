from app.jobs.process_meeting import _apply_long_meeting_final_polish_after_llm


def _long_transcript() -> str:
    filler = (
        "The section reviewed upload reliability, transcript completeness, worker timeout behavior, "
        "support expectations, and long recording quality. "
    ) * 700

    return " ".join(
        [
            "The goal is to review 3-hour recording support, processing reliability, upload expectations, and long-recording quality.",
            filler,
            "There is a risk that exposing 3-hour support publicly too early creates failure, cost, and expectation risk.",
            "There is a risk that exposing 3-hour support publicly creates failure, cost, and expectation risk.",
            "A partial transcript may look complete, but mislaid decisions and actions.",
            "Sarah will write support copy for long recording upload expectations by Tuesday.",
        ]
    )


def _llm_polished_bad_notes() -> dict[str, object]:
    return {
        "summary": (
            "Discuss ProPilot's main priorities and next steps. "
            "Alignment on key priorities and subsequent actions"
        ),
        "summary_slots": {
            "purpose": "Discuss ProPilot's main priorities and next steps",
            "outcome": "Alignment on key priorities and subsequent actions",
            "risks": [
                "Exposing 3-hour support publicly too early creates failure, cost, and expectation risk",
                "Exposing 3-hour support publicly creates failure, cost, and expectation risk.",
                "Large video files may upload, but fail later, because of memory, or timeout limits.",
            ],
            "next_steps": [
                "Update the goal statement by Friday.",
                "Write support copy for long recording upload expectations by Tuesday.",
            ],
        },
        "key_points": [
            "Determining the maximum file size for ProPilot users",
            "Testing Meet IQ with a synthetic three-hour meeting recording",
        ],
        "decisions": [],
        "action_items": [
            "Priya — Update the goal statement by Friday",
            "Sarah — Write support copy for long recording upload expectations by Tuesday",
        ],
        "action_item_objects": [
            {
                "owner": "Priya",
                "task": "Update the goal statement by Friday",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Sarah",
                "task": "Write support copy for long recording upload expectations by Tuesday",
                "status": "open",
                "priority": "medium",
            },
        ],
    }


def test_final_long_meeting_polish_runs_after_llm_output():
    result = _apply_long_meeting_final_polish_after_llm(
        _llm_polished_bad_notes(),
        transcript_text=_long_transcript(),
    )

    slots = result["summary_slots"]
    assert isinstance(slots, dict)

    purpose = str(slots["purpose"]).lower()
    outcome = str(slots["outcome"]).lower()
    risks = [str(item).lower() for item in slots["risks"]]
    joined_risks = " ".join(risks)

    assert "3-hour" in purpose or "3 hour" in purpose
    assert "processing reliability" in purpose
    assert "upload expectations" in purpose

    assert "pro pilot" in outcome
    assert "quality review" in outcome

    assert joined_risks.count("exposing 3-hour support publicly") <= 1
    assert "mislaid decisions" not in joined_risks
    assert "miss decisions and actions" in joined_risks

    assert len(result["key_points"]) >= 6

    assert result["action_item_objects"] == _llm_polished_bad_notes()["action_item_objects"]
    assert slots["next_steps"] == _llm_polished_bad_notes()["summary_slots"]["next_steps"]


def test_final_long_meeting_polish_does_not_touch_short_notes():
    notes = _llm_polished_bad_notes()
    original_summary = notes["summary"]

    result = _apply_long_meeting_final_polish_after_llm(
        notes,
        transcript_text="Short meeting about demo planning.",
    )

    assert result["summary"] == original_summary
