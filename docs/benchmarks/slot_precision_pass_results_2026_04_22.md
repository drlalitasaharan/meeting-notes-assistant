# Slot precision pass results — 2026-04-22

## Branch
feat/slot-precision-pass-purpose-risks-nextsteps

## Goal
Improve Meeting 81 precision by tightening structured slot extraction for:
- purpose
- risks
- next_steps

## Validation results

### Meeting 81
- Result: FAIL
- summary_len: 10376
- decisions_count: 2
- action_items_count: 1
- purpose_len: 296
- risks_count: 3
- max_risk_len: 5031
- next_steps_count: 4
- Interpretation:
  - Meeting 81 is still not promotable
  - slot precision remains poor
  - risks still contain giant transcript-like content
  - summary is still far too long
  - this pass did not solve the core precision issue

### Meeting 86
- Result: PASS
- summary_len: 321
- decisions_count: 0
- action_items_count: 0
- purpose_len: 0
- risks_count: 0
- next_steps_count: 0
- Interpretation:
  - non-meeting safety remains intact

### 30-minute script
- Result: PASS
- summary_len: 439
- decisions_count: 6
- action_items_count: 4
- purpose_len: 191
- risks_count: 3
- next_steps_count: 4
- Interpretation:
  - regression benchmark remains stable
  - no meaningful degradation versus baseline restore check

## Decision
Do not promote this slot precision pass.

## Why
- Meeting 81 still fails the promotion rule
- summary remains transcript-like and oversized
- risks extraction is still not precise enough
- next_steps are acceptable, but not enough to justify promotion
- safety and regression benchmarks stayed stable, which is good

## Best next step
Revert this experimental slot-precision patch.

Then trace exactly where Meeting 81 oversized content enters:
- purpose
- outcome
- risks

Focus next on:
- sentence candidate selection
- transcript-like sentence rejection
- maximum-length enforcement before slot assembly

Do not change:
- meeting-confidence guardrail
- non-meeting safety behavior
- 30-minute quality pass
