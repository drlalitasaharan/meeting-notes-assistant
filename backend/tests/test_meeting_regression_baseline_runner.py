from pathlib import Path

from backend.app.services.meeting_regression_evaluator import load_expected_cases
from backend.scripts.run_meeting_regression_baseline import (
    normalize_actual_output,
    transcript_path_for_case,
)

FIXTURE_DIR = Path("backend/tests/fixtures/meeting_regression")


def _case(case_id: str) -> dict:
    for loaded_case in load_expected_cases(FIXTURE_DIR):
        expected_id = loaded_case["expected"].get("id")
        manifest_id = loaded_case["manifest"].get("id")
        if case_id in {expected_id, manifest_id}:
            return loaded_case
    raise AssertionError(f"case not found: {case_id}")


def test_transcript_path_is_found_for_controlled_short_case() -> None:
    path = transcript_path_for_case(FIXTURE_DIR, _case("S01"))

    assert path is not None
    assert path.name == "S01_controlled_short.txt"
    assert path.exists()


def test_transcript_path_is_found_for_ami_case_with_explicit_transcript_file() -> None:
    path = transcript_path_for_case(FIXTURE_DIR, _case("L02"))

    assert path is not None
    assert path.name == "L02_AMI_EN2001b_50min.txt"
    assert path.exists()


def test_missing_transcript_case_is_reported_as_none() -> None:
    path = transcript_path_for_case(FIXTURE_DIR, _case("N01"))

    assert path is None


def test_normalize_string_output_expands_to_evaluator_keys() -> None:
    actual = normalize_actual_output("Decision: launch pilot. Action: Priya sends pricing.")

    assert actual["summary"]
    assert actual["decisions"]
    assert actual["action_items"]
    assert actual["risks"]
    assert actual["context"]


def test_normalize_dict_output_preserves_schema() -> None:
    actual = normalize_actual_output(
        {
            "summary": "Pilot review",
            "decisions": ["Limit pilot to twenty users."],
            "action_items": [{"owner": "Priya", "action": "Send pricing."}],
        }
    )

    assert actual["summary"] == "Pilot review"
    assert actual["decisions"] == ["Limit pilot to twenty users."]
    assert actual["action_items"][0]["owner"] == "Priya"
