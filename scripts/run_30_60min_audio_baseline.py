#!/usr/bin/env python3
"""Run selected 30-60 minute MeetIQ audio baseline recordings through local API.

This is a local QA helper only. It does not change backend behavior, billing,
auth, prompts, processing, or generated notes.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "qa_results" / "baseline_30_60min_before"
DEFAULT_MANIFEST = DEFAULT_OUTPUT_DIR / "manifest.csv"
DEFAULT_EMAIL = "meetiq-qa-baseline@example.com"
DEFAULT_PASSWORD = "QaBaselinePassword123!"
TERMINAL_SUCCESS_STATUSES = {"done", "finished", "succeeded", "success", "completed"}
TERMINAL_FAILURE_STATUSES = {"failed", "error", "cancelled", "canceled", "stopped"}


@dataclass(frozen=True)
class BaselineCase:
    meeting_id: str
    recording_path: Path
    expected_duration_min: str
    notes_file: Path


class ApiError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one selected 30-60 minute MP3 baseline recording through a local "
            "MeetIQ API and save generated notes outputs."
        ),
        epilog=(
            "Example M01 only:\n"
            "  python scripts/run_30_60min_audio_baseline.py --case M01\n\n"
            "Required local services:\n"
            "  backend API at BASE_URL, Redis/RQ worker, DB, storage, ffmpeg/ffprobe, "
            "and transcription/model configuration used by your local MeetIQ stack.\n\n"
            "Because these files are longer than the free-trial limit, use a local "
            "pilot/paid QA account or set the running API env accordingly, for example:\n"
            "  MEETIQ_PILOT_OVERRIDE_EMAILS=meetiq-qa-baseline@example.com"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST),
        help="CSV manifest to read. Defaults to qa_results/baseline_30_60min_before/manifest.csv.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where generated JSON/Markdown outputs are saved.",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("BASE_URL") or os.getenv("MNA_API") or DEFAULT_BASE_URL,
        help="MeetIQ API base URL. Can also use BASE_URL or MNA_API env.",
    )
    parser.add_argument(
        "--email",
        default=os.getenv("MEETIQ_QA_EMAIL", DEFAULT_EMAIL),
        help="QA user email. Can also use MEETIQ_QA_EMAIL env.",
    )
    parser.add_argument(
        "--password",
        default=os.getenv("MEETIQ_QA_PASSWORD", DEFAULT_PASSWORD),
        help="QA user password. Can also use MEETIQ_QA_PASSWORD env.",
    )
    parser.add_argument(
        "--case",
        action="append",
        default=[],
        help="Case id to run, e.g. --case M01. Can be repeated.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run every manifest row. This is intentionally explicit for long files.",
    )
    parser.add_argument(
        "--list-cases",
        action="store_true",
        help="List available manifest cases and exit.",
    )
    parser.add_argument(
        "--max-poll-attempts",
        type=int,
        default=int(os.getenv("MAX_POLL_ATTEMPTS", "240")),
        help="Maximum job poll attempts. Can also use MAX_POLL_ATTEMPTS env.",
    )
    parser.add_argument(
        "--poll-sleep-seconds",
        type=float,
        default=float(os.getenv("POLL_SLEEP_SECONDS", "5")),
        help="Seconds between job polls. Can also use POLL_SLEEP_SECONDS env.",
    )
    return parser.parse_args()


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def load_manifest(path: Path) -> dict[str, BaselineCase]:
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")

    cases: dict[str, BaselineCase] = {}
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            case_id = (row.get("meeting_id") or "").strip()
            recording_path = (row.get("recording_path") or "").strip()
            notes_file = (row.get("notes_file") or "").strip()
            if not case_id or not recording_path:
                continue

            cases[case_id] = BaselineCase(
                meeting_id=case_id,
                recording_path=resolve_repo_path(recording_path),
                expected_duration_min=(row.get("expected_duration_min") or "").strip(),
                notes_file=resolve_repo_path(notes_file)
                if notes_file
                else DEFAULT_OUTPUT_DIR / f"{case_id}_generated_notes.md",
            )

    return cases


def request_json(
    session: requests.Session,
    method: str,
    url: str,
    **kwargs: Any,
) -> dict[str, Any]:
    response = session.request(method, url, timeout=60, **kwargs)
    if not response.ok:
        detail = response.text
        try:
            parsed = response.json()
            detail = json.dumps(parsed, indent=2)
        except ValueError:
            pass
        raise ApiError(f"{method} {url} failed with HTTP {response.status_code}:\n{detail}")

    try:
        return response.json()
    except ValueError as exc:
        raise ApiError(f"{method} {url} did not return JSON") from exc


def authenticate(session: requests.Session, base_url: str, email: str, password: str) -> str:
    signup_payload = {
        "email": email,
        "password": password,
        "first_name": "MeetIQ",
        "last_name": "QA",
        "organization_name": "Local baseline QA",
    }
    signup_response = session.post(
        f"{base_url}/v1/auth/signup",
        json=signup_payload,
        timeout=60,
    )

    if signup_response.ok:
        return str(signup_response.json()["access_token"])

    login_payload = {"email": email, "password": password}
    login_response = session.post(f"{base_url}/v1/auth/login", json=login_payload, timeout=60)
    if not login_response.ok:
        raise ApiError(
            "Could not sign up or log in QA user.\n"
            f"Signup HTTP {signup_response.status_code}: {signup_response.text}\n"
            f"Login HTTP {login_response.status_code}: {login_response.text}"
        )

    return str(login_response.json()["access_token"])


def normalize_status(value: Any) -> str:
    return str(value or "").strip().lower()


def poll_job(
    session: requests.Session,
    base_url: str,
    job_id: str,
    output_dir: Path,
    case_id: str,
    max_attempts: int,
    sleep_seconds: float,
) -> dict[str, Any]:
    latest: dict[str, Any] = {}
    for attempt in range(1, max_attempts + 1):
        latest = request_json(session, "GET", f"{base_url}/v1/jobs/{job_id}")
        (output_dir / f"{case_id}_job_latest.json").write_text(
            json.dumps(latest, indent=2),
            encoding="utf-8",
        )

        status = normalize_status(latest.get("status"))
        print(f"{case_id}: poll {attempt}/{max_attempts}: {status or 'unknown'}")
        if status in TERMINAL_SUCCESS_STATUSES:
            return latest
        if status in TERMINAL_FAILURE_STATUSES:
            raise ApiError(f"{case_id}: job {job_id} failed with status {status}")

        time.sleep(sleep_seconds)

    raise ApiError(f"{case_id}: job {job_id} did not finish after {max_attempts} polls")


def run_case(
    case: BaselineCase,
    *,
    session: requests.Session,
    base_url: str,
    output_dir: Path,
    max_poll_attempts: int,
    poll_sleep_seconds: float,
) -> dict[str, Any]:
    if not case.recording_path.exists():
        raise FileNotFoundError(f"{case.meeting_id}: recording not found: {case.recording_path}")

    print("=" * 72)
    print(f"Running {case.meeting_id}: {case.recording_path}")
    print(f"Expected duration: {case.expected_duration_min or 'unknown'} minutes")

    create_response = request_json(
        session,
        "POST",
        f"{base_url}/v1/meetings",
        json={"title": f"30-60 minute baseline {case.meeting_id}"},
    )
    (output_dir / f"{case.meeting_id}_create_meeting.json").write_text(
        json.dumps(create_response, indent=2),
        encoding="utf-8",
    )

    meeting_pk = create_response.get("id") or create_response.get("meeting_id")
    if not meeting_pk:
        raise ApiError(f"{case.meeting_id}: could not read meeting id: {create_response}")

    with case.recording_path.open("rb") as audio_file:
        upload_response = request_json(
            session,
            "POST",
            f"{base_url}/v1/meetings/{meeting_pk}/upload",
            files={"file": (case.recording_path.name, audio_file, "audio/mpeg")},
        )

    (output_dir / f"{case.meeting_id}_upload.json").write_text(
        json.dumps(upload_response, indent=2),
        encoding="utf-8",
    )

    job_id = (
        upload_response.get("job_id") or upload_response.get("jobId") or upload_response.get("id")
    )
    if not job_id:
        raise ApiError(f"{case.meeting_id}: could not read job id: {upload_response}")

    job_response = poll_job(
        session,
        base_url,
        str(job_id),
        output_dir,
        case.meeting_id,
        max_poll_attempts,
        poll_sleep_seconds,
    )

    notes_json = request_json(session, "GET", f"{base_url}/v1/meetings/{meeting_pk}/notes/ai")
    notes_json_path = output_dir / f"{case.meeting_id}_generated_notes.json"
    notes_json_path.write_text(json.dumps(notes_json, indent=2), encoding="utf-8")

    markdown_response = session.get(
        f"{base_url}/v1/meetings/{meeting_pk}/notes.md",
        timeout=60,
    )
    if not markdown_response.ok:
        raise ApiError(
            f"GET notes.md failed with HTTP {markdown_response.status_code}: "
            f"{markdown_response.text}"
        )

    markdown_path = output_dir / f"{case.meeting_id}_generated_notes.md"
    markdown_path.write_text(markdown_response.text, encoding="utf-8")

    print(f"{case.meeting_id}: wrote {markdown_path}")
    print(f"{case.meeting_id}: wrote {notes_json_path}")

    return {
        "case": case.meeting_id,
        "status": "completed",
        "meeting_id": meeting_pk,
        "job_id": job_id,
        "job_status": job_response.get("status"),
        "notes_json": str(notes_json_path.relative_to(REPO_ROOT)),
        "notes_markdown": str(markdown_path.relative_to(REPO_ROOT)),
    }


def write_run_summary(output_dir: Path, rows: list[dict[str, Any]]) -> None:
    summary_path = output_dir / "run_summary.csv"
    fieldnames = [
        "case",
        "status",
        "meeting_id",
        "job_id",
        "job_status",
        "notes_json",
        "notes_markdown",
        "error",
    ]
    with summary_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})
    print(f"Wrote run summary: {summary_path.relative_to(REPO_ROOT)}")


def main() -> int:
    args = parse_args()
    manifest_path = resolve_repo_path(args.manifest)
    output_dir = resolve_repo_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    base_url = str(args.base_url).rstrip("/")

    cases = load_manifest(manifest_path)
    if args.list_cases:
        for case in cases.values():
            print(
                f"{case.meeting_id}: {case.recording_path.relative_to(REPO_ROOT)} "
                f"({case.expected_duration_min or '?'} min)"
            )
        return 0

    if args.all:
        selected_ids = list(cases.keys())
    elif args.case:
        selected_ids = [case_id.upper() for case_id in args.case]
    else:
        print("No cases selected. Use --case M01 for one recording or --all explicitly.")
        print()
        print("M01 command:")
        print("  python scripts/run_30_60min_audio_baseline.py --case M01")
        print()
        print("List cases:")
        print("  python scripts/run_30_60min_audio_baseline.py --list-cases")
        return 2

    missing = [case_id for case_id in selected_ids if case_id not in cases]
    if missing:
        print(f"Unknown case id(s): {', '.join(missing)}", file=sys.stderr)
        return 2

    print("MeetIQ 30-60 minute audio baseline QA")
    print(f"Base URL: {base_url}")
    print(f"Manifest: {manifest_path.relative_to(REPO_ROOT)}")
    print(f"Output dir: {output_dir.relative_to(REPO_ROOT)}")
    print(f"QA email: {args.email}")
    print("Reminder: these files require a local pilot/paid QA account or raised local limits.")
    print()

    session = requests.Session()
    try:
        health = request_json(session, "GET", f"{base_url}/healthz")
        (output_dir / "healthz.json").write_text(json.dumps(health, indent=2), encoding="utf-8")

        token = authenticate(session, base_url, args.email, args.password)
        session.headers.update({"Authorization": f"Bearer {token}"})

        rows: list[dict[str, Any]] = []
        had_error = False
        for case_id in selected_ids:
            try:
                rows.append(
                    run_case(
                        cases[case_id],
                        session=session,
                        base_url=base_url,
                        output_dir=output_dir,
                        max_poll_attempts=args.max_poll_attempts,
                        poll_sleep_seconds=args.poll_sleep_seconds,
                    )
                )
            except Exception as exc:
                had_error = True
                print(f"{case_id}: ERROR: {exc}", file=sys.stderr)
                rows.append({"case": case_id, "status": "failed", "error": str(exc)})

        write_run_summary(output_dir, rows)
        return 1 if had_error else 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
