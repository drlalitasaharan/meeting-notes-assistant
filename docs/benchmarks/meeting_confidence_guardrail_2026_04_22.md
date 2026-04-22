# Meeting confidence guardrail validation — 2026-04-22

## Scope
Validated the new meeting-confidence guardrail against:
- Meeting 86 non-meeting safety case
- Meeting 81 extraction precision case
- 30-minute script regression benchmark

## Results

### Meeting 86
- Result: PASS
- Summary now clearly downgrades the audio as non-meeting
- decisions_count: 0
- action_items_count: 0
- Interpretation: safety behavior improved as intended

### Meeting 81
- Result: NO QUALITY IMPROVEMENT
- decisions_count: 2
- action_items_count: 1
- Summary still long, duplicated, and transcript-like
- Interpretation: core precision / extraction issue remains

### 30-minute script
- Result: PASS
- decisions_count: 6
- action_items_count: 4
- Summary remains clean and product-usable
- Interpretation: guardrail did not damage strongest current benchmark

## Decision
Keep and commit the meeting-confidence guardrail.

## Why
- It solves the safety failure mode
- It preserves the 30-minute benchmark
- It does not claim to solve Meeting 81 precision, which should be handled separately

## Next step
Build a separate precision-only extraction pass for:
- decisions
- action items
- summary compression / dedupe on structured business meetings
