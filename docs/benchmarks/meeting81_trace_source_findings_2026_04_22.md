# Meeting 81 trace source findings — 2026-04-22

## Decision
Do not patch downstream post-processing for this issue.

## Why
Trace confirms the oversized content already exists in raw_strategy output.

## Evidence
For Meeting 81:
- raw_strategy already produced:
  - summary_len around 10k
  - purpose_len around 296
  - outcome_len around 10k
  - max_risk_len around 5k
  - max_next_step_len around 321
  - max_decision_len around 5k

Those values remained materially unchanged through:
- after_normalize
- after_30min_pass
- after_guardrail

## Interpretation
The oversized transcript-like content is entering inside:
- backend/app/services/note_strategies/local_summary.py

It is not primarily introduced by:
- normalize_canonical_notes
- apply_focused_30min_quality_pass
- apply_meeting_confidence_guardrail

## Separate note
Action items changed across stages, but that is a separate issue from the slot/source bloat problem.

## Next engineering step
Patch local_summary slot construction only:
- tighten sentence candidate selection
- reject speaker-prefixed or transcript-like sentences
- enforce max words and max chars before slot assembly
- enforce final hard cap for:
  - purpose
  - outcome
  - each risk
  - each next_step

## Do not change
- meeting-confidence guardrail
- non-meeting safety behavior
- 30-minute quality pass
