from app.services.quality_engine_v3 import apply_quality_engine_v3


def _baseline_notes() -> dict:
    return {
        "summary": "The team discussed a long pilot review.",
        "summary_slots": {
            "purpose": "",
            "outcome": "",
            "risks": [],
            "open_questions": [],
            "next_steps": [],
        },
        "action_item_objects": [],
        "action_items": [],
        "decision_objects": [],
        "decisions": [],
        "key_points": [],
    }


def test_qev3_uses_beginning_middle_end_sections_for_long_transcript_actions_and_risks():
    transcript = """
Priya: Section 1: Pilot scope.
Priya: I will circulate the approved pilot pricing table by Friday.
Priya: The team confirmed the invited pilot launch scope.

Jordan: Section 2: Context only.
Jordan: This section contains background discussion without action ownership.

Jordan: Section 3: Context only.
Jordan: This section contains background discussion without action ownership.

Jordan: Section 4: Context only.
Jordan: This section contains background discussion without action ownership.

Priya: Section 5: Security review.
Alex: I will complete the storage access review by Monday.
Alex: Risk confirmed: Storage permissions may delay approval if review is not complete.

Jordan: Section 6: Context only.
Jordan: This section contains background discussion without action ownership.

Jordan: Section 7: Context only.
Jordan: This section contains background discussion without action ownership.

Jordan: Section 8: Context only.
Jordan: This section contains background discussion without action ownership.

Jordan: Section 9: Context only.
Jordan: This section contains background discussion without action ownership.

Priya: Section 10: Final recap.
Morgan: I will send the support onboarding email by Tuesday.
Priya: Decision confirmed: Support will use email for pilot users.
"""

    result = apply_quality_engine_v3(_baseline_notes(), transcript)

    action_text = " ".join(
        str(item.get("task") or item.get("action") or "")
        for item in result.get("action_item_objects", [])
        if isinstance(item, dict)
    ).lower()
    decision_text = " ".join(str(item) for item in result.get("decisions", [])).lower()
    risk_text = " ".join(
        str(item) for item in result.get("summary_slots", {}).get("risks", [])
    ).lower()

    assert "circulate the approved pilot pricing table" in action_text
    assert "complete the storage access review" in action_text
    assert "send the support onboarding email" in action_text

    assert "support will use email for pilot users" in decision_text

    assert "storage permissions may delay approval" in risk_text
