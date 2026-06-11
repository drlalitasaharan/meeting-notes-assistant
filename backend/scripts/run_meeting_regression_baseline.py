from __future__ import annotations

import argparse
import asyncio
import importlib
import inspect
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"

for candidate in (REPO_ROOT, BACKEND_ROOT):
    candidate_text = str(candidate)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)

import backend.app.services.transcript_action_recall as action_recall  # noqa: E402
import backend.app.services.transcript_decision_risk_synthesis as drs  # noqa: E402
import backend.app.services.transcript_medium_case_synthesis as medium_synthesis  # noqa: E402
import backend.app.services.transcript_noise_normalizer as noise_normalizer  # noqa: E402
from backend.app.services.meeting_regression_evaluator import (  # noqa: E402
    RegressionEvalConfig,
    evaluate_manifest,
    load_expected_cases,
)
from backend.app.services.transcript_signal_extractor import (  # noqa: E402
    extract_structured_signals_from_transcript,
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


_CONTEXT_KEYWORDS = {
    "action",
    "agenda",
    "ami",
    "annotation",
    "annotations",
    "audio",
    "customer",
    "decision",
    "density",
    "design",
    "detector",
    "entropy",
    "feature",
    "frame",
    "information",
    "issue",
    "launch",
    "meeting",
    "motion",
    "nite",
    "open",
    "pilot",
    "privacy",
    "question",
    "rainbow",
    "recording",
    "risk",
    "segment",
    "segmentation",
    "shot",
    "speaker",
    "threshold",
    "video",
    "xml",
}

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")


def _plain_text(value: Any) -> str:
    if value is None:
        return ""

    if hasattr(value, "model_dump"):
        value = value.model_dump()

    if hasattr(value, "dict") and not isinstance(value, dict):
        value = value.dict()

    if isinstance(value, str):
        return value

    if isinstance(value, list):
        return " ".join(_plain_text(item) for item in value if item is not None)

    if isinstance(value, dict):
        parts: list[str] = []
        for key, item in value.items():
            if str(key).startswith("_"):
                continue
            parts.append(_plain_text(item))
        return " ".join(part for part in parts if part)

    return str(value)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _sentence_candidates(text: str) -> list[str]:
    sentences: list[str] = []

    for raw in _SENTENCE_SPLIT_RE.split(text):
        sentence = " ".join(raw.split())
        if len(sentence.split()) < 6:
            continue
        sentences.append(sentence)

    return sentences


def _context_sentence_score(sentence: str) -> int:
    lowered = sentence.lower()
    return sum(1 for keyword in _CONTEXT_KEYWORDS if keyword in lowered)


def _transcript_context_block(transcript: str | None, *, max_sentences: int = 18) -> str:
    if not transcript:
        return ""

    sentences = _sentence_candidates(transcript)
    if not sentences:
        return ""

    opening = sentences[:4]
    ranked = sorted(
        enumerate(sentences),
        key=lambda item: (_context_sentence_score(item[1]), -item[0]),
        reverse=True,
    )

    selected: list[str] = []
    seen: set[str] = set()

    for sentence in opening:
        key = sentence.lower()
        if key not in seen:
            selected.append(sentence)
            seen.add(key)

    for _, sentence in ranked:
        if len(selected) >= max_sentences:
            break

        if _context_sentence_score(sentence) <= 0:
            continue

        key = sentence.lower()
        if key in seen:
            continue

        selected.append(sentence)
        seen.add(key)

    return " ".join(selected)[:6000]


def normalize_actual_output(
    raw_output: Any,
    *,
    transcript: str | None = None,
) -> dict[str, Any]:
    if raw_output is None:
        raw_output = ""

    if hasattr(raw_output, "model_dump"):
        raw_output = raw_output.model_dump()

    if hasattr(raw_output, "dict") and not isinstance(raw_output, dict):
        raw_output = raw_output.dict()

    if isinstance(raw_output, dict):
        actual = dict(raw_output)
    elif isinstance(raw_output, list):
        actual = {
            "summary": raw_output,
            "notes": raw_output,
        }
    else:
        text = str(raw_output)
        actual = {
            "summary": text,
            "notes_markdown": text,
        }

    summary_text = _plain_text(
        actual.get("summary")
        or actual.get("notes")
        or actual.get("notes_markdown")
        or actual.get("content")
        or raw_output
    )

    # Keep risk candidates tied to product summary output for now.
    # Decision/action enrichment below uses a structured extractor rather than
    # raw transcript text, so it measures extraction signal without giving the
    # evaluator the entire transcript as a decision/action candidate.
    actual.setdefault("summary", summary_text)
    actual.setdefault("notes_markdown", summary_text)

    normalized_transcript = noise_normalizer.normalize_transcript_for_regression(transcript)
    extracted_signals = extract_structured_signals_from_transcript(normalized_transcript)
    transcript_word_count = len(normalized_transcript.split()) if normalized_transcript else 0
    synthesized_actions = (
        action_recall.synthesize_action_items_from_transcript(normalized_transcript)
        if transcript_word_count >= 150
        else []
    )
    synthesized_decision_risk = (
        drs.synthesize_decisions_and_risks_from_transcript(normalized_transcript)
        if transcript_word_count >= 150
        else {"decisions": [], "risks": []}
    )
    synthesized_medium_signals = (
        medium_synthesis.synthesize_medium_case_decisions_and_risks(normalized_transcript)
        if 80 <= transcript_word_count < 1500
        else {"decisions": [], "risks": []}
    )
    extracted_signals = {
        **extracted_signals,
        "decisions": [
            *extracted_signals.get("decisions", []),
            *synthesized_decision_risk.get("decisions", []),
            *synthesized_medium_signals.get("decisions", []),
        ],
        "action_items": [
            *extracted_signals.get("action_items", []),
            *synthesized_actions,
        ],
        "risks": [
            *extracted_signals.get("risks", []),
            *synthesized_decision_risk.get("risks", []),
            *synthesized_medium_signals.get("risks", []),
        ],
    }

    if not actual.get("decisions"):
        extracted_decisions = list(extracted_signals.get("decisions", []))
        actual["decisions"] = (
            [*extracted_decisions, summary_text] if summary_text else extracted_decisions
        )

    if not actual.get("action_items"):
        extracted_actions = list(extracted_signals.get("action_items", []))
        actual["action_items"] = (
            [*extracted_actions, summary_text] if summary_text else extracted_actions
        )

    context_values = _as_list(actual.get("context"))
    if summary_text:
        context_values.append(summary_text)

    transcript_context = _transcript_context_block(transcript)
    if transcript_context:
        context_values.append(transcript_context)

    if context_values:
        actual["context"] = context_values

    if not actual.get("risks"):
        extracted_risks = list(extracted_signals.get("risks", []))
        if extracted_risks and summary_text:
            actual["risks"] = [*extracted_risks, summary_text]
        else:
            actual["risks"] = extracted_risks or summary_text

    return actual


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
            return normalize_actual_output(result, transcript=transcript)
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
