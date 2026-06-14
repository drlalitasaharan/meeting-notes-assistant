
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_scorer_module():
    script = Path(__file__).resolve().parents[1] / "scripts" / "score_chunk_action_expected.py"
    spec = importlib.util.spec_from_file_location("score_chunk_action_expected", script)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _json_block(payload: dict) -> str:
    return "```json\n" + json.dumps(payload, indent=2) + "\n```\n"


def test_normalize_action_matches_owner_separator_variants():
    scorer = _load_scorer_module()

    assert scorer.normalize_action(
        "Industrial Designer - Take minutes and put updated minutes in the shared folder."
    ) == scorer.normalize_action(
        "industrial designer: take minutes and put updated minutes in the shared folder"
    )


def test_extract_after_actions_prefers_raw_json_block(tmp_path):
    scorer = _load_scorer_module()

    after = tmp_path / "sample.after.md"
    after.write_text(
        "# After\n\n"
        "## Action Items\n\n"
        "- Wrong fallback\n\n"
        + _json_block(
            {
                "action_items": [
                    "Team - Save the smartboard output as a JPEG",
                ]
            }
        )
    )

    assert scorer.extract_after_actions(after) == [
        "Team - Save the smartboard output as a JPEG"
    ]


def test_score_case_exact_match_passes(tmp_path):
    scorer = _load_scorer_module()

    expected = tmp_path / "expected.md"
    expected.write_text(
        "# Expected\n\n"
        "## Expected actions\n\n"
        "- Team - Save the smartboard output as a JPEG\n"
    )

    after = tmp_path / "after.md"
    after.write_text(
        "# After\n\n"
        + _json_block(
            {
                "action_items": [
                    "Team - Save the smartboard output as a JPEG",
                ]
            }
        )
    )

    result = scorer.score_case(
        {"id": "sample", "expected": str(expected), "after": str(after)},
        min_precision=0.85,
        min_recall=0.85,
    )

    assert result["status"] == "PASS"
    assert result["matched_count"] == 1
    assert result["missing_count"] == 0
    assert result["unexpected_count"] == 0


def test_score_case_reports_missing_and_unexpected(tmp_path):
    scorer = _load_scorer_module()

    expected = tmp_path / "expected.md"
    expected.write_text(
        "# Expected\n\n"
        "## Expected actions\n\n"
        "- Priya - Confirm pricing\n"
    )

    after = tmp_path / "after.md"
    after.write_text(
        "# After\n\n"
        + _json_block(
            {
                "action_items": [
                    "Jordan - Prepare demo account",
                ]
            }
        )
    )

    result = scorer.score_case(
        {"id": "sample", "expected": str(expected), "after": str(after)},
        min_precision=0.85,
        min_recall=0.85,
    )

    assert result["status"] == "FAIL"
    assert result["missing_expected_actions"] == ["Priya - Confirm pricing"]
    assert result["unexpected_actual_actions"] == ["Jordan - Prepare demo account"]


def test_score_case_marks_missing_after_evidence(tmp_path):
    scorer = _load_scorer_module()

    expected = tmp_path / "expected.md"
    expected.write_text(
        "# Expected\n\n"
        "## Expected actions\n\n"
        "- Team - Save the smartboard output as a JPEG\n"
    )

    result = scorer.score_case(
        {"id": "sample", "expected": str(expected), "after": None},
        min_precision=0.85,
        min_recall=0.85,
    )

    assert result["status"] == "MISSING_AFTER_EVIDENCE"
    assert result["missing_count"] == 1
