from __future__ import annotations

import json
from pathlib import Path

from backend.scripts import run_quality_engine_v2_regression_gate as runner

FIXTURE_DIR = Path("backend/tests/fixtures/meeting_regression")


def test_quality_engine_v2_regression_gate_runner_builds_five_case_report() -> None:
    report = runner.build_report(fixture_dir=FIXTURE_DIR)

    assert report["case_ids"] == ["S01", "M01", "M04", "M05", "L01"]
    assert report["total_cases"] == 5
    assert len(report["results"]) == 5
    for result in report["results"]:
        assert "v1_score" in result
        assert "v2_score" in result
        assert "checks" in result
        assert "v2_score_meets_threshold" in result["checks"]


def test_quality_engine_v2_regression_gate_runner_writes_json_and_markdown(
    tmp_path: Path,
) -> None:
    output = tmp_path / "latest.json"
    markdown_output = tmp_path / "latest.md"
    report = runner.build_report(fixture_dir=FIXTURE_DIR)

    runner.write_reports(report, output, markdown_output)

    payload = json.loads(output.read_text(encoding="utf-8"))
    markdown = markdown_output.read_text(encoding="utf-8")
    assert payload["total_cases"] == 5
    assert payload["case_ids"] == ["S01", "M01", "M04", "M05", "L01"]
    assert "# Quality Engine v2 Regression Gate" in markdown
    assert "| Case | v1 score | v2 score | Result | Failed checks |" in markdown


def test_quality_engine_v2_regression_gate_runner_exits_nonzero_on_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    def failed_report(*, fixture_dir, case_ids, min_score):
        return {
            "schema_version": 1,
            "gate": "quality_engine_v2_regression",
            "notes_engine_default": "v1",
            "fixture_dir": str(fixture_dir),
            "case_ids": ["S01"],
            "min_score": min_score,
            "passed": False,
            "total_cases": 1,
            "passed_cases": 0,
            "failed_cases": 1,
            "results": [
                {
                    "case_id": "S01",
                    "passed": False,
                    "v1_score": 1.0,
                    "v2_score": 0.0,
                    "checks": {"overall_score_not_regressed": False},
                    "warnings": ["Quality Engine v2 overall score regressed."],
                }
            ],
        }

    monkeypatch.setattr(runner, "build_report", failed_report)

    result = runner.main(
        [
            "--output",
            str(tmp_path / "latest.json"),
            "--markdown-output",
            str(tmp_path / "latest.md"),
        ]
    )

    assert result == 1


def test_quality_engine_v2_regression_gate_runner_allow_fail_exits_zero(
    tmp_path: Path,
    monkeypatch,
) -> None:
    def failed_report(*, fixture_dir, case_ids, min_score):
        return {
            "schema_version": 1,
            "gate": "quality_engine_v2_regression",
            "notes_engine_default": "v1",
            "fixture_dir": str(fixture_dir),
            "case_ids": ["S01"],
            "min_score": min_score,
            "passed": False,
            "total_cases": 1,
            "passed_cases": 0,
            "failed_cases": 1,
            "results": [
                {
                    "case_id": "S01",
                    "passed": False,
                    "v1_score": 1.0,
                    "v2_score": 0.0,
                    "checks": {"overall_score_not_regressed": False},
                    "warnings": ["Quality Engine v2 overall score regressed."],
                }
            ],
        }

    monkeypatch.setattr(runner, "build_report", failed_report)

    result = runner.main(
        [
            "--output",
            str(tmp_path / "latest.json"),
            "--markdown-output",
            str(tmp_path / "latest.md"),
            "--allow-fail",
        ]
    )

    assert result == 0
