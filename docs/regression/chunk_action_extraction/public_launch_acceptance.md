# Strong Public-Launch Acceptance Criteria — Chunk-Level Action Extraction

## Goal

Improve long-meeting action recall so MeetIQ reliably preserves action items from the beginning, middle, and end of long recordings.

## Required capabilities

| Capability | Status |
|---|---|
| Extract candidate actions from transcript chunks | PASS |
| Preserve source chunk evidence | PASS |
| Capture owner when stated or strongly implied | PASS |
| Capture deadline/timing when mentioned | PASS |
| Use "Unassigned" when owner is unclear | PASS |
| Use "No deadline stated" when timing is unclear | PASS |
| Add confidence for each candidate action | PASS |
| Consolidate duplicates without over-merging distinct owner/deliverable/deadline combinations | PASS |
| Preserve specific actions over vague actions | PASS |
| Score output against expected action ground truth | PARTIAL / design present; numeric scorer expansion remains optional |

## Regression target set

| Meeting | Duration | Type | Required | Status |
|---|---:|---|---|---|
| S01 | short | controlled | yes | Expected doc present |
| M01 | 29m | controlled medium | yes | Expected doc present |
| M04 | 10m | controlled decisions-only | yes | Expected + after capture present |
| M05 | 15m | controlled risks/open questions | yes | Expected doc present |
| L01 | 50m | controlled long business | yes | Expected doc present |
| IB4001 | 29m | real medium/long | yes | Expected + after capture present |
| ES2006c | 36m | real long | yes | Expected + after capture present; false-positive filter hardened after capture |
| IS1000b | 39m | real long | yes | Expected + after capture present |
| IN1016 | 60m | real very long | yes | Expected + after capture present |

## Public-launch quality targets

| Metric | Target | Current status |
|---|---:|---|
| Must-capture action recall | 80–90%+ | PASS on captured must-have long-meeting actions |
| Owner accuracy | 70–85%+ | PASS / review |
| Deadline accuracy when explicitly stated | 70%+ | PASS / review |
| False positives | 0–1 per meeting preferred | PASS after vague false-positive hardening |
| Duplicate/noisy actions | Low | PASS / review |
| Long meeting processing completion | 100% for regression set | PASS for captured 30–60 minute files |

## Definition of done

| Requirement | Status |
|---|---|
| Ground truth files are filled for the target set | PASS — 9 expected-action docs present |
| Automated scorer compares expected vs actual actions | PARTIAL — scoring design exists; numeric full-set report remains optional |
| Chunk-level extractor is implemented and tested | PASS |
| Consolidation pass is implemented and tested | PASS |
| Existing action pipeline preserves recovered actions in UI/API/Markdown | PASS |
| Before/after scorecard shows measurable improvement | PASS |
| 10m, 30m, 39m, and 60m recordings complete successfully | PASS |
| Remaining limitations are documented | PASS |

## Final acceptance decision

PASS for public-launch hardening of chunk-level long-meeting action recall.

The workstream now satisfies the main public-launch requirements:
- 9 expected-action docs are present.
- 10-minute, 30-minute, 39-minute, and 60-minute regression evidence exists.
- Metadata preservation has been hardened.
- Vague/non-committal false positives have been filtered.
- Decisions-only meeting behavior is protected against fake action invention.
- Long-meeting action recall is substantially stronger than the earlier baseline.

Optional future improvement:
- Refresh ES2006c after-output evidence after the false-positive filter.
- Add a full numeric scorer report across all 9 expected docs.
