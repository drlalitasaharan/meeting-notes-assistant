# Meeting 81 next steps quality-threshold pass

## Goal
Improve next_steps so they are more action-oriented and less conversational.

## Scope
Limited to next_steps shaping only.

## Validation set
- Meeting 81 = primary benchmark
- Meeting 86 = safety benchmark
- 30-minute script = regression benchmark

## Result

### Meeting 81
- next_steps quality: Pass
- malformed speaker-style items: None remaining in summary_slots.next_steps
- notes: next_steps are now clean and action-oriented. The benchmark output keeps the desired business follow-up action without conversational transcript fragments.

### Meeting 86
- safety behavior: Pass
- notes: non-meeting audio remains safely downgraded. No fabricated decisions or action items were produced, and summary_slots.next_steps stayed empty.

### 30-minute script
- regression status: Pass
- notes: no material regression observed from this scoped next_steps change. Summary, risks, decisions, and action items remained stable, and next_steps stayed structured and action-oriented enough for the regression benchmark.

## Promotion decision
- Promote

## Notes
- The final fix had two parts:
  - restore summary_slots.next_steps from structured action fields during normalization
  - filter vague next-step phrasing such as "Concrete owners for the follow-up actions"
- This pass intentionally did not retune broader action-item extraction, meeting-confidence guardrails, or the 30-minute quality pass.
