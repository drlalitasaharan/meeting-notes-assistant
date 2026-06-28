from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from app.services.meeting_regression_evaluator import (
    RegressionEvalConfig,
    evaluate_case,
)
from app.services.quality_engine_v3 import (
    run_quality_engine_v3,
)


@dataclass(frozen=True)
class QualityEngineV3RegressionGateConfig:
    min_v3_case_score: float = 0.70
    max_allowed_score_drop: float = 0.0


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _merged_list(*values: Any) -> list[Any]:
    output: list[Any] = []
    seen: set[str] = set()
    for value in values:
        for item in _as_list(value):
            key = repr(item)
            if key in seen:
                continue
            seen.add(key)
            output.append(item)
    return output


def _summary_slots(notes: dict[str, Any]) -> dict[str, Any]:
    slots = notes.get("summary_slots")
    return slots if isinstance(slots, dict) else {}


def _evaluator_payload(notes: dict[str, Any]) -> dict[str, Any]:
    """Adapt structured v3 notes to the existing regression evaluator schema."""

    payload = copy.deepcopy(notes)
    slots = _summary_slots(payload)

    action_objects = _as_list(payload.get("action_item_objects"))
    if action_objects:
        payload["actions"] = _merged_list(payload.get("actions"), action_objects)
        payload["action_items"] = _merged_list(payload.get("action_items"), action_objects)

    decision_objects = _as_list(payload.get("decision_objects"))
    if decision_objects:
        payload["decisions"] = _merged_list(payload.get("decisions"), decision_objects)

    risks = _as_list(slots.get("risks"))
    if risks:
        payload["risks"] = _merged_list(payload.get("risks"), risks)

    open_questions = _as_list(slots.get("open_questions"))
    if open_questions:
        payload["open_questions"] = _merged_list(payload.get("open_questions"), open_questions)

    if slots.get("purpose") and not payload.get("purpose"):
        payload["purpose"] = slots["purpose"]
    if slots.get("next_steps") and not payload.get("next_steps"):
        payload["next_steps"] = slots["next_steps"]

    return payload


def _metric_recall(result: dict[str, Any], metric: str) -> float:
    metrics = result.get("metrics")
    if not isinstance(metrics, dict):
        return 0.0
    metric_result = metrics.get(metric)
    if not isinstance(metric_result, dict):
        return 1.0
    return float(metric_result.get("recall", 0.0))


def _warning_messages(checks: dict[str, bool]) -> list[str]:
    messages = {
        "v3_output_generated": "Quality Engine v3 did not generate comparable output.",
        "v3_score_meets_threshold": "Quality Engine v3 score is below the regression threshold.",
        "overall_score_not_regressed": "Quality Engine v3 overall score regressed.",
        "action_recall_not_regressed": "Quality Engine v3 action recall regressed.",
        "decision_recall_not_regressed": "Quality Engine v3 decision recall regressed.",
        "risk_recall_not_regressed": "Quality Engine v3 risk recall regressed.",
        "context_recall_not_regressed": "Quality Engine v3 context recall regressed.",
        "critic_passed": "Quality Engine v3 critic reported warnings.",
    }
    return [message for key, message in messages.items() if not checks.get(key, False)]


def evaluate_quality_engine_v3_regression_case(
    *,
    case_id: str,
    expected: dict[str, Any],
    v1_notes: dict[str, Any],
    transcript_text: str | None,
    config: QualityEngineV3RegressionGateConfig | None = None,
) -> dict[str, Any]:
    """Run the v3 regression gate for one case without changing production notes."""

    config = config or QualityEngineV3RegressionGateConfig()
    eval_config = RegressionEvalConfig(min_case_score=config.min_v3_case_score)

    v1_eval = evaluate_case(expected, _evaluator_payload(v1_notes), eval_config)
    v3_result = run_quality_engine_v3(copy.deepcopy(v1_notes), transcript_text, mode="v3")
    v3_notes = v3_result.get("notes") if isinstance(v3_result, dict) else None
    metadata = v3_result.get("metadata") if isinstance(v3_result, dict) else {}
    if not isinstance(v3_notes, dict):
        v3_notes = copy.deepcopy(v1_notes)
    if not isinstance(metadata, dict):
        metadata = {}

    v3_eval = evaluate_case(expected, _evaluator_payload(v3_notes), eval_config)
    score_drop = float(v1_eval.get("score", 0.0)) - float(v3_eval.get("score", 0.0))
    critic_raw = metadata.get("critic")
    critic: dict[str, Any] = critic_raw if isinstance(critic_raw, dict) else {}

    checks = {
        "v3_output_generated": v3_notes != v1_notes,
        "v3_score_meets_threshold": bool(v3_eval.get("passed")),
        "overall_score_not_regressed": score_drop <= config.max_allowed_score_drop,
        "action_recall_not_regressed": _metric_recall(v3_eval, "actions")
        >= _metric_recall(v1_eval, "actions"),
        "decision_recall_not_regressed": _metric_recall(v3_eval, "decisions")
        >= _metric_recall(v1_eval, "decisions"),
        "risk_recall_not_regressed": _metric_recall(v3_eval, "risks")
        >= _metric_recall(v1_eval, "risks"),
        "context_recall_not_regressed": _metric_recall(v3_eval, "context")
        >= _metric_recall(v1_eval, "context"),
        "critic_passed": bool(critic.get("passed", True)),
    }

    warnings = _warning_messages(checks)
    return {
        "case_id": case_id,
        "passed": all(checks.values()),
        "warnings": warnings,
        "checks": checks,
        "v1_score": v1_eval.get("score", 0.0),
        "v3_score": v3_eval.get("score", 0.0),
        "v1_evaluation": v1_eval,
        "v3_evaluation": v3_eval,
        "v3_metadata": metadata,
    }


def evaluate_quality_engine_v3_regression_gate(
    cases: list[dict[str, Any]],
    config: QualityEngineV3RegressionGateConfig | None = None,
) -> dict[str, Any]:
    """Aggregate multiple v3 regression gate case results."""

    results = [
        evaluate_quality_engine_v3_regression_case(
            case_id=str(case.get("case_id") or case.get("id") or "unknown"),
            expected=case["expected"],
            v1_notes=case["v1_notes"],
            transcript_text=case.get("transcript_text"),
            config=config,
        )
        for case in cases
    ]
    passed_cases = sum(1 for result in results if result["passed"])
    total_cases = len(results)
    return {
        "passed": passed_cases == total_cases,
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "failed_cases": total_cases - passed_cases,
        "results": results,
    }
