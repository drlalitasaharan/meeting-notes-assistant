from __future__ import annotations

import argparse
import asyncio
import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"

for candidate in (REPO_ROOT, BACKEND_ROOT):
    candidate_text = str(candidate)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)

from backend.app.services.meeting_regression_evaluator import (  # noqa: E402
    RegressionEvalConfig,
    evaluate_manifest,
    load_expected_cases,
)

SummarizerCallable = Callable[..., Any]


SUMMARIZER_CANDIDATES = [
    ("backend.app.services.summarize", "summarize_transcript"),
    ("backend.app.services.summarize", "summarize_meeting"),
    ("backend.app.services.summarize", "summarize_text"),
    ("backend.app.services.summarize", "summarize"),
    ("backend.app.summarizers", "summarize_transcript"),
    ("backend.app.summarizers", "summarize_meeting"),
    ("backend.app.summarizers", "summarize_text"),
    ("backend.app.summarizers", "summarize"),
    ("app.services.summarize", "summarize_transcript"),
    ("app.services.summarize", "summarize_meeting"),
    ("app.services.summarize", "summarize_text"),
    ("app.services.summarize", "summarize"),
    ("app.summarizers", "summarize_transcript"),
    ("app.summarizers", "summarize_meeting"),
    ("app.summarizers", "summarize_text"),
    ("app.summarizers", "summarize"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate transcript-based MeetIQ regression baseline actual outputs "
            "and evaluate them against expected fixture JSON."
        )
    )
    parser.add_argument(
        "--fixture-dir",
        default="backend/tests/fixtures/meeting_regression",
        help="Directory containing manifest.json and regression fixtures.",
    )
    parser.add_argument(
        "--actual-dir",
        default="backend/tests/tmp/meeting_regression_actual",
        help="Directory where generated actual JSON outputs will be written.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to write the combined baseline report JSON.",
    )
    parser.add_argument(
        "--case",
        action="append",
        default=[],
        help="Run only one case id. Can be repeated, e.g. --case S01 --case L01.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.70,
        help="Minimum weighted case score required to pass.",
    )
    parser.add_argument(
        "--text-threshold",
        type=float,
        default=0.52,
        help="Token-recall threshold for decisions, risks, and context.",
    )
    parser.add_argument(
        "--action-threshold",
        type=float,
        default=0.55,
        help="Combined action/owner/deadline threshold for action matches.",
    )
    parser.add_argument(
        "--allow-fail",
        action="store_true",
        help="Exit zero even when baseline scores fail. Useful for recording first baseline.",
    )
    parser.add_argument(
        "--list-cases",
        action="store_true",
        help="List transcript-backed cases and exit.",
    )
    return parser.parse_args()


def _case_id(loaded_case: dict[str, Any]) -> str:
    expected = loaded_case["expected"]
    manifest = loaded_case["manifest"]
    return str(expected.get("id") or manifest.get("id"))


def _expected_stem(loaded_case: dict[str, Any]) -> str:
    expected_path = Path(loaded_case["expected_path"])
    return expected_path.name.replace(".expected.json", "")


def transcript_path_for_case(fixture_dir: Path, loaded_case: dict[str, Any]) -> Path | None:
    expected = loaded_case["expected"]
    manifest = loaded_case["manifest"]

    transcript_file = expected.get("transcript_file") or manifest.get("transcript_file")
    candidates: list[Path] = []

    if transcript_file:
        candidates.append(fixture_dir / str(transcript_file))

    candidates.append(fixture_dir / f"{_expected_stem(loaded_case)}.txt")

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


def normalize_actual_output(raw_output: Any) -> dict[str, Any]:
    if raw_output is None:
        return {}

    if hasattr(raw_output, "model_dump"):
        raw_output = raw_output.model_dump()

    if hasattr(raw_output, "dict") and not isinstance(raw_output, dict):
        raw_output = raw_output.dict()

    if isinstance(raw_output, dict):
        return raw_output

    if isinstance(raw_output, list):
        return {
            "summary": raw_output,
            "notes": raw_output,
            "decisions": raw_output,
            "action_items": raw_output,
            "risks": raw_output,
            "context": raw_output,
        }

    text = str(raw_output)
    return {
        "summary": text,
        "notes_markdown": text,
        "decisions": text,
        "action_items": text,
        "risks": text,
        "context": text,
    }


def resolve_summarizer() -> tuple[str, SummarizerCallable]:
    attempted: list[str] = []

    for module_name, function_name in SUMMARIZER_CANDIDATES:
        attempted.append(f"{module_name}.{function_name}")

        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue

        function = getattr(module, function_name, None)
        if callable(function):
            return f"{module_name}.{function_name}", function

    attempted_text = "\n  - ".join(attempted)
    raise RuntimeError(
        "Could not find a compatible transcript summarizer function. Tried:\n  - " + attempted_text
    )


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


async def call_summarizer(function: SummarizerCallable, transcript: str) -> dict[str, Any]:
    call_attempts = [
        lambda: function(transcript),
        lambda: function(transcript=transcript),
        lambda: function(text=transcript),
        lambda: function(meeting_text=transcript),
    ]

    errors: list[str] = []

    for call in call_attempts:
        try:
            result = call()
            result = await _maybe_await(result)
            return normalize_actual_output(result)
        except TypeError as exc:
            errors.append(str(exc))
            continue

    raise RuntimeError("Could not call summarizer with supported signatures: " + " | ".join(errors))


def write_actual_json(
    actual_dir: Path,
    loaded_case: dict[str, Any],
    actual: dict[str, Any],
    *,
    summarizer_name: str,
    transcript_path: Path,
) -> Path:
    case_id = _case_id(loaded_case)
    expected_stem = _expected_stem(loaded_case)
    actual_dir.mkdir(parents=True, exist_ok=True)

    enriched_actual = dict(actual)
    enriched_actual.setdefault("_regression_case_id", case_id)
    enriched_actual.setdefault("_baseline_source", "transcript")
    enriched_actual.setdefault("_summarizer", summarizer_name)
    enriched_actual.setdefault("_transcript_path", str(transcript_path))

    path = actual_dir / f"{expected_stem}.actual.json"
    path.write_text(json.dumps(enriched_actual, indent=2), encoding="utf-8")
    return path


async def generate_actual_outputs(
    fixture_dir: Path,
    actual_dir: Path,
    selected_case_ids: set[str] | None,
) -> dict[str, Any]:
    loaded_cases = load_expected_cases(fixture_dir)
    summarizer_name, summarizer = resolve_summarizer()

    generated_case_ids: set[str] = set()
    generated: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    failed_generation: list[dict[str, Any]] = []

    for loaded_case in loaded_cases:
        case_id = _case_id(loaded_case)
        if selected_case_ids and case_id not in selected_case_ids:
            continue

        transcript_path = transcript_path_for_case(fixture_dir, loaded_case)
        if transcript_path is None:
            skipped.append(
                {
                    "id": case_id,
                    "reason": "missing transcript fixture",
                    "expected_path": loaded_case["expected_path"],
                }
            )
            continue

        transcript = transcript_path.read_text(encoding="utf-8")

        try:
            actual = await call_summarizer(summarizer, transcript)
            actual_path = write_actual_json(
                actual_dir,
                loaded_case,
                actual,
                summarizer_name=summarizer_name,
                transcript_path=transcript_path,
            )
            generated_case_ids.add(case_id)
            generated.append(
                {
                    "id": case_id,
                    "actual_path": str(actual_path),
                    "transcript_path": str(transcript_path),
                }
            )
        except Exception as exc:
            failed_generation.append(
                {
                    "id": case_id,
                    "error": str(exc),
                    "transcript_path": str(transcript_path),
                }
            )

    return {
        "summarizer": summarizer_name,
        "generated_case_ids": sorted(generated_case_ids),
        "generated": generated,
        "skipped": skipped,
        "generation_failures": failed_generation,
    }


def print_case_list(fixture_dir: Path) -> None:
    loaded_cases = load_expected_cases(fixture_dir)

    print("Transcript-backed regression cases:")
    for loaded_case in loaded_cases:
        case_id = _case_id(loaded_case)
        category = loaded_case["expected"].get("category")
        transcript_path = transcript_path_for_case(fixture_dir, loaded_case)
        status = "transcript" if transcript_path else "no transcript"
        print(f"- {case_id} [{category}] {status}")


async def async_main() -> int:
    args = parse_args()

    fixture_dir = Path(args.fixture_dir)
    actual_dir = Path(args.actual_dir)

    if not fixture_dir.exists():
        print(f"ERROR: fixture directory not found: {fixture_dir}", file=sys.stderr)
        return 2

    if args.list_cases:
        print_case_list(fixture_dir)
        return 0

    selected_case_ids = set(args.case) if args.case else None

    generation_report = await generate_actual_outputs(
        fixture_dir,
        actual_dir,
        selected_case_ids,
    )

    generated_case_ids = set(generation_report["generated_case_ids"])

    if generated_case_ids:
        config = RegressionEvalConfig(
            min_case_score=args.min_score,
            text_match_threshold=args.text_threshold,
            action_match_threshold=args.action_threshold,
        )

        eval_report = evaluate_manifest(
            fixture_dir,
            actual_dir,
            case_ids=generated_case_ids,
            config=config,
        )
    else:
        eval_report = {
            "total_cases": 0,
            "passed_cases": 0,
            "failed_cases": 0,
            "average_score": 0.0,
            "passed": False,
            "results": [],
        }

    combined_report = {
        "mode": "transcript_baseline",
        "fixture_dir": str(fixture_dir),
        "actual_dir": str(actual_dir),
        "generation": generation_report,
        "evaluation": eval_report,
    }

    print(
        "Meeting regression transcript baseline:"
        f" {eval_report['passed_cases']}/{eval_report['total_cases']} passed,"
        f" average_score={eval_report['average_score']}"
    )
    print(f"Summarizer: {generation_report['summarizer']}")

    if generation_report["skipped"]:
        print(f"Skipped missing-transcript cases: {len(generation_report['skipped'])}")
        for skipped in generation_report["skipped"]:
            print(f"SKIP {skipped['id']}: {skipped['reason']}")

    if generation_report["generation_failures"]:
        print(f"Generation failures: {len(generation_report['generation_failures'])}")
        for failure in generation_report["generation_failures"]:
            print(f"ERROR {failure['id']}: {failure['error']}")

    for result in eval_report["results"]:
        status = "PASS" if result.get("passed") else "FAIL"
        print(
            f"{status} {result.get('id')} [{result.get('category')}] "
            f"score={result.get('score', 0.0)}"
        )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(combined_report, indent=2), encoding="utf-8")
        print(f"Wrote baseline report: {output_path}")

    if generation_report["generation_failures"]:
        return 0 if args.allow_fail else 1

    if eval_report["passed"]:
        return 0

    return 0 if args.allow_fail else 1


def main() -> int:
    return asyncio.run(async_main())


if __name__ == "__main__":
    raise SystemExit(main())
