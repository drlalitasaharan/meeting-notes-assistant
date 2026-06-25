from __future__ import annotations

import json
from pathlib import Path

from scripts.compare_quality_engine_v2_baseline import (
    collect_metrics,
    load_transcript_for_case,
    write_report,
)


def test_collect_metrics_counts_baseline_sections() -> None:
    notes = {
        "summary_slots": {
            "purpose": "Review launch readiness.",
            "next_steps": ["Send recap."],
            "risks": ["Pricing delay."],
            "open_questions": ["Who owns support?"],
        },
        "action_item_objects": [{"task": "Send recap"}],
        "decision_objects": [{"text": "Use email support."}],
    }

    assert collect_metrics(notes) == {
        "purpose_present": True,
        "action_count": 1,
        "decision_count": 1,
        "next_step_count": 1,
        "risk_count": 1,
        "open_question_count": 1,
    }


def test_load_transcript_for_case_is_optional(tmp_path: Path) -> None:
    notes = {"summary_slots": {}}

    transcript, source = load_transcript_for_case(tmp_path, "M01", notes)

    assert transcript == ""
    assert source == "not available"


def test_write_report_creates_shadow_comparison_markdown(tmp_path: Path) -> None:
    for case_id in ("M01", "M02", "M03", "M04", "S01_client_weekly_sync"):
        notes = {
            "summary": "Today we need to review launch readiness.",
            "summary_slots": {
                "purpose": "",
                "next_steps": [],
                "risks": [],
            },
            "action_item_objects": [{"owner": "Team", "task": "Send recap"}],
            "decision_objects": [],
        }
        (tmp_path / f"{case_id}_current_notes.json").write_text(
            json.dumps(notes),
            encoding="utf-8",
        )

    output_path = write_report(tmp_path)
    report = output_path.read_text(encoding="utf-8")

    assert output_path.name == "v1_vs_v2_shadow_comparison.md"
    assert "# Quality Engine v2 Shadow Comparison" in report
    assert "M01" in report
    assert "S01_client_weekly_sync" in report
    assert "purpose_present" in report
