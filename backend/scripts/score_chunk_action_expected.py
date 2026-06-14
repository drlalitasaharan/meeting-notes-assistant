from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def normalize_action(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"^\s*[-*]\s*", "", text)
    text = re.sub(r"^\[[ xX]\]\s*", "", text)

    # Exact-match scoring compares the task sentence, not display owner labels.
    # Product output may prefix actions as "Unassigned - task",
    # "Jordan: task", or "**Jordan** — task". Strip that prefix first.
    text = re.sub(r"^\*\*[^*]{1,80}\*\*\s*[—–:-]\s+", "", text)
    text = re.sub(r"^[a-z0-9][a-z0-9 ._'()/&]{0,80}\s*[—–:-]\s+", "", text)

    text = text.replace("—", " ").replace("–", " ").replace("-", " ").replace(":", " ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_bullet(line: str) -> str:
    value = re.sub(r"^\s*[-*]\s*", "", line.strip())
    value = re.sub(r"^\[[ xX]\]\s*", "", value)
    return value.strip().rstrip(".")


def is_metadata_bullet(value: str) -> bool:
    low = value.lower().strip()
    if not low or low in {"none", "n/a", "no action items", "no actions"}:
        return True
    prefixes = (
        "capture type",
        "meeting id",
        "status",
        "source endpoint",
        "source file",
        "duration seconds",
        "expected absent",
        "model version",
    )
    return any(low.startswith(prefix + ":") for prefix in prefixes)


def section_bullets(text: str, section_keyword: str) -> list[str]:
    bullets: list[str] = []
    in_section = False

    for line in text.splitlines():
        stripped = line.strip()

        if stripped.startswith("## "):
            title = stripped.lstrip("#").strip().lower()
            in_section = title == section_keyword.lower()
            continue

        if in_section and stripped.startswith("#"):
            break

        if in_section and stripped.startswith(("-", "*")):
            bullet = clean_bullet(stripped)
            if not is_metadata_bullet(bullet):
                bullets.append(bullet)

    return bullets


def extract_expected_actions(path: Path) -> list[str]:
    text = path.read_text()

    # Exact-match scoring must only read machine-readable expected-action sections.
    # It must not treat acceptance criteria, forbidden examples, or behavior notes as expected actions.
    for section in ("expected action items", "expected actions", "must-capture actions"):
        bullets = section_bullets(text, section)
        if bullets:
            return bullets

    return []


def load_json_block(text: str) -> dict[str, Any] | None:
    blocks = re.findall(r"```json\s*\n(.*?)\n```", text, flags=re.DOTALL)
    for block in reversed(blocks):
        try:
            payload = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return None


def extract_after_actions(path: Path) -> list[str]:
    text = path.read_text()
    payload = load_json_block(text)

    if payload:
        action_items = payload.get("action_items")
        if isinstance(action_items, list):
            return [str(item).strip() for item in action_items if str(item).strip()]

        action_objects = payload.get("action_item_objects")
        if isinstance(action_objects, list):
            actions: list[str] = []
            for item in action_objects:
                if not isinstance(item, dict):
                    continue
                text_value = str(item.get("text") or "").strip()
                owner = str(item.get("owner") or "").strip()
                task = str(item.get("task") or "").strip()

                if text_value:
                    actions.append(text_value)
                elif owner and task:
                    actions.append(f"{owner} - {task}")
                elif task:
                    actions.append(task)
            return actions

    return section_bullets(text, "action items")


def unique_by_norm(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        norm = normalize_action(value)
        if norm:
            result.setdefault(norm, value)
    return result


def score_case(case: dict[str, Any], min_precision: float, min_recall: float) -> dict[str, Any]:
    case_id = str(case["id"])
    expected_path = Path(str(case["expected"]))
    after_value = case.get("after")
    after_path = Path(str(after_value)) if after_value else None

    expected_by_norm = unique_by_norm(extract_expected_actions(expected_path))

    if after_path is None or not after_path.exists():
        expected_count = len(expected_by_norm)
        return {
            "case_id": case_id,
            "status": "MISSING_AFTER_EVIDENCE",
            "expected_count": expected_count,
            "actual_count": 0,
            "matched_count": 0,
            "missing_count": expected_count,
            "unexpected_count": 0,
            "precision": 0.0 if expected_count else 1.0,
            "recall": 0.0 if expected_count else 1.0,
            "f1": 0.0 if expected_count else 1.0,
            "missing_expected_actions": list(expected_by_norm.values()),
            "unexpected_actual_actions": [],
        }

    actual_by_norm = unique_by_norm(extract_after_actions(after_path))

    expected_norms = set(expected_by_norm)
    actual_norms = set(actual_by_norm)
    matched = expected_norms & actual_norms
    missing = expected_norms - actual_norms
    unexpected = actual_norms - expected_norms

    if not expected_norms and not actual_norms:
        precision = recall = f1 = 1.0
    else:
        precision = len(matched) / len(actual_norms) if actual_norms else 0.0
        recall = len(matched) / len(expected_norms) if expected_norms else 1.0
        f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)

    status = "PASS" if precision >= min_precision and recall >= min_recall else "FAIL"

    return {
        "case_id": case_id,
        "status": status,
        "expected_count": len(expected_norms),
        "actual_count": len(actual_norms),
        "matched_count": len(matched),
        "missing_count": len(missing),
        "unexpected_count": len(unexpected),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "missing_expected_actions": [expected_by_norm[n] for n in sorted(missing)],
        "unexpected_actual_actions": [actual_by_norm[n] for n in sorted(unexpected)],
    }


def write_markdown_report(path: Path, results: list[dict[str, Any]]) -> None:
    lines = [
        "# Chunk Action Exact-Match Scorer Report",
        "",
        "| Case | Expected | Matched | Missing | Unexpected | Precision | Recall | F1 | Status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]

    for result in results:
        lines.append(
            "| {case_id} | {expected_count} | {matched_count} | {missing_count} | "
            "{unexpected_count} | {precision:.2f} | {recall:.2f} | {f1:.2f} | {status} |".format(
                **result
            )
        )

    lines.extend(["", "## Details", ""])

    for result in results:
        lines.extend([f"### {result['case_id']}", "", f"Status: **{result['status']}**", ""])

        lines.append("Missing expected actions:")
        missing = result.get("missing_expected_actions", [])
        lines.extend([f"- {item}" for item in missing] or ["- None"])

        lines.append("")
        lines.append("Unexpected actual actions:")
        unexpected = result.get("unexpected_actual_actions", [])
        lines.extend([f"- {item}" for item in unexpected] or ["- None"])
        lines.append("")

    path.write_text("\n".join(lines).rstrip() + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--min-precision", type=float, default=0.85)
    parser.add_argument("--min-recall", type=float, default=0.85)
    parser.add_argument("--allow-missing-after", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text())
    cases = manifest.get("cases")
    if not isinstance(cases, list):
        raise ValueError("Manifest must contain a top-level cases list.")

    results = [
        score_case(case, min_precision=args.min_precision, min_recall=args.min_recall)
        for case in cases
    ]

    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    out_json.write_text(json.dumps({"results": results}, indent=2, sort_keys=True) + "\n")
    write_markdown_report(out_md, results)

    failures = [
        result
        for result in results
        if result["status"] != "PASS"
        and not (args.allow_missing_after and result["status"] == "MISSING_AFTER_EVIDENCE")
    ]

    if failures:
        print(f"FAIL: {len(failures)} case(s) failed scorer thresholds.")
        return 1

    print("PASS: scorer report generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
