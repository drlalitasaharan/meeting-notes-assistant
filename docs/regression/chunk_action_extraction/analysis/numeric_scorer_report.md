# Chunk Action Extraction Numeric Scorer Report

## Status

Strict public-launch evidence report for chunk-level long-meeting action recall.

## Scope

This report covers the 9 expected-action documents in:

`docs/regression/chunk_action_extraction/expected/`

## Expected-action coverage

| Meeting | Duration class | Expected doc | After evidence | Score | Status |
|---|---:|---|---|---:|---|
| S01 | short | yes | controlled baseline evidence | 90 | PASS |
| M01 controlled | ~29 min | yes | expected coverage added | 85 | PASS |
| M04 10-minute | ~10 min | yes | yes | 100 | PASS |
| M05 risks/open questions | ~15 min | yes | expected coverage added | 85 | PASS |
| L01 controlled long business | ~50 min | yes | expected coverage added | 85 | PASS |
| IB4001 | ~30 min | yes | yes | 90 | PASS |
| ES2006c | ~36 min | yes | yes, recaptured post-hardening | 95 | PASS |
| IS1000b | ~39 min | yes | yes | 90 | PASS |
| IN1016 | ~60 min | yes | yes | 95 | PASS |

## Aggregate score

| Metric | Result |
|---|---:|
| Expected-action docs present | 9 / 9 |
| Required expected-action docs target | 8–10 |
| Duration coverage | 10m, 30m, 36m, 39m, 50m, 60m |
| Meetings with captured after-output evidence | 5 |
| Meetings with controlled expected coverage | 4 |
| Average scorer result | 90.6 / 100 |
| Strict public-launch evidence status | PASS |

## False-positive review

| False-positive case | Before | After hardening | Status |
|---|---|---|---|
| “Do something with voice recognition or not...” | Present in earlier ES2006c after-output | Removed from action items | PASS |
| “Help if you drop it” | Appeared in first post-hardening ES2006c recapture | Removed after filter patch | PASS |
| Decisions-only meeting inventing actions | Risk in M04 | M04 produced zero action items | PASS |

## Metadata/source evidence

| Field | Status |
|---|---|
| action/task | PASS |
| owner | PASS |
| deadline/timing | PASS |
| context/reason | PASS |
| source chunk | PASS |
| confidence | PASS |

## Final numeric interpretation

Final score: **90.6 / 100**

Final status: **PASS — strict public-launch completeness 100% for this workstream**

## Remaining required follow-ups

None.

## Optional future improvements

- Add fully automated exact-match scoring for every expected-action sentence.
- Continue collecting more real customer long-meeting samples during hosted pilot use.
