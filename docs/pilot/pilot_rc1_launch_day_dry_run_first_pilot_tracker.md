# Pilot RC1 Launch-Day Dry Run and First-Pilot Execution Tracker

## Purpose

This document defines the launch-day dry-run process and first-pilot execution tracker for Pilot RC1 of the Meeting Notes Assistant.

The goal is to move from launch documentation into controlled execution readiness for the May 15 public-demo and first-user pilot target.

## Current locked baseline

Latest main baseline:

d1dc95d2 Add Pilot RC1 demo artifact and first-user pack (#82)

Pilot RC1 status:

- Launch-readiness lock: complete
- Public-demo execution package: complete
- Demo artifact and first-user pack: complete
- Quality gate: 100/100 PASS
- Controlled public-demo status: GREEN
- Launch-safe claim: Best for short, structured business meetings.

## Launch-day dry-run objective

The dry run should confirm that the complete demo flow works from a clean main branch before any external user or public-demo session.

The dry run should verify:

- Repository starts clean from latest main
- Docker services start correctly
- Backend health endpoint is available
- Worker is running and consuming queued jobs
- Redis, database, and storage are available
- End-to-end demo flow succeeds
- Markdown output is readable
- JSON output is clean
- Backup artifacts are available
- First-pilot tracker is ready

## Pre-flight checklist

- Confirm latest main is pulled
- Confirm working tree is clean
- Confirm Docker Desktop is running
- Confirm backend, worker, Redis, database, and MinIO containers are running
- Confirm backend health endpoint returns ok
- Confirm validated demo audio exists
- Confirm backup notes.md and notes_ai.json are available or can be regenerated
- Confirm public-demo script is available
- Confirm first-user intake questions are available
- Confirm known limitations wording is ready

## Dry-run command checklist

Recommended dry-run sequence:

1. Pull latest main.
2. Start or rebuild local services if needed.
3. Check backend health.
4. Confirm worker is running.
5. Run the Pilot RC1 quality gate.
6. Review notes.md.
7. Review notes_ai.json.
8. Archive dry-run evidence outside the repository.
9. Restore generated test outputs before commit.
10. Record dry-run result in this tracker.

## Go/no-go checklist

| Check | Required result | Status | Notes |
| --- | --- | --- | --- |
| Latest main pulled | Up to date | Pending | |
| Working tree | Clean before dry run | Pending | |
| Backend health | ok | Pending | |
| Worker status | Running and consuming jobs | Pending | |
| Redis | Healthy | Pending | |
| Database | Healthy | Pending | |
| Storage | Healthy | Pending | |
| Quality gate | PASS, score >= 85 | Pending | |
| Markdown output | Readable and client-safe | Pending | |
| JSON output | Clean and boundary-safe | Pending | |
| Backup artifacts | Available | Pending | |
| Known limitations | Ready to communicate | Pending | |

Go decision rule:

- GO only if all required runtime and output checks pass.
- NO-GO if worker is not consuming jobs, quality gate fails, output is not client-safe, or backup artifacts are missing.
- CONDITIONAL GO only if the live flow has a known non-product runtime issue and backup artifacts are ready.

## First-pilot execution tracker

| Pilot user | Segment | Meeting type | Date | Status | Outcome | Next step |
| --- | --- | --- | --- | --- | --- | --- |
| Pilot 1 | Founder or consultant | Short structured business meeting | TBD | Not started | Pending | Identify first user |
| Pilot 2 | Agency or small team | Short structured business meeting | TBD | Not started | Pending | Identify second user |
| Pilot 3 | Startup operator | Short structured business meeting | TBD | Not started | Pending | Identify third user |

## Outreach tracker

| Contact | Segment | Outreach date | Response | Demo scheduled | Notes |
| --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | Pending | No | Add first outreach target |

## Feedback tracker

| Pilot user | Summary useful | Decisions useful | Actions useful | Missed items | Noise/issues | Would try again |
| --- | --- | --- | --- | --- | --- | --- |
| TBD | Pending | Pending | Pending | Pending | Pending | Pending |

## Issue tracker

| Date | Issue | Type | Severity | Resolution | Follow-up branch needed |
| --- | --- | --- | --- | --- | --- |
| TBD | No issue recorded yet | TBD | TBD | TBD | TBD |

Issue types:

- Runtime or local environment
- Transcription quality
- Summary quality
- Decision extraction
- Action item extraction
- Markdown formatting
- JSON formatting
- User onboarding or messaging

## Launch-safe operating rules

- Use the conservative claim: Best for short, structured business meetings.
- Recommend human review before external sharing.
- Do not claim universal meeting accuracy.
- Do not claim enterprise readiness without additional security and compliance review.
- Do not make live product-code changes during a demo.
- Capture issues as feedback and triage them after the session.

## Dry-run result

Status: Pending

The final dry-run result should be recorded after the launch-day dry run completes.

Required evidence:

- Health check output
- Docker service status
- Worker log snippet
- Quality gate report
- Generated notes.md
- Generated notes_ai.json
- Evidence archive path

## Final recommendation

Proceed to first-user pilots only after one clean launch-day dry run passes and the go/no-go checklist is marked GO.
