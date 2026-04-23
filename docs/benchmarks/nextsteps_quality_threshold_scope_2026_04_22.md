# Next steps quality-threshold pass scope — 2026-04-22

## Goal
Improve Meeting 81 next_steps quality without changing summary, outcome, risks, safety guardrails, or 30-minute quality behavior.

## Why this pass exists
The earlier narrow next_steps pass was safer than the aggressive slot-source patch, but it was still not promotable.
Meeting 81 still showed malformed or conversational next_steps, even when next_steps became shorter.

## In scope
Inside local_summary.py only:
- tighten next_steps acceptance rules
- reject speaker-prefixed text
- reject conversational openers
- reject malformed or cut-off sentences
- prefer compact, action-oriented next steps
- require a minimum quality threshold before accepting a next_step

## Acceptance intent
A valid next_step should look like a business follow-up action, for example:
- Prepare the short-lived demo file.
- Finalize the landing page and outreach message.
- Keep one backup processed meeting ready.

A next_step should not look like:
- Speaker Two, I agree with that...
- I think that backup is essential...
- If the live run feels slow, we should also...
- cut-off or transcript-fragment sentences

## Out of scope
- do not change meeting-confidence guardrail
- do not change non-meeting safety behavior
- do not change 30-minute quality pass
- do not retune purpose / outcome / risks in this pass
- do not retune action-item extraction beyond next_steps shaping

## Validation set
- Meeting 81 = primary benchmark
- Meeting 86 = safety benchmark
- 30-minute script = regression benchmark

## Promotion rule
Promote only if:
- Meeting 81 next_steps become clearly more action-oriented and less conversational
- no malformed speaker-style next_steps remain
- Meeting 86 remains safely downgraded
- 30-minute benchmark remains stable
