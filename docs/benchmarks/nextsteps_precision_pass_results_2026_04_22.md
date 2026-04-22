# Next steps precision pass results — 2026-04-22

## Meeting 81
- summary_len: 10376
- decisions_count: 2
- action_items_count: 1
- purpose_len: 296
- outcome_len: 10092
- risks_count: 3
- max_risk_len: 5031
- next_steps_count: 2
- max_next_step_len: 85

Interpretation:
- the narrow next_steps pass did not solve the main Meeting 81 problem
- oversized transcript-like content is still entering summary, outcome, and risks
- next_steps became shorter, but quality is still not clean enough
- one next_step is still conversational / malformed
- this means next_steps filtering improved only partially, not enough for promotion

## Meeting 86
- summary_len: 321
- decisions_count: 0
- action_items_count: 0
- next_steps_count: 0

Interpretation:
- safety behavior remained stable
- non-meeting downgrade still looks good

## 30-minute benchmark
- summary_len: 439
- decisions_count: 6
- action_items_count: 4
- purpose_len: 191
- outcome_len: 246
- risks_count: 3
- next_steps_count: 4
- max_next_step_len: 99

Interpretation:
- no meaningful regression introduced in the 30-minute benchmark
- outcome stayed intact
- next_steps stayed present and compact enough
- this is a good sign for scope control of the narrow pass

## Conclusion
This pass is directionally safer than the earlier aggressive slot-source patch, but it is still not promotable.

### Why
- Meeting 81 still fails on the primary issue
- summary / outcome / risks remain oversized
- next_steps precision improved only partially
- safety and 30-minute regression behavior remained stable

## Best next engineering step
Keep this as a learning pass, but do not promote yet.

Focus next on next_steps only, with a tighter filter for:
- speaker-prefix rejection
- conversational opener rejection
- malformed sentence rejection
- action-oriented verb shaping
- minimum quality threshold before accepting a next_step

## Do not change yet
- meeting-confidence guardrail
- non-meeting safety behavior
- 30-minute quality pass
