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


def test_normalize_output_adds_transcript_context_without_leaking_to_decisions() -> None:
    transcript = (
        "The group discusses annotation data, NITE XML files, segmentation, "
        "information density, entropy scoring, Rainbow, and mapping scores "
        "back to existing segment identifiers."
    )

    actual = normalize_actual_output("Short generated summary.", transcript=transcript)

    context_text = " ".join(str(item) for item in actual["context"])
    assert "annotation data" in context_text
    assert "NITE XML" in context_text
    assert "information density" in context_text
    assert actual["decisions"] == ["Short generated summary."]
    assert actual["action_items"] == ["Short generated summary."]
    assert actual["risks"] == "Short generated summary."


def test_normalize_output_preserves_existing_structured_fields() -> None:
    actual = normalize_actual_output(
        {
            "summary": "Pilot review",
            "decisions": ["Limit pilot to twenty users."],
            "action_items": [{"owner": "Priya", "action": "Send pricing."}],
            "risks": ["Pricing delay may affect launch."],
            "context": ["Commercial pilot planning."],
        },
        transcript="Extra transcript context should only supplement context.",
    )

    assert actual["decisions"] == ["Limit pilot to twenty users."]
    assert actual["action_items"][0]["owner"] == "Priya"
    assert actual["risks"] == ["Pricing delay may affect launch."]
    assert "Commercial pilot planning." in actual["context"]


def test_normalize_output_uses_structured_decision_action_extraction() -> None:
    transcript = (
        "The team decided to limit the pilot to twenty users. "
        "We agreed to use email as the primary support channel. "
        "Priya will send the pricing table by 2026-06-18 17:00."
    )

    actual = normalize_actual_output("Short generated summary.", transcript=transcript)

    assert isinstance(actual["decisions"], list)
    assert any("limit the pilot to twenty users" in item.lower() for item in actual["decisions"])
    assert "Short generated summary." in actual["decisions"]

    assert isinstance(actual["action_items"], list)
    assert actual["action_items"][0]["owner"] == "Priya"
    assert "pricing table" in actual["action_items"][0]["action"].lower()
    assert "Short generated summary." in actual["action_items"]


def test_normalize_output_uses_structured_risk_extraction_with_summary_fallback() -> None:
    transcript = (
        "Pricing confirmation may delay the client follow-up. "
        "Old test files may reduce client confidence. "
        "Over-promising custom reporting could create unrealistic expectations."
    )

    actual = normalize_actual_output("Short generated summary.", transcript=transcript)

    assert isinstance(actual["risks"], list)
    risk_text = " ".join(str(item) for item in actual["risks"])
    assert "Pricing confirmation" in risk_text
    assert "reduce client confidence" in risk_text
    assert "unrealistic expectations" in risk_text
    assert "Short generated summary." in actual["risks"]
