# Local summary slot source fix exact-anchor results — 2026-04-22

## Decision
Do not promote this exact-anchor local_summary slot-source fix.

## Why
- Meeting 81 improved partially, but summary is still oversized
- purpose / outcome / risks were over-pruned to empty
- next_steps still contain transcript-like speaker narration
- Meeting 86 safety remained good
- 30-minute benchmark regressed because outcome disappeared and summary became too thin

## Key evidence

### Meeting 81
- summary_len: 5798
- purpose_len: 0
- outcome_len: 0
- risks_count: 0
- next_steps_count: 4
- max_next_step_len: 113

Interpretation:
- oversized content was reduced, but the structured slots were over-pruned
- next_steps are still not clean enough

### Meeting 86
- summary_len: 123
- decisions_count: 0
- action_items_count: 0
- next_steps_count: 0

Interpretation:
- safety behavior remained good

### 30-minute benchmark
- summary_len: 191
- purpose_len: 191
- outcome_len: 0
- risks_count: 3
- next_steps_count: 4

Interpretation:
- regression introduced
- summary became too thin
- outcome was incorrectly removed

## Conclusion
This patch is too aggressive and should not be promoted.

## Next engineering step
Revert this patch.

Then make a narrower pass focused first on:
- next_steps transcript rejection
- speaker-prefix rejection
- conversational sentence rejection
- compact action-oriented next-step shaping

Do not change yet:
- meeting-confidence guardrail
- non-meeting safety behavior
- 30-minute quality pass
