from app.services.quality_engine_v3 import finalize_quality_engine_v3_persisted_notes


def _notes_with_key_points(key_points: list[str]) -> dict:
    return {
        "summary": "Align on main priorities.",
        "summary_slots": {},
        "key_points": key_points,
        "action_items": [],
        "action_item_objects": [],
        "decisions": [],
        "decision_objects": [],
    }


def test_qev3_filters_q_number_and_zero_filler_from_key_points() -> None:
    filler = (
        "Q3 Q4 Q5 Q6 Q7 Q8 Q9 Q10 Q11 Q12 Q13 Q14 Q15 Q16 Q17 Q18 "
        "Q19 Q20 Q21 Q22 Q23 Q24 Q25 Q26 Q27 Q28 Q29 Q30 "
        "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"
    )
    meaningful = "What maximum file size should be allowed for ProPilot users?"

    result = finalize_quality_engine_v3_persisted_notes(
        _notes_with_key_points([meaningful, filler])
    )

    assert result["key_points"] == [meaningful]


def test_qev3_filters_video_outro_filler_from_key_points() -> None:
    result = finalize_quality_engine_v3_persisted_notes(
        _notes_with_key_points(
            [
                "Diolch yn fawr am wylio'r fideo",
                "This is a synthetic three-hour meeting recording for Meet IQ testing",
            ]
        )
    )

    assert result["key_points"] == [
        "This is a synthetic three-hour meeting recording for Meet IQ testing"
    ]


def test_qev3_keeps_business_key_points() -> None:
    key_points = [
        "What maximum file size should be allowed for ProPilot users?",
        "Large video files may upload but fail later because of memory or timeout limits.",
        "Support copy should explain long recording upload expectations.",
    ]

    result = finalize_quality_engine_v3_persisted_notes(_notes_with_key_points(key_points))

    assert result["key_points"] == key_points
