from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _action_key(item: dict[str, Any]) -> str:
    owner = _norm(item.get("owner")).lower()
    task = _norm(item.get("task")).lower()
    task = re.sub(r"[^a-z0-9]+", " ", task).strip()
    return f"{owner}:{task}"


def evaluate(path: Path) -> int:
    data = json.loads(path.read_text())

    decisions = data.get("decision_objects") or []
    actions = data.get("action_item_objects") or []
    slots = data.get("summary_slots") or {}
    next_steps = slots.get("next_steps") or []
    key_points = data.get("key_points") or []

    bad_decisions: list[Any] = []
    bad_actions: list[Any] = []
    bad_next_steps: list[Any] = []
    bad_key_points: list[Any] = []
    bad_summary_fields: list[str] = []
    duplicate_actions: list[Any] = []

    seen_actions: set[str] = set()
    has_weekly_priority_action = False

    _slots_for_summary_check = data.get("summary_slots") or {}
    for field_name, field_value in (
        ("summary", data.get("summary")),
        ("purpose", _slots_for_summary_check.get("purpose")),
        ("outcome", _slots_for_summary_check.get("outcome")),
    ):
        field_text = _norm(field_value).lower()
        if "i'd us" in field_text or "i’d us" in field_text:
            bad_summary_fields.append(f"{field_name}: {field_value}")

    for item in decisions:
        text = _norm(item.get("text")).lower()
        if text in {"and action items", "action items"} or text.startswith("and action"):
            bad_decisions.append(item)
        if (
            "target audience" in text
            and "finalized plan for the demo flow" in text
            and (
                "concrete owners for the follow-up actions" in text
                or "concrete owners for the follow up actions" in text
            )
        ):
            bad_decisions.append(item)

    for item in actions:
        owner = _norm(item.get("owner"))
        owner_lower = owner.lower()
        task = _norm(item.get("task"))
        task_lower = task.lower()

        if owner_lower.startswith("i also think") or owner_lower.startswith("i think"):
            bad_actions.append(item)

        if "be careful with what we claim publicly" in task_lower:
            bad_actions.append(item)

        if "for example, the product does handle short files well" in task_lower:
            bad_actions.append(item)

        if len(task_lower) > 220:
            bad_actions.append(item)

        if "weekly priorities" in task_lower or "priority" in task_lower:
            has_weekly_priority_action = True

        if owner == "Team" and ":" in task:
            bad_actions.append(item)
        if "the purpose of today's meeting" in task_lower:
            bad_actions.append(item)
        if "keep the launch scope focused on upload" in task_lower:
            bad_actions.append(item)
        if task_lower.startswith("s "):
            bad_actions.append(item)

        key = _action_key(item)
        if key in seen_actions:
            duplicate_actions.append(item)
        seen_actions.add(key)

    for step in next_steps:
        step_lower = _norm(step).lower()
        if "keep the launch scope focused on upload" in step_lower or step_lower.startswith("s "):
            bad_next_steps.append(step)

    for point in key_points:
        point_lower = _norm(point).lower()
        if "control.reach" in point_lower or "s keep" in point_lower:
            bad_key_points.append(point)
        if "i'd us" in point_lower or "i’d us" in point_lower:
            bad_key_points.append(point)
        if "be careful with what we claim publicly" in point_lower:
            bad_key_points.append(point)
        if "for example, the product does handle short files well" in point_lower:
            bad_key_points.append(point)

    score = 100
    if bad_summary_fields:
        score -= 25

    if len(decisions) < 3:
        score -= 15
    if len(actions) < 3:
        score -= 20
    if len(next_steps) < 3:
        score -= 15
    if not has_weekly_priority_action:
        score -= 15
    if bad_decisions:
        score -= 15
    if bad_actions:
        score -= 20
    if bad_next_steps:
        score -= 15
    if bad_key_points:
        score -= 10
    if duplicate_actions:
        score -= 10

    score = max(score, 0)

    print("CLIENT-FACING PILOT RC1 QUALITY GATE")
    print("-----------------------------------")
    print(f"input: {path}")
    print(f"decision_count: {len(decisions)}")
    print(f"action_count: {len(actions)}")
    print(f"next_steps_count: {len(next_steps)}")
    print(f"has_weekly_priority_action: {has_weekly_priority_action}")
    print(f"client_facing_score: {score}")
    print(f"bad_decisions: {bad_decisions}")
    print(f"bad_actions: {bad_actions}")
    print(f"bad_next_steps: {bad_next_steps}")
    print(f"bad_key_points: {bad_key_points}")
    print(f"bad_summary_fields: {bad_summary_fields}")
    print(f"duplicate_actions: {duplicate_actions}")
    print()

    passed = (
        score >= 95
        and len(decisions) >= 3
        and len(actions) >= 3
        and len(next_steps) >= 3
        and has_weekly_priority_action
        and not bad_decisions
        and not bad_actions
        and not bad_next_steps
        and not bad_key_points
        and not bad_summary_fields
        and not duplicate_actions
    )

    if passed:
        print("CLIENT_FACING_REHEARSAL_PASS")
        return 0

    print("CLIENT_FACING_REHEARSAL_REVIEW_NEEDED")
    return 1


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/quality_gates/pilot_rc1_client_facing_gate.py <notes_ai.json>")
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        return 2

    return evaluate(path)


if __name__ == "__main__":
    raise SystemExit(main())
