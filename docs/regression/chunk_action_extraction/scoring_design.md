# Chunk Action Extraction Scoring Design

## Goal

Compare MeetIQ-generated action items against manually defined expected action ground truth.

## Inputs

- Expected actions:
  - docs/regression/chunk_action_extraction/expected/*.expected_actions.md

- Actual action output:
  - generated meeting notes
  - persisted action_item_objects
  - markdown/UI-facing action items

## Metrics

| Metric | Meaning |
|---|---|
| Must-capture recall | How many required expected actions were found |
| Owner accuracy | Whether the extracted owner matches expected owner |
| Deadline accuracy | Whether the extracted deadline/timing matches expected deadline |
| False positives | Action items generated that are not supported by the meeting |
| Duplicate rate | Repeated or over-merged actions |
| Coverage position | Whether actions from beginning, middle, and end are preserved |

## Public-launch targets

| Metric | Target |
|---|---:|
| Must-capture recall | 80–90%+ |
| Owner accuracy | 70–85%+ |
| Deadline accuracy when explicitly stated | 70%+ |
| False positives | 0–1 per meeting preferred |
| Duplicate/noisy actions | Low |

## Scoring notes

- ES2006c is currently review-needed and should not be used for final scoring until expected actions are manually verified.
- Ground truth should not be copied blindly from current model output.
- Current model output can be used as reference, but expected actions should represent what a strong system should capture.
