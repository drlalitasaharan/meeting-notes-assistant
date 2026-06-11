# Meeting Regression Transcript Baseline

Date recorded: 2026-06-11

## Purpose

This report records the current transcript-based regression baseline after adding structured risk extraction to the baseline runner.

The goal is to measure MeetIQ note-generation quality before making the next long-meeting recall, summarization, or guardrail improvement.

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
- Average score: 0.3197
- Overall pass: False
- Generated cases: L01, L02, L03, L04, M01, M02, M03, M04, M05, S01, S02, S03
- Skipped cases: 1
- Generation failures: 0

## Change Since Previous Baseline

- Previous passed cases: 1
- Current passed cases: 1
- Previous failed cases: 11
- Current failed cases: 11
- Previous average score: 0.2957
- Current average score: 0.3197
- Average score delta: 0.024

## Target Risk Improvement Snapshot

| Case | Previous Score | Current Score | Delta | Risks | Decisions | Actions |
|---|---:|---:|---:|---:|---:|---:|
| M01 | 0.5098 | 0.5686 | 0.0588 | 1/3 (0.3333) | 2/6 (0.3333) | 5/6 (0.8333) |
| M05 | 0.2706 | 0.4118 | 0.1412 | 5/5 (1.0) | 0/2 (0.0) | 1/2 (0.5) |
| L01 | 0.2618 | 0.35 | 0.0882 | 4/6 (0.6667) | 1/8 (0.125) | 4/10 (0.4) |
| S01 | 0.8824 | 0.8824 | 0.0 | 1/1 (1.0) | 2/3 (0.6667) | 3/3 (1.0) |
| M04 | 0.625 | 0.625 | 0.0 | 0/0 (1.0) | 5/8 (0.625) | 0/0 (1.0) |

## Case Results

| Case | Category | Status | Score | Decisions | Actions | Risks | Context |
|---|---:|---:|---:|---:|---:|---:|---:|
| L01 | long | FAIL | 0.35 | 1/8 (0.125) | 4/10 (0.4) | 4/6 (0.6667) | 0/0 (1.0) |
| L02 | long | FAIL | 0.05 | 0/7 (0.0) | 0/5 (0.0) | 0/5 (0.0) | 1/3 (0.3333) |
| L03 | long | FAIL | 0.1 | 0/7 (0.0) | 0/5 (0.0) | 0/6 (0.0) | 2/3 (0.6667) |
| L04 | long | FAIL | 0.0708 | 1/9 (0.1111) | 0/5 (0.0) | 0/7 (0.0) | 1/4 (0.25) |
| M01 | medium | FAIL | 0.5686 | 2/6 (0.3333) | 5/6 (0.8333) | 1/3 (0.3333) | 0/0 (1.0) |
| M02 | medium | FAIL | 0.15 | 0/2 (0.0) | 0/0 (1.0) | 0/5 (0.0) | 3/5 (0.6) |
| M03 | medium | FAIL | 0.05 | 0/6 (0.0) | 0/1 (0.0) | 0/5 (0.0) | 1/3 (0.3333) |
| M04 | medium | FAIL | 0.625 | 5/8 (0.625) | 0/0 (1.0) | 0/0 (1.0) | 0/0 (1.0) |
| M05 | medium | FAIL | 0.4118 | 0/2 (0.0) | 1/2 (0.5) | 5/5 (1.0) | 0/0 (1.0) |
| S01 | short | PASS | 0.8824 | 2/3 (0.6667) | 3/3 (1.0) | 1/1 (1.0) | 0/0 (1.0) |
| S02 | short | FAIL | 0.5 | 0/0 (1.0) | 0/0 (1.0) | 0/0 (1.0) | 3/6 (0.5) |
| S03 | short | FAIL | 0.0779 | 0/0 (1.0) | 0/1 (0.0) | 0/0 (1.0) | 2/7 (0.2857) |

## Risk Recall Snapshot

| Case | Category | Risks |
|---|---:|---:|
| L01 | long | 4/6 (0.6667) |
| L02 | long | 0/5 (0.0) |
| L03 | long | 0/6 (0.0) |
| L04 | long | 0/7 (0.0) |
| M01 | medium | 1/3 (0.3333) |
| M02 | medium | 0/5 (0.0) |
| M03 | medium | 0/5 (0.0) |
| M05 | medium | 5/5 (1.0) |
| S01 | short | 1/1 (1.0) |

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
python backend/scripts/run_meeting_regression_baseline.py --allow-fail --output backend/tests/tmp/meeting_regression_post_risk_report.json
```

## Notes

This baseline is intentionally measurement-only. Future PRs should use this report to decide which long-meeting recall, summarization, guardrail, or evaluator improvements to make next.
