from pathlib import Path

from backend.app.services.meeting_regression_evaluator import (
    RegressionEvalConfig,
    evaluate_case,
    evaluate_manifest,
    load_expected_cases,
    load_json,
)

FIXTURE_DIR = Path("backend/tests/fixtures/meeting_regression")


def test_regression_manifest_loads_completed_cases() -> None:
    cases = load_expected_cases(FIXTURE_DIR)

    assert len(cases) == 13
    assert all(case["manifest"]["ground_truth_status"] == "complete" for case in cases)


def test_expected_fixture_self_match_passes() -> None:
    expected = load_json(FIXTURE_DIR / "L01_long_business.expected.json")

    result = evaluate_case(
        expected,
        expected,
        RegressionEvalConfig(min_case_score=0.95),
    )

    assert result["passed"] is True
    assert result["score"] >= 0.95
    assert result["metrics"]["decisions"]["recall"] == 1.0
    assert result["metrics"]["actions"]["recall"] == 1.0


def test_missing_actual_output_fails_meaningfully() -> None:
    expected = load_json(FIXTURE_DIR / "L01_long_business.expected.json")

    result = evaluate_case(
        expected,
        {"summary": "This output does not include the expected decisions or actions."},
        RegressionEvalConfig(min_case_score=0.70),
    )

    assert result["passed"] is False
    assert result["metrics"]["decisions"]["matched"] < result["metrics"]["decisions"]["total"]
    assert result["metrics"]["actions"]["matched"] < result["metrics"]["actions"]["total"]


def test_manifest_self_check_passes_all_cases() -> None:
    report = evaluate_manifest(
        FIXTURE_DIR,
        self_check=True,
        config=RegressionEvalConfig(min_case_score=0.95),
    )

    assert report["total_cases"] == 13
    assert report["passed"] is True
    assert report["failed_cases"] == 0


def test_cli_self_check_runs_as_direct_script() -> None:
    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable,
            "backend/scripts/run_meeting_regression.py",
            "--self-check",
            "--min-score",
            "0.95",
            "--case",
            "S01",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "1/1 passed" in result.stdout
