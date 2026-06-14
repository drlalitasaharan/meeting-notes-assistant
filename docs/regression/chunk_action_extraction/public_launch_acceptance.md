# Strong Public-Launch Acceptance Criteria — Chunk-Level Action Extraction

## Goal

Improve long-meeting action recall so MeetIQ reliably preserves action items from the beginning, middle, and end of long recordings.

## Required capabilities

- Extract candidate actions from transcript chunks.
- Preserve source chunk evidence.
- Capture owner when stated or strongly implied.
- Capture deadline/timing when mentioned.
- Use "Unassigned" when owner is unclear.
- Use "No deadline stated" when timing is unclear.
- Add confidence for each candidate action.
- Consolidate duplicates without over-merging distinct owner/deliverable/deadline combinations.
- Preserve specific actions over vague actions.
- Score output against expected action ground truth.

## Regression target set

| Meeting | Duration | Type | Required |
|---|---:|---|---|
| S01 | short | controlled | yes |
| IB4001 | 29m | medium/long | yes |
| ES2006c | 36m | long | yes |
| IS1000b | 39m | long | yes |
| IN1016 | 60m | very long | yes |

## Public-launch quality targets

| Metric | Target |
|---|---:|
| Must-capture action recall | 80–90%+ |
| Owner accuracy | 70–85%+ |
| Deadline accuracy when explicitly stated | 70%+ |
| False positives | 0–1 per meeting preferred |
| Duplicate/noisy actions | Low |
| Long meeting processing completion | 100% for regression set |

## Definition of done

- Ground truth files are filled for the target set.
- Automated scorer compares expected vs actual actions.
- Chunk-level extractor is implemented and tested.
- Consolidation pass is implemented and tested.
- Existing action pipeline preserves recovered actions in UI/API/Markdown.
- Before/after scorecard shows measurable improvement.
- 30–60 minute recordings complete successfully.
- Remaining limitations are documented.
