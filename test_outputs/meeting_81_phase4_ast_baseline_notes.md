# real test after phase 4 AST rewrite

## Purpose
The main purpose of today's meeting is to review where we are with the Meeting Notes Assistant demo, confirm the pilot outreach plan, discuss a few open issues, and align on next steps for this week

## Outcome
Key outcomes: the first pilot audience will be consultants, agencies, founders, and small teams; the live demo will use a short and clean file, while capability testing will use a separate 10 minute audio sample

## Risks
- We already saw that if a meeting gets processed before a raw media path is attached, the worker throws an error saying the meeting has no raw media path, that means our clean test process should always be, first make sure the audio file exists, then create a fresh meeting then upload the file, and only then let the worker process that new meeting, reusing older failed meetings is likely to cause confusion.

## Next Steps
- Create the clean 10 minute audio test and run it through the product.
- Prepare the short live demo file.
- Keep one backup processed meeting ready.

## Key Points
- Lalita will create the clean 10 minute audio test and run it through the product.
- Lalita will prepare the short live demo file.
- Lalita will keep one backup processed meeting ready.
- We already saw that if a meeting gets processed before a raw media path is attached, the worker throws an error saying the meeting has no raw media path, that means our clean test process should always be, first make sure the audio file exists, then create a fresh meeting then upload the file, and only then let the worker process that new meeting, reusing older failed meetings is likely to cause confusion.

## Decisions
- The first pilot audience will be consultants, agencies, founders, and small teams.
- The live demo will use a short and clean file, while capability testing will use a separate 10 minute audio sample.

## Action Items
- [ ] **Lalita** — create the clean 10 minute audio test and run it through the product _(due: today, status: open, priority: medium)_
- [ ] **Lalita** — prepare the short live demo file _(status: open, priority: medium)_
- [ ] **Lalita** — keep one backup processed meeting ready _(status: open, priority: medium)_
