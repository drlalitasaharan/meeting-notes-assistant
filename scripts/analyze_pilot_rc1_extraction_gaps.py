from __future__ import annotations

import csv
import json
from pathlib import Path


BENCH_DIR = Path("test_outputs/pilot_rc1_benchmark_audio")
OUT_DIR = Path("test_outputs/pilot_rc1_extraction_improvement")
OUT_DIR.mkdir(parents=True, exist_ok=True)

rows: list[dict[str, str]] = []

for case_dir in sorted(BENCH_DIR.iterdir()):
    if not case_dir.is_dir():
        continue

    notes_path = case_dir / "notes_ai.json"
    job_path = case_dir / "job_status_latest.json"

    if not notes_path.exists():
        continue

    try:
        notes = json.loads(notes_path.read_text())
    except json.JSONDecodeError:
        notes = {}

    try:
        job = json.loads(job_path.read_text()) if job_path.exists() else {}
    except json.JSONDecodeError:
        job = {}

    summary = notes.get("summary") or ""
    slots = notes.get("summary_slots") or {}
    key_points = notes.get("key_points") or []
    decisions = notes.get("decisions") or []
    decision_objects = notes.get("decision_objects") or []
    action_items = notes.get("action_items") or []
    action_objects = notes.get("action_item_objects") or []

    decision_count = len(decisions) + len(decision_objects)
    action_count = len(action_items) + len(action_objects)

    rows.append(
        {
            "case": case_dir.name,
            "job_status": str(job.get("status", "")),
            "summary_len": str(len(summary)),
            "purpose_len": str(len(slots.get("purpose") or "")),
            "outcome_len": str(len(slots.get("outcome") or "")),
            "key_points": str(len(key_points)),
            "decisions": str(decision_count),
            "actions": str(action_count),
            "needs_decision_fix": "yes" if decision_count == 0 else "no",
            "needs_action_fix": "yes" if action_count == 0 else "no",
        }
    )

csv_path = OUT_DIR / "extraction_gap_summary.csv"
with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "case",
            "job_status",
            "summary_len",
            "purpose_len",
            "outcome_len",
            "key_points",
            "decisions",
            "actions",
            "needs_decision_fix",
            "needs_action_fix",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

case_count = len(rows)
jobs_succeeded = sum(1 for r in rows if r["job_status"] == "succeeded")
decision_gap_count = sum(1 for r in rows if r["needs_decision_fix"] == "yes")
action_gap_count = sum(1 for r in rows if r["needs_action_fix"] == "yes")

report = [
    "# Pilot RC1 Decision and Action Extraction Improvement Plan",
    "",
    "## Purpose",
    "",
    "This plan targets the highest-impact quality gap from the Pilot RC1 benchmark baseline: structured decision and action extraction across realistic meeting types.",
    "",
    "## Current Benchmark Signal",
    "",
    f"- Benchmark cases analyzed: {case_count}",
    f"- Jobs succeeded: {jobs_succeeded}/{case_count}",
    f"- Cases missing structured decisions: {decision_gap_count}/{case_count}",
    f"- Cases missing structured actions: {action_gap_count}/{case_count}",
    "",
    "## Gap Summary",
    "",
    "| Case | Job Status | Key Points | Decisions | Actions | Needs Decision Fix | Needs Action Fix |",
    "|---|---|---:|---:|---:|---|---|",
]

for r in rows:
    report.append(
        f"| {r['case']} | {r['job_status']} | {r['key_points']} | {r['decisions']} | {r['actions']} | {r['needs_decision_fix']} | {r['needs_action_fix']} |"
    )

report.extend(
    [
        "",
        "## Recommended Implementation Scope",
        "",
        "Improve deterministic extraction for explicit business-meeting language:",
        "",
        "- `Decision:` prefixes",
        "- `we decided to ...`",
        "- `we agreed to ...`",
        "- `we will ...` when stated as an outcome or decision",
        "- `we will not ...` for negative executive decisions",
        "- `Action item for OWNER: TASK`",
        "- `OWNER should ...`",
        "- `OWNER will ...` when the sentence clearly assigns work",
        "",
        "## Acceptance Criteria",
        "",
        "The next patch should raise the benchmark from 64/100 to at least 80/100 by improving:",
        "",
        "- decision recall across at least 4 of 5 benchmark cases",
        "- action recall across at least 4 of 5 benchmark cases",
        "- no regression to job completion",
        "- no regression to summary/key-point generation",
        "",
        "## Best-Practice Guardrail",
        "",
        "This should be implemented as a narrow extraction improvement, not as broad prompt-style rewriting. The goal is to improve structured recall while avoiding hallucinated decisions or fake owners.",
        "",
    ]
)

doc_path = Path("docs/pilot/pilot_rc1_decision_action_extraction_improvement_plan.md")
doc_path.parent.mkdir(parents=True, exist_ok=True)
doc_path.write_text("\n".join(report) + "\n")

print(f"Wrote {csv_path}")
print(f"Wrote {doc_path}")
