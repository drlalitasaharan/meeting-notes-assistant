from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_WORD_RE = re.compile(r"[a-z0-9]+")
_DATE_RE = re.compile(r"\b20\d{2}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?\b")

_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "use",
    "with",
    "will",
    "we",
    "was",
    "were",
    "should",
    "can",
    "could",
    "would",
}


@dataclass(frozen=True)
class RegressionEvalConfig:
    min_case_score: float = 0.70
    text_match_threshold: float = 0.52
    action_match_threshold: float = 0.55


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_manifest(fixture_dir: Path) -> dict[str, Any]:
    return load_json(fixture_dir / "manifest.json")


def load_expected_cases(fixture_dir: Path) -> list[dict[str, Any]]:
    manifest = load_manifest(fixture_dir)
    cases = manifest.get("cases", [])
    loaded: list[dict[str, Any]] = []

    for manifest_case in cases:
        if manifest_case.get("ground_truth_status") != "complete":
            continue

        expected_path = fixture_dir / manifest_case["expected_fixture"]
        expected = load_json(expected_path)
        loaded.append(
            {
                "manifest": manifest_case,
                "expected_path": str(expected_path),
                "expected": expected,
            }
        )

    return loaded


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).lower()
    text = text.replace("’", "'")
    return " ".join(_WORD_RE.findall(text))


def tokens(value: Any) -> set[str]:
    return {token for token in normalize_text(value).split() if token not in _STOP_WORDS}


def token_recall(expected: Any, actual: Any) -> float:
    expected_tokens = tokens(expected)
    if not expected_tokens:
        return 1.0

    actual_tokens = tokens(actual)
    if not actual_tokens:
        return 0.0

    return len(expected_tokens & actual_tokens) / len(expected_tokens)


def flatten_text(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, str):
        return [value]

    if isinstance(value, (int, float, bool)):
        return [str(value)]

    if isinstance(value, list):
        texts: list[str] = []
        for item in value:
            texts.extend(flatten_text(item))
        return texts

    if isinstance(value, dict):
        texts = []
        for key, item in value.items():
            if key in {"id", "meeting_id", "audio_file", "transcript_file", "source_metadata_file"}:
                continue
            texts.extend(flatten_text(item))
        return texts

    return [str(value)]


def _collect_values_by_key(value: Any, accepted_keys: set[str]) -> list[Any]:
    found: list[Any] = []

    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = key.lower()
            if normalized_key in accepted_keys:
                found.append(item)
            found.extend(_collect_values_by_key(item, accepted_keys))

    elif isinstance(value, list):
        for item in value:
            found.extend(_collect_values_by_key(item, accepted_keys))

    return found


def _candidate_texts(actual: dict[str, Any], accepted_keys: set[str]) -> list[str]:
    values = _collect_values_by_key(actual, accepted_keys)
    texts: list[str] = []
    for value in values:
        texts.extend(flatten_text(value))

    if texts:
        return texts

    # Fallback: if the product output stores details in a generic Markdown/notes blob,
    # still allow the evaluator to detect recall without requiring one exact schema.
    return flatten_text(actual)


def _expected_list(expected: dict[str, Any], key: str) -> list[Any]:
    value = expected.get(key, [])
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _best_text_match(expected_text: str, candidates: list[str]) -> dict[str, Any]:
    best_score = 0.0
    best_candidate = ""

    for candidate in candidates:
        score = token_recall(expected_text, candidate)
        if score > best_score:
            best_score = score
            best_candidate = candidate

    return {
        "score": round(best_score, 4),
        "candidate": best_candidate,
    }


def score_text_expectations(
    expected_items: list[Any],
    actual: dict[str, Any],
    accepted_actual_keys: set[str],
    threshold: float,
) -> dict[str, Any]:
    candidates = _candidate_texts(actual, accepted_actual_keys)
    details: list[dict[str, Any]] = []

    for item in expected_items:
        expected_text = " ".join(flatten_text(item))
        best = _best_text_match(expected_text, candidates)
        details.append(
            {
                "expected": expected_text,
                "matched": best["score"] >= threshold,
                "score": best["score"],
                "best_candidate": best["candidate"],
            }
        )

    matched = sum(1 for item in details if item["matched"])
    total = len(details)

    return {
        "matched": matched,
        "total": total,
        "recall": round(matched / total, 4) if total else 1.0,
        "details": details,
    }


def _action_candidates(actual: dict[str, Any]) -> list[Any]:
    accepted_keys = {
        "actions",
        "action",
        "action_items",
        "actionitems",
        "next_steps",
        "nextsteps",
        "expected_actions",
    }
    values = _collect_values_by_key(actual, accepted_keys)
    if not values:
        return []

    candidates: list[Any] = []
    for value in values:
        if isinstance(value, list):
            candidates.extend(value)
        else:
            candidates.append(value)
    return candidates


def _action_to_text(action: Any) -> str:
    if isinstance(action, dict):
        parts = [
            str(action.get("owner") or ""),
            str(action.get("action") or action.get("task") or action.get("description") or ""),
            str(action.get("deadline") or action.get("due_date") or ""),
        ]
        return " ".join(part for part in parts if part)
    return " ".join(flatten_text(action))


def _owner_matches(expected: dict[str, Any], actual_candidate: Any) -> bool:
    expected_owner = normalize_text(expected.get("owner"))
    if not expected_owner:
        return True

    if isinstance(actual_candidate, dict):
        actual_owner = normalize_text(
            actual_candidate.get("owner") or actual_candidate.get("assignee")
        )
        if actual_owner and expected_owner == actual_owner:
            return True

    return expected_owner in normalize_text(_action_to_text(actual_candidate))


def _deadline_matches(expected: dict[str, Any], actual_candidate: Any) -> bool:
    expected_deadline = expected.get("deadline")
    if not expected_deadline:
        return True

    expected_dates = set(_DATE_RE.findall(str(expected_deadline)))
    actual_dates = set(_DATE_RE.findall(_action_to_text(actual_candidate)))

    if not expected_dates:
        return True
    return bool(expected_dates & actual_dates)


def score_action_expectations(
    expected_actions: list[Any],
    actual: dict[str, Any],
    threshold: float,
) -> dict[str, Any]:
    candidates = _action_candidates(actual)
    if not candidates:
        candidates = flatten_text(actual)

    details: list[dict[str, Any]] = []

    for expected_action in expected_actions:
        expected_dict = (
            expected_action
            if isinstance(expected_action, dict)
            else {"action": str(expected_action)}
        )
        expected_text = str(expected_dict.get("action") or expected_dict)

        best_score = 0.0
        best_candidate = ""

        for candidate in candidates:
            candidate_text = _action_to_text(candidate)
            text_score = token_recall(expected_text, candidate_text)
            owner_score = 1.0 if _owner_matches(expected_dict, candidate) else 0.0
            deadline_score = 1.0 if _deadline_matches(expected_dict, candidate) else 0.0

            combined = (0.75 * text_score) + (0.20 * owner_score) + (0.05 * deadline_score)
            if combined > best_score:
                best_score = combined
                best_candidate = candidate_text

        details.append(
            {
                "expected": expected_dict,
                "matched": best_score >= threshold,
                "score": round(best_score, 4),
                "best_candidate": best_candidate,
            }
        )

    matched = sum(1 for item in details if item["matched"])
    total = len(details)

    return {
        "matched": matched,
        "total": total,
        "recall": round(matched / total, 4) if total else 1.0,
        "details": details,
    }


def weighted_case_score(metrics: dict[str, dict[str, Any]]) -> float:
    weights = {
        "decisions": 0.30,
        "actions": 0.40,
        "risks": 0.15,
        "context": 0.15,
    }

    active_weight = 0.0
    score = 0.0

    for name, weight in weights.items():
        metric = metrics.get(name)
        if not metric or metric.get("total", 0) == 0:
            continue
        active_weight += weight
        score += weight * float(metric.get("recall", 0.0))

    if active_weight == 0:
        return 1.0

    return round(score / active_weight, 4)


def evaluate_case(
    expected: dict[str, Any],
    actual: dict[str, Any],
    config: RegressionEvalConfig | None = None,
) -> dict[str, Any]:
    config = config or RegressionEvalConfig()

    metrics = {
        "decisions": score_text_expectations(
            _expected_list(expected, "expected_decisions"),
            actual,
            {"decisions", "decision", "expected_decisions"},
            config.text_match_threshold,
        ),
        "actions": score_action_expectations(
            _expected_list(expected, "expected_actions"),
            actual,
            config.action_match_threshold,
        ),
        "risks": score_text_expectations(
            _expected_list(expected, "expected_risks"),
            actual,
            {"risks", "risk", "expected_risks"},
            config.text_match_threshold,
        ),
        "context": score_text_expectations(
            _expected_list(expected, "expected_context"),
            actual,
            {"context", "purpose", "outcome", "summary", "expected_context"},
            config.text_match_threshold,
        ),
    }

    score = weighted_case_score(metrics)

    return {
        "id": expected.get("id"),
        "title": expected.get("title"),
        "category": expected.get("category"),
        "score": score,
        "passed": score >= config.min_case_score,
        "metrics": metrics,
    }


def find_actual_path(actual_dir: Path, expected_path: Path, case_id: str) -> Path | None:
    expected_stem = expected_path.name.replace(".expected.json", "")
    candidates = [
        actual_dir / f"{case_id}.json",
        actual_dir / f"{expected_stem}.json",
        actual_dir / f"{expected_stem}.actual.json",
        actual_dir / expected_path.name,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


def evaluate_manifest(
    fixture_dir: Path,
    actual_dir: Path | None = None,
    *,
    self_check: bool = False,
    case_ids: set[str] | None = None,
    config: RegressionEvalConfig | None = None,
) -> dict[str, Any]:
    config = config or RegressionEvalConfig()
    cases = load_expected_cases(fixture_dir)
    results: list[dict[str, Any]] = []

    for loaded in cases:
        manifest_case = loaded["manifest"]
        expected_path = Path(loaded["expected_path"])
        expected = loaded["expected"]

        case_id = str(expected.get("id") or manifest_case.get("id"))
        if case_ids and case_id not in case_ids:
            continue

        if self_check:
            actual = expected
            actual_path = str(expected_path)
        else:
            if actual_dir is None:
                raise ValueError("actual_dir is required unless self_check=True")

            found_actual_path = find_actual_path(actual_dir, expected_path, case_id)
            if found_actual_path is None:
                results.append(
                    {
                        "id": case_id,
                        "title": expected.get("title"),
                        "category": expected.get("category"),
                        "score": 0.0,
                        "passed": False,
                        "error": f"No actual output found in {actual_dir}",
                    }
                )
                continue

            actual = load_json(found_actual_path)
            actual_path = str(found_actual_path)

        result = evaluate_case(expected, actual, config)
        result["expected_path"] = str(expected_path)
        result["actual_path"] = actual_path
        results.append(result)

    passed = sum(1 for result in results if result.get("passed"))
    total = len(results)
    average_score = (
        round(
            sum(float(result.get("score", 0.0)) for result in results) / total,
            4,
        )
        if total
        else 1.0
    )

    return {
        "total_cases": total,
        "passed_cases": passed,
        "failed_cases": total - passed,
        "average_score": average_score,
        "passed": passed == total,
        "results": results,
    }
