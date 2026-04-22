# Slot precision pass scope — 2026-04-22

## Goal
Improve Meeting 81 precision by tightening structured slot extraction for:
- purpose
- risks
- next_steps

## Why this pass exists
Previous experiments showed:
- non-meeting safety is now protected by the meeting-confidence guardrail
- 30-minute benchmark remains stable
- Meeting 81 still fails because summary_slots contain long transcript-like content

## In scope
- add stricter candidate filtering for summary slot builders
- prefer short, business-style, structured statements
- reject transcript-like speaker narration and oversized sentences

## Out of scope
- do not change meeting-confidence guardrail
- do not broaden generic transcript boosting
- do not retune action-item cleanup in this pass
- do not change 30-minute quality pass behavior unless needed for safety

## Validation set
- Meeting 81 = primary precision benchmark
- Meeting 86 = safety benchmark
- 30-minute script = regression benchmark

## Promotion rule
Promote only if:
- Meeting 81 summary becomes materially shorter and cleaner
- Meeting 81 risks / next_steps become more structured
- Meeting 86 remains safely downgraded
- 30-minute benchmark remains stable
