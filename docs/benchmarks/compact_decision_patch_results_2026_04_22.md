# Compact decision patch results — 2026-04-22

## Summary
This patch improved decision compactness, but it does not meet promotion criteria.

## Meeting 81
- Result: FAIL
- summary_len: 668
- decisions_count: 0
- action_items_count: 1
- Interpretation:
  - giant transcript-style decisions were removed
  - but the summary is still too long
  - summary_slots are still polluted with transcript-like content
  - action-item recall did not materially improve

## Meeting 86
- Result: PASS
- decisions_count: 0
- action_items_count: 0
- Interpretation:
  - non-meeting safety remains intact

## 30-minute script
- Result: PASS
- summary_len: 439
- decisions_count: 6
- action_items_count: 4
- Interpretation:
  - regression benchmark remains strong
  - compact decision filtering did not damage the strongest current benchmark

## Decision
Do not promote this compact decision patch.

## Why
- Meeting 81 still fails the promotion rule
- decision compactness improved, but summary precision did not improve enough
- main remaining issue is slot extraction precision, especially:
  - purpose
  - risks
  - next_steps

## Next step
Revert this experimental local_summary patch.

Then build a slot-precision pass focused on:
- purpose
- risks
- next_steps

Do not change:
- meeting-confidence guardrail
- non-meeting safety behavior
