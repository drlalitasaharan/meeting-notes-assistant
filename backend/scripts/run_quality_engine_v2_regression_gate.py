#!/usr/bin/env python3
"""Run the Quality Engine v2 regression gate on known fixture meetings.

This script is local/QA-only. It does not enable Quality Engine v2 rollout and
does not change production note processing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"

for candidate in (REPO_ROOT, BACKEND_ROOT):
    candidate_text = str(candidate)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)

from backend.scripts.run_meeting_regression_baseline import (  # noqa: E402
    normalize_actual_output,
    transcript_path_for_case,
)

from app.services.meeting_regression_evaluator import load_expected_cases  # noqa: E402
from app.services.quality_engine_v2_regression_gate import (  # noqa: E402
    QualityEngineV2RegressionGateConfig,
    evaluate_quality_engine_v2_regression_gate,
)

DEFAULT_CASE_IDS = ("S01", "M01", "M04", "M05", "L01")
DEFAULT_FIXTURE_DIR = Path("backend/tests/fixtures/meeting_regression")
DEFAULT_OUTPUT = Path("backend/reports/qev2_regression_gate/latest.json")
DEFAULT_MARKDOWN_OUTPUT = Path("backend/reports/qev2_regression_gate/latest.md")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Quality Engine v2 regression quality gate on fixture meetings."
    )
    parser.add_argument(
        "--fixture-dir",
        type=Path,
        default=DEFAULT_FIXTURE_DIR,
        help="Directory containing meeting regression manifest and fixtures.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path for deterministic JSON report.",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=DEFAULT_MARKDOWN_OUTPUT,
        help="Path for Markdown summary report.",
    )
    parser.add_argument(
        "--case",
        action="append",
        default=[],
        help="Case ID to run. Can be repeated. Defaults to S01, M01, M04, M05, L01.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.70,
        help="Minimum v2 case score required to pass.",
    )
    parser.add_argument(
        "--allow-fail",
        action="store_true",
        help="Exit zero even when the quality gate fails.",
    )
    return parser.parse_args(argv)


def _case_id(loaded_case: dict[str, Any]) -> str:
    expected = loaded_case["expected"]
    manifest = loaded_case["manifest"]
    return str(expected.get("id") or manifest.get("id"))


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _selected_cases(
    fixture_dir: Path,
    requested_case_ids: list[str],
) -> list[dict[str, Any]]:
    requested = requested_case_ids or list(DEFAULT_CASE_IDS)
    loaded_by_id = {_case_id(case): case for case in load_expected_cases(fixture_dir)}

    missing = [case_id for case_id in requested if case_id not in loaded_by_id]
    if missing:
        raise SystemExit(f"Missing requested regression fixture case(s): {', '.join(missing)}")

    return [loaded_by_id[case_id] for case_id in requested]


def _load_gate_case(fixture_dir: Path, loaded_case: dict[str, Any]) -> dict[str, Any]:
    case_id = _case_id(loaded_case)
    transcript_path = transcript_path_for_case(fixture_dir, loaded_case)
    if transcript_path is None:
        raise SystemExit(f"Missing transcript fixture for case {case_id}")

    transcript = transcript_path.read_text(encoding="utf-8")
    v1_notes = normalize_actual_output({}, transcript=transcript)
    v1_notes["_regression_case_id"] = case_id
    v1_notes["_baseline_source"] = "transcript_normalizer"
    v1_notes["_transcript_path"] = _display_path(transcript_path)

    return {
        "case_id": case_id,
        "expected": loaded_case["expected"],
        "v1_notes": v1_notes,
        "transcript_text": transcript,
        "transcript_path": _display_path(transcript_path),
        "expected_path": _display_path(Path(loaded_case["expected_path"])),
    }


def _summarize_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": result["case_id"],
        "passed": result["passed"],
        "v1_score": result["v1_score"],
        "v2_score": result["v2_score"],
        "warnings": result["warnings"],
        "checks": result["checks"],
    }


def build_report(
    *,
    fixture_dir: Path = DEFAULT_FIXTURE_DIR,
    case_ids: list[str] | None = None,
    min_score: float = 0.70,
) -> dict[str, Any]:
    loaded_cases = _selected_cases(fixture_dir, case_ids or [])
    gate_cases = [_load_gate_case(fixture_dir, loaded_case) for loaded_case in loaded_cases]
    gate_report = evaluate_quality_engine_v2_regression_gate(
        gate_cases,
        config=QualityEngineV2RegressionGateConfig(min_v2_case_score=min_score),
    )
    case_metadata = {
        case["case_id"]: {
            "expected_path": case["expected_path"],
            "transcript_path": case["transcript_path"],
        }
        for case in gate_cases
    }

    results = []
    for result in gate_report["results"]:
        summary = _summarize_result(result)
        summary.update(case_metadata.get(result["case_id"], {}))
        results.append(summary)

    return {
        "schema_version": 1,
        "gate": "quality_engine_v2_regression",
        "notes_engine_default": "v1",
        "fixture_dir": _display_path(fixture_dir),
        "case_ids": [result["case_id"] for result in results],
        "min_score": min_score,
        "passed": gate_report["passed"],
        "total_cases": gate_report["total_cases"],
        "passed_cases": gate_report["passed_cases"],
        "failed_cases": gate_report["failed_cases"],
        "results": results,
    }


def render_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Quality Engine v2 Regression Gate",
        "",
        "This report is generated from fixture transcripts only. It does not enable "
        "Quality Engine v2 rollout or change production note behavior.",
        "",
        f"- Fixture directory: `{report['fixture_dir']}`",
        f"- Cases: {', '.join(report['case_ids'])}",
        f"- Minimum v2 score: {report['min_score']}",
        f"- Result: {'PASS' if report['passed'] else 'FAIL'}",
        "",
        "| Case | v1 score | v2 score | Result | Failed checks |",
        "| --- | ---: | ---: | --- | --- |",
    ]

    for result in report["results"]:
        failed_checks = [key for key, passed in result.get("checks", {}).items() if not passed]
        lines.append(
            "| {case_id} | {v1_score} | {v2_score} | {status} | {failed} |".format(
                case_id=result["case_id"],
                v1_score=result["v1_score"],
                v2_score=result["v2_score"],
                status="PASS" if result["passed"] else "FAIL",
                failed=", ".join(failed_checks) if failed_checks else "-",
            )
        )

    lines.extend(["", "## Warnings", ""])
    for result in report["results"]:
        warnings = result.get("warnings") or []
        if not warnings:
            lines.append(f"- {result['case_id']}: none")
            continue
        for warning in warnings:
            lines.append(f"- {result['case_id']}: {warning}")

    return "\n".join(lines).rstrip() + "\n"


def write_reports(report: dict[str, Any], output: Path, markdown_output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_output.write_text(render_markdown_report(report), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_report(
        fixture_dir=args.fixture_dir,
        case_ids=args.case,
        min_score=args.min_score,
    )
    write_reports(report, args.output, args.markdown_output)
    print(f"Wrote {args.output}")
    print(f"Wrote {args.markdown_output}")
    if report["passed"] or args.allow_fail:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
