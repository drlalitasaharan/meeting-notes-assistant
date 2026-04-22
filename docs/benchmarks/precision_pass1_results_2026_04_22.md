# Precision pass 1 results

## Validation set
- Meeting 81 = primary precision benchmark
- Meeting 86 = safety benchmark
- 30-minute script = regression benchmark

## Result summary

### Meeting 81
- Result: FAIL
- decisions_count: 1
- action_items_count: 1
- Summary is still long and transcript-like
- Decision extraction still contains a giant transcript chunk
- Interpretation: patch did not materially improve precision extraction

### Meeting 86
- Result: PASS
- decisions_count: 0
- action_items_count: 0
- Non-meeting safety remains intact
- Interpretation: meeting-confidence guardrail still works

### 30-minute script
- Result: PARTIAL PASS
- decisions_count: 6
- action_items_count: 3
- Summary remains usable
- Interpretation: regression benchmark mostly stable, but slightly weaker on action items

## Decision
Do not promote this precision patch.

## Why
- Meeting 81 did not materially improve
- Giant transcript-style decision still survives
- 30-minute benchmark is not clearly improved
- Safety remains preserved, which is good, but this patch does not meet promotion criteria

## Best next step
Revert the experimental local_summary precision patch and trace where
decisions / action_items / summary_slots are being rewritten downstream.
