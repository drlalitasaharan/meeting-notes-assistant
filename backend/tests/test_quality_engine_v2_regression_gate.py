from __future__ import annotations

from app.services.quality_engine_v2 import normalize_notes_engine_mode
from app.services.quality_engine_v2_regression_gate import (
    evaluate_quality_engine_v2_regression_case,
    evaluate_quality_engine_v2_regression_gate,
)


def _expected_case() -> dict[str, object]:
    return {
        "id": "QEV2_GATE",
        "title": "Quality Engine v2 gate fixture",
        "expected_context": ["Review launch readiness for Starter checkout."],
        "expected_decisions": ["Launch Starter first."],
        "expected_actions": [
            {
                "owner": "Priya",
                "action": "Prepare launch copy.",
                "deadline": "Friday",
            }
        ],
        "expected_risks": ["Pricing approval may delay launch."],
    }


def _thin_v1_notes() -> dict[str, object]:
    return {
        "summary": "The team reviewed launch readiness for Starter checkout.",
        "summary_slots": {
            "purpose": "Review launch readiness for Starter checkout.",
            "next_steps": [],
            "risks": [],
        },
        "action_item_objects": [],
        "decision_objects": [],
    }


def _transcript() -> str:
    return (
        "Decision: we will launch Starter first. "
        "Priya will prepare launch copy by Friday. "
        "Risk: Pricing approval may delay launch."
    )


def test_quality_engine_v2_regression_gate_passes_when_v2_improves_expected_recall() -> None:
    result = evaluate_quality_engine_v2_regression_case(
        case_id="QEV2_GATE",
        expected=_expected_case(),
        v1_notes=_thin_v1_notes(),
        transcript_text=_transcript(),
    )

    assert result["passed"] is True
    assert result["checks"]["v1_default_preserved"] is True
    assert result["checks"]["v2_score_meets_threshold"] is True
    assert result["checks"]["action_recall_not_regressed"] is True
    assert result["checks"]["decision_recall_not_regressed"] is True
    assert result["checks"]["risk_recall_not_regressed"] is True
    assert result["v2_score"] >= result["v1_score"]
    assert result["warnings"] == []
    assert normalize_notes_engine_mode(None) == "v1"


def test_quality_engine_v2_regression_gate_fails_when_v2_quality_regresses(monkeypatch) -> None:
    import app.services.quality_engine_v2_regression_gate as gate

    def weak_v2_result(notes, transcript_text, *, mode):
        return {
            "notes": {
                "summary": "Generic notes.",
                "summary_slots": {"purpose": "", "next_steps": [], "risks": []},
                "action_item_objects": [],
                "decision_objects": [],
            },
            "metadata": {"critic": {"passed": True, "warnings": [], "checks": {}}},
        }

    monkeypatch.setattr(gate, "run_quality_engine_v2", weak_v2_result)

    result = evaluate_quality_engine_v2_regression_case(
        case_id="QEV2_GATE",
        expected=_expected_case(),
        v1_notes={
            **_thin_v1_notes(),
            "action_item_objects": [
                {
                    "owner": "Priya",
                    "task": "Prepare launch copy.",
                    "deadline": "Friday",
                }
            ],
        },
        transcript_text=_transcript(),
    )

    assert result["passed"] is False
    assert result["checks"]["v2_score_meets_threshold"] is False
    assert result["checks"]["overall_score_not_regressed"] is False
    assert "Quality Engine v2 overall score regressed." in result["warnings"]


def test_quality_engine_v2_regression_gate_aggregates_cases() -> None:
    report = evaluate_quality_engine_v2_regression_gate(
        [
            {
                "case_id": "QEV2_GATE",
                "expected": _expected_case(),
                "v1_notes": _thin_v1_notes(),
                "transcript_text": _transcript(),
            }
        ]
    )

    assert report["passed"] is True
    assert report["total_cases"] == 1
    assert report["passed_cases"] == 1
    assert report["failed_cases"] == 0
