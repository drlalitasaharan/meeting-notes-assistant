#!/usr/bin/env python3
"""Compare Quality Engine v2 shadow output against current baseline notes.

This script is intentionally local/QA-only. It does not wire Quality Engine v2
into production processing and does not change NOTES_ENGINE.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.quality_engine_v2 import run_quality_engine_v2  # noqa: E402


DEFAULT_BASELINE_DIR = REPO_ROOT / "qa_results" / "quality_engine_v2_baseline"
DEFAULT_REPORT_NAME = "v1_vs_v2_shadow_comparison.md"


@dataclass(frozen=True)
class MetricComparison:
    name: str
    v1: int | bool | None
    v2: int | bool | None

    @property
    def delta(self) -> int | str:
        if isinstance(self.v1, bool) or isinstance(self.v2, bool):
            return "yes" if self.v1 != self.v2 else "no"
        if self.v1 is None or self.v2 is None:
            return "n/a"
        return self.v2 - self.v1


@dataclass(frozen=True)
class CaseComparison:
    case_id: str
    notes_path: Path
    transcript_source: str
    metrics: list[MetricComparison]
    metadata: dict[str, Any]


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return payload


def _case_id_from_path(path: Path) -> str:
    name = path.name
    suffix = "_current_notes.json"
    return name[: -len(suffix)] if name.endswith(suffix) else path.stem


def discover_notes_files(baseline_dir: Path) -> list[Path]:
    return sorted(baseline_dir.glob("*_current_notes.json"))


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _slots(notes: dict[str, Any]) -> dict[str, Any]:
    summary_slots = notes.get("summary_slots")
    return summary_slots if isinstance(summary_slots, dict) else {}


def _list_or_none(value: Any) -> list[Any] | None:
    return value if isinstance(value, list) else None


def _preferred_count(notes: dict[str, Any], object_key: str, fallback_key: str) -> int:
    objects = _list_or_none(notes.get(object_key))
    if objects is not None:
        return len(objects)
    fallback = _list_or_none(notes.get(fallback_key))
    return len(fallback or [])


def _slot_count(notes: dict[str, Any], slot_key: str, fallback_key: str | None = None) -> int:
    values = _list_or_none(_slots(notes).get(slot_key))
    if values is not None:
        return len(values)
    if fallback_key:
        fallback = _list_or_none(notes.get(fallback_key))
        return len(fallback or [])
    return 0


def _optional_slot_count(
    notes: dict[str, Any],
    slot_key: str,
    fallback_key: str | None = None,
) -> int | None:
    slots = _slots(notes)
    if slot_key in slots:
        values = _list_or_none(slots.get(slot_key))
        return len(values or [])
    if fallback_key and fallback_key in notes:
        values = _list_or_none(notes.get(fallback_key))
        return len(values or [])
    return None


def collect_metrics(notes: dict[str, Any]) -> dict[str, int | bool | None]:
    slots = _slots(notes)
    return {
        "purpose_present": bool(_text(slots.get("purpose"))),
        "action_count": _preferred_count(notes, "action_item_objects", "action_items"),
        "decision_count": _preferred_count(notes, "decision_objects", "decisions"),
        "next_step_count": _slot_count(notes, "next_steps", "next_steps"),
        "risk_count": _slot_count(notes, "risks", "risks"),
        "open_question_count": _optional_slot_count(notes, "open_questions", "open_questions"),
    }


def compare_metrics(v1: dict[str, Any], v2: dict[str, Any]) -> list[MetricComparison]:
    v1_metrics = collect_metrics(v1)
    v2_metrics = collect_metrics(v2)
    return [
        MetricComparison(name=key, v1=v1_metrics[key], v2=v2_metrics[key])
        for key in (
            "purpose_present",
            "action_count",
            "decision_count",
            "next_step_count",
            "risk_count",
            "open_question_count",
        )
    ]


def _raw_transcript_from_notes(notes: dict[str, Any]) -> str:
    for key in ("transcript", "transcript_text", "raw_transcript"):
        value = notes.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            text = value.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()
    return ""


def load_transcript_for_case(
    baseline_dir: Path,
    case_id: str,
    notes: dict[str, Any],
) -> tuple[str, str]:
    embedded = _raw_transcript_from_notes(notes)
    if embedded:
        return embedded, "embedded notes transcript"

    candidates = [
        baseline_dir / f"{case_id}_transcript.txt",
        baseline_dir / f"{case_id}_transcript.md",
        baseline_dir / f"{case_id}_source.txt",
        baseline_dir / f"{case_id}_source.md",
        baseline_dir / f"{case_id}_raw_transcript.txt",
        baseline_dir / "transcripts" / f"{case_id}.txt",
        baseline_dir / "transcripts" / f"{case_id}.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            text = candidate.read_text(encoding="utf-8").strip()
            if text:
                return text, str(candidate.relative_to(REPO_ROOT))

    return "", "not available"


def compare_case(path: Path) -> CaseComparison:
    notes = _load_json(path)
    case_id = _case_id_from_path(path)
    transcript, transcript_source = load_transcript_for_case(path.parent, case_id, notes)
    result = run_quality_engine_v2(copy.deepcopy(notes), transcript, mode="v2")
    v2_notes = result.get("notes") if isinstance(result, dict) else None
    metadata = result.get("metadata") if isinstance(result, dict) else {}
    if not isinstance(v2_notes, dict):
        v2_notes = notes
    if not isinstance(metadata, dict):
        metadata = {}
    return CaseComparison(
        case_id=case_id,
        notes_path=path,
        transcript_source=transcript_source,
        metrics=compare_metrics(notes, v2_notes),
        metadata=metadata,
    )


def _format_value(value: int | bool | None) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _markdown_row(cells: list[object]) -> str:
    return "| " + " | ".join(str(cell) for cell in cells) + " |"


def _markdown_separator(alignments: list[str]) -> str:
    return _markdown_row(alignments)


def _normalize_markdown_tables(markdown: str) -> str:
    """Normalize simple Markdown table spacing in generated QA reports."""
    markdown = markdown.replace("does notenable", "does not enable")
    markdown = markdown.replace("Actionsv1", "Actions v1")
    markdown = markdown.replace("Open questionsv1", "Open questions v1")
    markdown = markdown.replace('"mode": "v2","warnings"', '"mode": "v2", "warnings"')

    fixed_lines: list[str] = []
    for line in markdown.splitlines():
        if line.startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            line = "| " + " | ".join(cells) + " |"
        fixed_lines.append(line)

    return "\n".join(fixed_lines).rstrip() + "\n"


def render_report(comparisons: list[CaseComparison], baseline_dir: Path) -> str:
    lines = [
        "# Quality Engine v2 Shadow Comparison",
        "",
        "This local QA report compares current baseline notes JSON against "
        '`run_quality_engine_v2(..., mode="v2")` output. It does not enable '
        "`NOTES_ENGINE=v2` or modify production behavior.",
        "",
        f"Baseline directory: `{_display_path(baseline_dir)}`",
        "",
        "## Summary",
        "",
        _markdown_row(
            [
                "Case",
                "Transcript source",
                "Purpose v1",
                "Purpose v2",
                "Actions v1",
                "Actions v2",
                "Decisions v1",
                "Decisions v2",
                "Next steps v1",
                "Next steps v2",
                "Risks v1",
                "Risks v2",
                "Open questions v1",
                "Open questions v2",
            ]
        ),
        _markdown_separator(
            [
                "---",
                "---",
                "---:",
                "---:",
                "---:",
                "---:",
                "---:",
                "---:",
                "---:",
                "---:",
                "---:",
                "---:",
                "---:",
                "---:",
            ]
        ),
    ]

    for comparison in comparisons:
        metric_by_name = {metric.name: metric for metric in comparison.metrics}
        lines.append(
            _markdown_row(
                [
                    comparison.case_id,
                    comparison.transcript_source,
                    _format_value(metric_by_name["purpose_present"].v1),
                    _format_value(metric_by_name["purpose_present"].v2),
                    _format_value(metric_by_name["action_count"].v1),
                    _format_value(metric_by_name["action_count"].v2),
                    _format_value(metric_by_name["decision_count"].v1),
                    _format_value(metric_by_name["decision_count"].v2),
                    _format_value(metric_by_name["next_step_count"].v1),
                    _format_value(metric_by_name["next_step_count"].v2),
                    _format_value(metric_by_name["risk_count"].v1),
                    _format_value(metric_by_name["risk_count"].v2),
                    _format_value(metric_by_name["open_question_count"].v1),
                    _format_value(metric_by_name["open_question_count"].v2),
                ]
            )
        )

    lines.extend(["", "## Per-Case Metric Deltas", ""])
    for comparison in comparisons:
        lines.extend(
            [
                f"### {comparison.case_id}",
                "",
                f"- Notes file: `{_display_path(comparison.notes_path)}`",
                f"- Transcript source: `{comparison.transcript_source}`",
                f"- V2 metadata: `{json.dumps(comparison.metadata, sort_keys=True)}`",
                "",
                _markdown_row(["Metric", "v1", "v2", "Delta/changed"]),
                _markdown_separator(["---", "---:", "---:", "---:"]),
            ]
        )
        for metric in comparison.metrics:
            lines.append(
                _markdown_row(
                    [
                        metric.name,
                        _format_value(metric.v1),
                        _format_value(metric.v2),
                        metric.delta,
                    ]
                )
            )
        lines.append("")

    return _normalize_markdown_tables("\n".join(lines).rstrip() + "\n")


def write_report(baseline_dir: Path, report_name: str = DEFAULT_REPORT_NAME) -> Path:
    notes_files = discover_notes_files(baseline_dir)
    if len(notes_files) != 5:
        raise SystemExit(
            f"Expected 5 *_current_notes.json files in {baseline_dir}, found {len(notes_files)}"
        )
    comparisons = [compare_case(path) for path in notes_files]
    report = render_report(comparisons, baseline_dir)
    output_path = baseline_dir / report_name
    output_path.write_text(report, encoding="utf-8")
    return output_path


def _clean_report_markdown(markdown: str) -> str:
    """Clean generated Markdown report spacing."""
    markdown = markdown.replace("does notenable", "does not enable")
    markdown = markdown.replace("Actionsv1", "Actions v1")
    markdown = markdown.replace("Open questionsv1", "Open questions v1")
    markdown = markdown.replace('"mode": "v2","warnings"', '"mode": "v2", "warnings"')

    fixed_lines: list[str] = []
    for line in markdown.splitlines():
        if line.startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            line = "| " + " | ".join(cells) + " |"
        fixed_lines.append(line)

    return "\n".join(fixed_lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare Quality Engine v2 output against current baseline notes."
    )
    parser.add_argument(
        "--baseline-dir",
        type=Path,
        default=DEFAULT_BASELINE_DIR,
        help="Directory containing five *_current_notes.json files.",
    )
    parser.add_argument(
        "--report-name",
        default=DEFAULT_REPORT_NAME,
        help="Markdown report filename to write inside the baseline directory.",
    )
    args = parser.parse_args()

    output_path = write_report(args.baseline_dir, args.report_name)
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
