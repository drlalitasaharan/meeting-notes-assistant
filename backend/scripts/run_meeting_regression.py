from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.meeting_regression_evaluator import (  # noqa: E402
    RegressionEvalConfig,
    evaluate_manifest,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run MeetIQ meeting regression evaluation against expected fixture JSON."
    )
    parser.add_argument(
        "--fixture-dir",
        default="backend/tests/fixtures/meeting_regression",
        help="Directory containing manifest.json and *.expected.json files.",
    )
    parser.add_argument(
        "--actual-dir",
        default=None,
        help="Directory containing generated actual JSON outputs to evaluate.",
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="Compare expected fixtures against themselves. Useful to validate evaluator wiring.",
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
        help="Token-recall threshold for decisions, risks, and context matches.",
    )
    parser.add_argument(
        "--action-threshold",
        type=float,
        default=0.55,
        help="Combined action/owner/deadline threshold for action matches.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to write full JSON report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    fixture_dir = Path(args.fixture_dir)
    actual_dir = Path(args.actual_dir) if args.actual_dir else None

    if not fixture_dir.exists():
        print(f"ERROR: fixture directory not found: {fixture_dir}", file=sys.stderr)
        return 2

    if not args.self_check and actual_dir is None:
        print("ERROR: pass --actual-dir or use --self-check", file=sys.stderr)
        return 2

    if actual_dir is not None and not actual_dir.exists():
        print(f"ERROR: actual directory not found: {actual_dir}", file=sys.stderr)
        return 2

    config = RegressionEvalConfig(
        min_case_score=args.min_score,
        text_match_threshold=args.text_threshold,
        action_match_threshold=args.action_threshold,
    )

    report = evaluate_manifest(
        fixture_dir,
        actual_dir,
        self_check=args.self_check,
        case_ids=set(args.case) if args.case else None,
        config=config,
    )

    print(
        "Meeting regression:"
        f" {report['passed_cases']}/{report['total_cases']} passed,"
        f" average_score={report['average_score']}"
    )

    for result in report["results"]:
        status = "PASS" if result.get("passed") else "FAIL"
        score = result.get("score", 0.0)
        case_id = result.get("id")
        category = result.get("category")
        print(f"{status} {case_id} [{category}] score={score}")

        if not result.get("passed"):
            error = result.get("error")
            if error:
                print(f"  error: {error}")
            for metric_name, metric in result.get("metrics", {}).items():
                print(
                    f"  {metric_name}:"
                    f" {metric.get('matched', 0)}/{metric.get('total', 0)}"
                    f" recall={metric.get('recall', 0.0)}"
                )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Wrote report: {output_path}")

    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
