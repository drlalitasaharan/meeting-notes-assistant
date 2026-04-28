#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def flatten_strings(obj: Any) -> list[str]:
    values: list[str] = []

    if isinstance(obj, str):
        values.append(obj)
    elif isinstance(obj, dict):
        for value in obj.values():
            values.extend(flatten_strings(value))
    elif isinstance(obj, list):
        for item in obj:
            values.extend(flatten_strings(item))

    return values


def collect_dicts(obj: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []

    if isinstance(obj, dict):
        found.append(obj)
        for value in obj.values():
            found.extend(collect_dicts(value))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(collect_dicts(item))

    return found


def collect_lists_by_key(obj: Any, target_keys: set[str]) -> list[list[Any]]:
    lists: list[list[Any]] = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.lower() in target_keys and isinstance(value, list):
                lists.append(value)
            lists.extend(collect_lists_by_key(value, target_keys))
    elif isinstance(obj, list):
        for item in obj:
            lists.extend(collect_lists_by_key(item, target_keys))

    return lists


def is_action_like(item: dict[str, Any]) -> bool:
    keys = {str(key).lower() for key in item}
    task = str(item.get("task") or item.get("action") or item.get("description") or "").strip()
    return bool(task) and (
        "task" in keys
        or "owner" in keys
        or "due_date" in keys
        or "priority" in keys
        or "status" in keys
    )


def is_decision_like(item: dict[str, Any]) -> bool:
    keys = {str(key).lower() for key in item}
    decision = str(item.get("decision") or item.get("text") or item.get("summary") or "").strip()
    return bool(decision) and ("decision" in keys or "rationale" in keys)


def collect_actions(notes: Any) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    for list_value in collect_lists_by_key(notes, {"action_items", "actions"}):
        for item in list_value:
            if isinstance(item, dict) and is_action_like(item):
                actions.append(item)

    for item in collect_dicts(notes):
        if is_action_like(item):
            actions.append(item)

    unique: dict[str, dict[str, Any]] = {}
    for action in actions:
        task = str(
            action.get("task") or action.get("action") or action.get("description") or ""
        ).strip()
        if not task:
            continue
        key = normalize_text(task)
        unique[key] = action

    return list(unique.values())


def collect_decisions(notes: Any) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []

    for list_value in collect_lists_by_key(notes, {"decisions"}):
        for item in list_value:
            if isinstance(item, dict):
                decisions.append(item)
            elif isinstance(item, str) and item.strip():
                decisions.append({"decision": item.strip()})

    for item in collect_dicts(notes):
        if is_decision_like(item):
            decisions.append(item)

    unique: dict[str, dict[str, Any]] = {}
    for decision in decisions:
        text = str(
            decision.get("decision") or decision.get("text") or decision.get("summary") or ""
        ).strip()
        if not text:
            text = json.dumps(decision, sort_keys=True)
        key = normalize_text(text)
        unique[key] = decision

    return list(unique.values())


def has_summary(notes: Any) -> bool:
    strings = [s.strip() for s in flatten_strings(notes) if isinstance(s, str)]
    long_strings = [s for s in strings if len(s.split()) >= 8]
    joined = " ".join(strings).lower()
    has_summary_key_signal = any(
        signal in joined
        for signal in ["summary", "purpose", "outcome", "overview", "key points", "next steps"]
    )
    return bool(long_strings and has_summary_key_signal)


def markdown_is_publishable(markdown_path: Path | None) -> bool:
    if markdown_path is None or not markdown_path.exists():
        return False

    text = markdown_path.read_text(encoding="utf-8", errors="replace")
    if len(text.strip()) < 100:
        return False

    bad_signals = [
        "traceback",
        "exception",
        "undefined",
        "null null",
        "none none",
        "[object object]",
    ]
    lower = text.lower()
    return not any(signal in lower for signal in bad_signals)


def duplicate_action_count(actions: list[dict[str, Any]]) -> int:
    seen: set[str] = set()
    duplicates = 0

    for action in actions:
        task = str(action.get("task") or action.get("action") or action.get("description") or "")
        key = normalize_text(task)
        if not key:
            continue
        if key in seen:
            duplicates += 1
        seen.add(key)

    return duplicates


def owner_coverage(actions: list[dict[str, Any]]) -> float:
    if not actions:
        return 0.0

    with_owner = 0
    for action in actions:
        owner = str(action.get("owner") or "").strip()
        if owner:
            with_owner += 1

    return with_owner / len(actions)


def due_date_coverage(actions: list[dict[str, Any]]) -> float:
    if not actions:
        return 0.0

    with_due_date = 0
    for action in actions:
        due_date = str(action.get("due_date") or action.get("due") or "").strip()
        if due_date:
            with_due_date += 1

    return with_due_date / len(actions)


def safety_signal(notes: Any, markdown_path: Path | None) -> bool:
    text = " ".join(flatten_strings(notes))

    if markdown_path is not None and markdown_path.exists():
        text += " " + markdown_path.read_text(encoding="utf-8", errors="replace")

    lower = text.lower()
    return any(
        signal in lower
        for signal in [
            "no clear meeting structure",
            "not a meeting",
            "no clear decisions",
            "no clear action items",
            "insufficient meeting structure",
            "meeting structure was detected",
            "unclear meeting",
        ]
    )


def score_sample(sample_name: str, notes_path: Path, markdown_path: Path | None) -> dict[str, Any]:
    notes = json.loads(notes_path.read_text(encoding="utf-8"))

    actions = collect_actions(notes)
    decisions = collect_decisions(notes)

    is_non_meeting = "meeting_86" in sample_name.lower()

    summary_ok = has_summary(notes)
    markdown_ok = markdown_is_publishable(markdown_path)
    duplicates = duplicate_action_count(actions)
    owner_rate = owner_coverage(actions)
    due_rate = due_date_coverage(actions)
    safety_ok = safety_signal(notes, markdown_path)

    if is_non_meeting:
        action_ok = len(actions) <= 1
        decision_ok = len(decisions) <= 1
        score = 0
        score += 20 if summary_ok else 8
        score += 25 if action_ok else 0
        score += 25 if decision_ok else 0
        score += 20 if safety_ok else 8
        score += 10 if markdown_ok else 0
        status = "PASS" if score >= 85 and action_ok and decision_ok else "REVIEW"
    else:
        expected_min_actions = (
            2 if any(x in sample_name.lower() for x in ["30min", "meeting_81"]) else 1
        )
        expected_min_decisions = 1

        action_ok = len(actions) >= expected_min_actions
        decision_ok = len(decisions) >= expected_min_decisions

        score = 0
        score += 15 if summary_ok else 5
        score += 20 if action_ok else max(0, 10 * len(actions))
        score += 15 if decision_ok else max(0, 8 * len(decisions))
        score += 15 if owner_rate >= 0.5 else int(owner_rate * 15)
        score += 10 if duplicates == 0 else 3
        score += 10 if markdown_ok else 0
        score += 5 if due_rate > 0 else 2
        score += 10

        status = "PASS" if score >= 85 and action_ok and decision_ok and markdown_ok else "REVIEW"

    return {
        "sample": sample_name,
        "status": status,
        "score": min(score, 100),
        "summary_ok": summary_ok,
        "actions_count": len(actions),
        "decisions_count": len(decisions),
        "owner_coverage": round(owner_rate, 2),
        "due_date_coverage": round(due_rate, 2),
        "duplicate_actions": duplicates,
        "markdown_ok": markdown_ok,
        "safety_signal": safety_ok,
        "notes_json": str(notes_path),
        "markdown": str(markdown_path) if markdown_path else "",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--csv", required=True)
    parser.add_argument("--markdown", required=True)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    rows: list[dict[str, Any]] = []

    for notes_path in sorted(out_dir.glob("*/notes_ai.json")):
        sample_dir = notes_path.parent
        sample_name = sample_dir.name
        markdown_path = sample_dir / "notes.md"

        try:
            rows.append(score_sample(sample_name, notes_path, markdown_path))
        except Exception as exc:
            rows.append(
                {
                    "sample": sample_name,
                    "status": "ERROR",
                    "score": 0,
                    "summary_ok": False,
                    "actions_count": 0,
                    "decisions_count": 0,
                    "owner_coverage": 0,
                    "due_date_coverage": 0,
                    "duplicate_actions": 0,
                    "markdown_ok": False,
                    "safety_signal": False,
                    "notes_json": str(notes_path),
                    "markdown": str(markdown_path),
                    "error": str(exc),
                }
            )

    fieldnames = [
        "sample",
        "status",
        "score",
        "summary_ok",
        "actions_count",
        "decisions_count",
        "owner_coverage",
        "due_date_coverage",
        "duplicate_actions",
        "markdown_ok",
        "safety_signal",
        "notes_json",
        "markdown",
    ]

    with Path(args.csv).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    if rows:
        average_score = round(sum(int(row["score"]) for row in rows) / len(rows), 1)
    else:
        average_score = 0

    pass_count = sum(1 for row in rows if row["status"] == "PASS")

    lines = [
        "# Pilot RC1 Golden Consistency Gate Scorecard",
        "",
        f"Overall average score: {average_score}",
        f"Passing samples: {pass_count}/{len(rows)}",
        "",
        "| Sample | Status | Score | Actions | Decisions | Markdown | Safety Signal |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    for row in rows:
        lines.append(
            "| {sample} | {status} | {score} | {actions_count} | {decisions_count} | {markdown_ok} | {safety_signal} |".format(
                **row
            )
        )

    lines.extend(
        [
            "",
            "## Review notes",
            "",
            "- Meeting 86 should avoid fake decisions and fake action items.",
            "- Meeting 81 should preserve useful decisions and action items.",
            "- 30-minute meetings should capture final next steps.",
            "- Action items should be specific, owner-aware, and non-duplicated.",
            "- Markdown should be clean and client-facing.",
        ]
    )

    Path(args.markdown).write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
