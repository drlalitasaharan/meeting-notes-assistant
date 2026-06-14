# Chunk Action Extraction Scorecard

## Status

Updated after public-launch hardening for chunk-level action extraction.

## Completed hardening

| Area | Status | Evidence |
|---|---|---|
| Chunk-level candidate extraction | PASS | Implemented before this hardening branch. |
| Long-meeting action recall | PASS | 30m, 39m, and 60m captures completed. |
| 10-minute regression coverage | PASS | M04 9.94-minute after-output capture added. |
| Expected action ground truth | PASS | Expanded from 6 to 9 expected-action docs. |
| Metadata preservation | PASS | Final action objects now preserve source, source_chunk, reason_context, and confidence where available. |
| False-positive filtering | PASS | Vague/non-committal actions such as “do something with...” are filtered. |
| Consolidation safety | PASS | Distinct owner/task/deadline combinations are protected from over-merge by the existing consolidation path and tests. |

## Completed captures

| Meeting | Duration class | Status | Result |
|---|---:|---|---|
| IB4001 | ~30 min | PASS | Captured expected Speaker C action to create files from delimited segments / prepare data for annotation merge. |
| IS1000b | ~39 min | PASS / review | Captured Speaker B entropy/vocabulary action and minutes/shared-folder action. |
| IN1016 | ~60 min | PASS | Captured both expected must-have actions: Speaker C annotation-merge data prep and Speaker B entropy/vocabulary deliverable. |
| ES2006c | ~36 min | PASS / hardened | Earlier capture included one vague voice-recognition false positive; hardening now filters vague/non-committal action phrases. |
| M04 10-minute | ~10 min | PASS | Decisions-only meeting produced zero action items, avoiding fake action invention. |

## Expected-action coverage

| Coverage item | Count |
|---|---:|
| Expected action docs before hardening | 6 |
| Expected action docs after hardening | 9 |
| Public-launch target | 8–10 |

Expected-action docs now cover:
- S01
- M01 controlled 29-minute
- M04 10-minute decisions-only
- M05 risks/open questions
- L01 controlled 50-minute long business
- IB4001
- ES2006c
- IS1000b
- IN1016

## Key findings

- Real audio uploads completed successfully for 30–60 minute meetings.
- Long-meeting action recall is materially improved.
- Expected must-have actions were captured for IB4001 and IN1016.
- IS1000b captured the important Speaker B entropy/vocabulary action.
- ES2006c completed without the earlier stuck-processing/language-detection issue.
- M04 confirmed that decisions-only meetings do not produce fake action items.
- Final action object metadata preservation has been hardened in code and tests.
- Vague/non-committal false positives have been filtered in code and tests.

## Launch interpretation

Hosted pilot readiness impact: positive.

Public-launch interpretation: substantially improved. The chunk-level action extraction system now has stronger evidence for long-meeting recall, 10-minute coverage, expected-action ground truth coverage, metadata preservation, and false-positive filtering.

This is strong enough to mark the long-meeting action-recall workstream as public-launch hardened, with one optional follow-up: recapture ES2006c after the false-positive filter to refresh the after-output evidence.

## Remaining follow-up

1. Optional: recapture ES2006c after hardening so the after-output file reflects the new false-positive filter.
2. Optional: add a numeric scorer report across all 9 expected-action docs.
3. Continue monitoring long-meeting processing time during hosted pilot use.
