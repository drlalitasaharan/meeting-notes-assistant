from app.services.quality_engine_v3_regression_gate import (
    QualityEngineV3RegressionGateConfig,
    evaluate_quality_engine_v3_regression_case,
    evaluate_quality_engine_v3_regression_gate,
)

A10MINS_TRANSCRIPT = """
I'd like us to leave this meeting with a clear decision on the target audience.
The main purpose of today's meeting is to finalize the demo flow.
The first pilot audience will be consultants, agencies, founders, and small teams.
Lalita will create the clean 10-minute audio test and run it through the product today.
Lalita will prepare the short live demo file and keep one backup processed meeting ready.
If we say it's designed for consultants, we should be careful about the promise.
The live demo will use a short prepared recording.
Do we want to support 3-hour recordings now or later?
"""


def _baseline_notes() -> dict:
    return {
        "summary": "The team discussed target audience, demo flow, and pilot readiness.",
        "summary_slots": {
            "purpose": "",
            "outcome": "",
            "risks": [],
            "open_questions": [],
            "next_steps": [],
        },
        "action_item_objects": [],
        "decision_objects": [],
    }


def _expected_notes() -> dict:
    return {
        "summary": "The team discussed target audience, demo flow, and pilot readiness.",
        "actions": [
            "Create the clean 10-minute audio test",
            "Prepare the short live demo file",
        ],
        "decisions": [
            "The first pilot audience will be consultants, agencies, founders, and small teams.",
            "The live demo will use a short prepared recording.",
        ],
        "risks": [
            "If we say it's designed for consultants, we should be careful about the promise.",
        ],
        "open_questions": [
            "Do we want to support 3-hour recordings now or later?",
        ],
        "context": [
            "target audience",
            "demo flow",
            "pilot readiness",
        ],
    }


def test_qev3_regression_case_passes_a10mins() -> None:
    result = evaluate_quality_engine_v3_regression_case(
        case_id="A10mins",
        expected=_expected_notes(),
        v1_notes=_baseline_notes(),
        transcript_text=A10MINS_TRANSCRIPT,
        config=QualityEngineV3RegressionGateConfig(min_v3_case_score=0.60),
    )

    assert result["passed"] is True
    assert result["checks"]["v3_output_generated"] is True
    assert result["checks"]["v3_score_meets_threshold"] is True
    assert result["v3_metadata"]["mode"] == "v3"
    assert result["v3_metadata"]["applied"] is True


def test_qev3_regression_gate_aggregates_cases() -> None:
    result = evaluate_quality_engine_v3_regression_gate(
        [
            {
                "case_id": "A10mins",
                "expected": _expected_notes(),
                "v1_notes": _baseline_notes(),
                "transcript_text": A10MINS_TRANSCRIPT,
            }
        ],
        config=QualityEngineV3RegressionGateConfig(min_v3_case_score=0.60),
    )

    assert result["total_cases"] == 1
    assert result["passed_cases"] == 1
    assert result["failed_cases"] == 0
    assert result["passed"] is True
