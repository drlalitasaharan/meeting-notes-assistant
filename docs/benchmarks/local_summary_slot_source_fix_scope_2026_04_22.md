# Local summary slot source fix scope — 2026-04-22

## Goal
Stop transcript-sized content from entering summary_slots in Meeting 81.

## In scope
Inside local_summary.py only:
- tighten slot candidate filtering
- reject speaker-style narration
- reject oversized candidates before merge
- enforce hard output caps before summary slot assembly

## Hard constraints
- purpose must be short and structured
- outcome must not exceed compact business-summary length
- each risk must be compact
- each next_step must be compact and action-oriented

## Out of scope
- do not change meeting-confidence guardrail
- do not change non-meeting safety behavior
- do not retune 30-minute quality pass
- do not retune action-item cleanup in this pass

## Validation set
- Meeting 81 = primary
- Meeting 86 = safety
- 30-minute script = regression

## Promotion rule
Promote only if:
- Meeting 81 summary becomes materially shorter
- outcome no longer contains transcript-scale text
- risks and next_steps are compact and structured
- Meeting 86 remains safely downgraded
- 30-minute benchmark remains stable
