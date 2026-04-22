# Next steps precision pass scope — 2026-04-22

## Goal
Improve Meeting 81 precision by tightening next_steps extraction only.

## In scope
Inside local_summary.py only:
- tighten next_steps generation
- reject speaker-prefixed next-step text
- reject transcript-style conversational narration
- prefer compact action-oriented next-step statements
- enforce max length on each next_step

## Out of scope
- do not change purpose generation
- do not change outcome generation
- do not change risk extraction
- do not change meeting-confidence guardrail
- do not change non-meeting safety behavior
- do not change 30-minute quality pass

## Validation set
- Meeting 81 = primary precision benchmark
- Meeting 86 = safety benchmark
- 30-minute script = regression benchmark

## Promotion rule
Promote only if:
- Meeting 81 next_steps become shorter and more action-oriented
- Meeting 81 next_steps no longer contain speaker narration
- Meeting 86 remains safely downgraded
- 30-minute benchmark remains stable
