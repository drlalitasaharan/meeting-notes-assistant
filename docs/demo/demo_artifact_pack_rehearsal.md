# Demo Artifact Pack and Pilot Rehearsal

This document defines the reusable demo artifact pack and rehearsal checklist for Meeting Notes Assistant.

## Goal

Create one polished, repeatable demo package that can be shown to pilot users without live debugging.

This workstream comes after:

- Automated quality and safety regression gates
- Demo readiness documentation
- Pilot outreach asset templates

## Current readiness status

Current foundation:

- Quality gates are in place for Meeting 81 and Meeting 86.
- Demo runbook exists under docs/demo/runbook.md.
- Pilot outreach assets exist under docs/pilot/outreach_assets.md.

Current next step:

Prepare one polished demo artifact pack and rehearse the flow end to end.

## Selected demo input

Recommended first demo input:

client_weekly_sync_10min.m4a

Reason:

- Short enough for a live or near-live demo
- Structured enough to show useful meeting notes
- Better suited for pilot demos than long narrative audio
- Appropriate for validating summary, outcome, decisions, and action items

Avoid using these as first-impression demo inputs:

- 60-minute narrative audio
- Public-domain audiobook content
- Very noisy recordings
- Unstructured casual conversation
- Audio with no business-meeting intent

## Demo artifact pack

For each polished demo, prepare the following files:

1. Demo input file reference
2. AI JSON output
3. Markdown export
4. Human review note
5. Rehearsal checklist
6. Ready / not-ready decision record

Recommended folder for local outputs:

test_outputs/demo/

Recommended output filenames:

- latest_demo_notes_ai.json
- latest_demo_notes.md
- latest_demo_review.md
- latest_demo_decision.md

## How to generate demo artifacts

Follow the local demo runbook:

docs/demo/runbook.md

Minimum expected flow:

1. Start services.
2. Confirm backend health.
3. Create a demo meeting.
4. Upload the selected short demo audio.
5. Wait for worker processing to complete.
6. Review AI JSON.
7. Review markdown export.
8. Save outputs under test_outputs/demo/.
9. Complete human review.
10. Mark demo ready or not ready.

## Human review template

Use this template in:

test_outputs/demo/latest_demo_review.md

# Demo Output Review

## Demo file

## Meeting length

## Date generated

## Summary quality

Rating: 1 to 5

Notes:

## Purpose / outcome quality

Rating: 1 to 5

Notes:

## Decisions quality

Rating: 1 to 5

Notes:

## Action items quality

Rating: 1 to 5

Notes:

## Safety check

Confirm:

- No fake decisions
- No fake action items
- No greeting noise promoted as key content
- No malformed transcript fragments shown as actions
- Owner and due date fields are not invented when absent

## Overall readiness

Ready to show externally?

Yes / No

## Reviewer notes

## Rehearsal checklist

Use this checklist before any pilot call.

### Environment

- main branch is up to date
- working tree is clean
- Docker services are running
- backend health check passes
- worker is running
- storage is healthy

### Demo input

- selected short business-meeting input is available
- input file is not narrative audio
- input file is clear enough for transcription
- input has real meeting intent

### Output

- AI JSON output generated
- markdown export generated
- summary is clear
- outcome is meaningful
- decisions are real
- action items are useful
- no obvious hallucinated tasks
- markdown is clean enough to share

### Backup plan

Prepare backup artifacts before live demos:

- saved AI JSON output
- saved markdown export
- screenshot of result page
- short explanation of output sections

Do not depend only on live processing during early pilot calls.

## Ready / not-ready decision record

Use this template in:

test_outputs/demo/latest_demo_decision.md

# Demo Readiness Decision

## Demo date

## Input file

## Output files reviewed

- AI JSON:
- Markdown:
- Review note:

## Decision

Ready / Not ready

## Reason

## Known limitations to disclose

## Follow-up fixes needed

## Final demo rule

Only show externally if:

- The output passed human review.
- The markdown export is clean.
- The demo can be explained in under two minutes.
- There is a backup output available.
- The product claim stays launch-safe.

Current launch-safe claim:

Best for short, structured business meetings.
