# Meeting Regression Transcript Baseline

Date recorded: 2026-06-11

## Purpose

This report records the current transcript-based regression baseline after adding structured decision/action extraction to the baseline runner.

The goal is to measure MeetIQ note-generation quality before making the next summarization, risk extraction, or long-meeting recall improvement.

## Scope

- Transcript-based baseline only
- No fixture changes
- No evaluator changes
- No summarization-quality tuning
- No audio transcription regression yet
- Generated temporary actual-output JSON files are not committed

## Current Summary

- Mode: `transcript_baseline`
- Summarizer: `backend.app.services.summarize.summarize_text`
- Actual-output directory used temporarily: `backend/tests/tmp/meeting_regression_actual`
- Total evaluated cases: 12
- Passed cases: 1
- Failed cases: 11
- Average score: 0.2957
- Overall pass: False
- Generated cases: L01, L02, L03, L04, M01, M02, M03, M04, M05, S01, S02, S03
- Skipped cases: 1
- Generation failures: 0

## Change Since Previous Baseline

- Previous passed cases: 1
- Current passed cases: 1
- Previous failed cases: 11
- Current failed cases: 11
- Previous average score: 0.2377
- Current average score: 0.2957
- Average score delta: 0.058

## Target Improvement Snapshot

| Case | Previous Score | Current Score | Delta | Decisions | Actions |
|---|---:|---:|---:|---:|---:|
| M01 | 0.3137 | 0.5098 | 0.1961 | 2/6 (0.3333) | 5/6 (0.8333) |
| M04 | 0.25 | 0.625 | 0.375 | 5/8 (0.625) | 0/0 (1.0) |
| L01 | 0.1706 | 0.2618 | 0.0912 | 1/8 (0.125) | 4/10 (0.4) |
| M05 | 0.2706 | 0.2706 | 0.0 | 0/2 (0.0) | 1/2 (0.5) |
| S01 | 0.8824 | 0.8824 | 0.0 | 2/3 (0.6667) | 3/3 (1.0) |

## Case Results

| Case | Category | Status | Score | Decisions | Actions | Risks | Context |
|---|---:|---:|---:|---:|---:|---:|---:|
| L01 | long | FAIL | 0.2618 | 1/8 (0.125) | 4/10 (0.4) | 1/6 (0.1667) | 0/0 (1.0) |
| L02 | long | FAIL | 0.05 | 0/7 (0.0) | 0/5 (0.0) | 0/5 (0.0) | 1/3 (0.3333) |
| L03 | long | FAIL | 0.1 | 0/7 (0.0) | 0/5 (0.0) | 0/6 (0.0) | 2/3 (0.6667) |
| L04 | long | FAIL | 0.0708 | 1/9 (0.1111) | 0/5 (0.0) | 0/7 (0.0) | 1/4 (0.25) |
| M01 | medium | FAIL | 0.5098 | 2/6 (0.3333) | 5/6 (0.8333) | 0/3 (0.0) | 0/0 (1.0) |
| M02 | medium | FAIL | 0.15 | 0/2 (0.0) | 0/0 (1.0) | 0/5 (0.0) | 3/5 (0.6) |
| M03 | medium | FAIL | 0.05 | 0/6 (0.0) | 0/1 (0.0) | 0/5 (0.0) | 1/3 (0.3333) |
| M04 | medium | FAIL | 0.625 | 5/8 (0.625) | 0/0 (1.0) | 0/0 (1.0) | 0/0 (1.0) |
| M05 | medium | FAIL | 0.2706 | 0/2 (0.0) | 1/2 (0.5) | 1/5 (0.2) | 0/0 (1.0) |
| S01 | short | PASS | 0.8824 | 2/3 (0.6667) | 3/3 (1.0) | 1/1 (1.0) | 0/0 (1.0) |
| S02 | short | FAIL | 0.5 | 0/0 (1.0) | 0/0 (1.0) | 0/0 (1.0) | 3/6 (0.5) |
| S03 | short | FAIL | 0.0779 | 0/0 (1.0) | 0/1 (0.0) | 0/0 (1.0) | 2/7 (0.2857) |

## Decision/Action Recall Snapshot

| Case | Category | Decisions | Actions |
|---|---:|---:|---:|
| L01 | long | 1/8 (0.125) | 4/10 (0.4) |
| L02 | long | 0/7 (0.0) | 0/5 (0.0) |
| L03 | long | 0/7 (0.0) | 0/5 (0.0) |
| L04 | long | 1/9 (0.1111) | 0/5 (0.0) |
| M01 | medium | 2/6 (0.3333) | 5/6 (0.8333) |
| M02 | medium | 0/2 (0.0) | 0/0 (1.0) |
| M03 | medium | 0/6 (0.0) | 0/1 (0.0) |
| M04 | medium | 5/8 (0.625) | 0/0 (1.0) |
| M05 | medium | 0/2 (0.0) | 1/2 (0.5) |
| S01 | short | 2/3 (0.6667) | 3/3 (1.0) |
| S03 | short | 0/0 (1.0) | 0/1 (0.0) |

## Context Recall Snapshot

- L02 [long]: context 1/3 (0.3333)
- L03 [long]: context 2/3 (0.6667)
- L04 [long]: context 1/4 (0.25)
- M02 [medium]: context 3/5 (0.6)
- M03 [medium]: context 1/3 (0.3333)
- S02 [short]: context 3/6 (0.5)
- S03 [short]: context 2/7 (0.2857)

## Lowest-Scoring Cases

- M03 [medium]: score=0.05 status=FAIL
- L02 [long]: score=0.05 status=FAIL
- L04 [long]: score=0.0708 status=FAIL
- S03 [short]: score=0.0779 status=FAIL
- L03 [long]: score=0.1 status=FAIL

## Skipped Cases

- N01: missing transcript fixture

## Generation Failures

- None

## Validation Commands

```bash
python -m pytest backend/tests/test_transcript_signal_extractor.py backend/tests/test_meeting_regression_baseline_runner.py backend/tests/test_meeting_regression_evaluator.py -q
python backend/scripts/run_meeting_regression_baseline.py --allow-fail --output backend/tests/tmp/meeting_regression_post_decision_action_report.json
```

## Notes

This baseline is intentionally measurement-only. Future PRs should use this report to decide which summarization, risk extraction, long-meeting recall, or guardrail improvements to make next.
