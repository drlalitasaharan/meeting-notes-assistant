# S01_client_weekly_sync — Manually Corrected Perfect Notes

## Purpose

Review meeting notes assistant demo progress, confirm the pilot outreach plan, discuss open operational issues, and align on concrete next steps for the week.

## Executive Summary

The team confirmed that the core upload and processing flow is stable enough to prepare a controlled pilot demo, while keeping claims conservative. The first pilot audience will be consultants, agencies, founders, and small teams. The live demo should use a short clean file, while capability testing should use a separate 10-minute audio sample. A processed backup meeting should be ready before any live demo. This week's focus is to validate the 10-minute audio flow, prepare the demo and outreach assets, keep a command runbook, and review output before pilot outreach begins.

## Decisions

- The first pilot audience will be consultants, agencies, founders, and small teams.
- The live demo will use a short clean file.
- Capability testing will use a separate 10-minute audio sample.
- Keep one backup meeting already processed before any live demo.
- This week's priority is to validate the 10-minute audio flow and prepare basic pilot outreach assets.

## Action Items

- [ ] **Lalita** — Create the clean 10-minute audio test and run it through the product _(deadline: today, status: open)_
- [ ] **Lalita** — Prepare the short live demo file and keep one backup processed meeting ready _(deadline: before live demo, status: open)_
- [ ] **Unassigned** — Update the demo command runbook after the successful test, including health check, meeting creation, upload, worker logs, and notes-fetch commands _(deadline: after successful test, status: open)_
- [ ] **Unassigned** — Review and finalize the landing page and outreach message _(deadline: Friday, status: open)_
- [ ] **Unassigned** — Create the script file directly in the project folder, generate the audio locally, verify duration, create a fresh meeting, upload the audio, monitor worker logs, review notes, and preserve the processed meeting if output is good _(deadline: today and tomorrow, status: open)_

## Open Questions

- None clearly stated.

## Risks

- Live demo processing could be slow because of queue, transcription, or network conditions.
- Processing an older failed meeting can fail or confuse the demo if the meeting has no raw media path.
- Overpromising full-length one-hour meeting support before it is tested and hardened could weaken trust.
- Vague or overly conversational sample content could make the generated demo notes look weaker.

## Key Points

- The product's strongest current demo path is create meeting, upload file, process it, and show generated notes in JSON and Markdown.
- Backend, Redis, storage, and the worker were described as healthy.
- Pilot messaging should focus on short meeting recordings, structured summaries, decisions, and action items.
- Outreach should be practical and concise: a short demo video, a simple landing page, and a short message to early prospects.
- Success this week means one clean 10-minute test, one short live demo file, and a basic pilot outreach package.

## Evidence Notes

- The transcript states that the upload/processing workflow is stable and that the application can accept media files and start background jobs.
- The audience decision is grounded in the discussion of consultants, agencies, founders, and small teams.
- The demo-track decision separates a short live sample from the 10-minute capability test.
- The backup meeting is recommended to protect the live demo from queue, transcription, or network delays.
- Lalita is explicitly assigned the 10-minute test and demo-file/backup work; other follow-up tasks are described without a clear owner.

## Quality Notes

What current MeetIQ output missed or got wrong:

1. It captured the purpose and broad key point but missed all decisions and action items.
2. It missed the practical demo risks around raw media path timing, backup meeting need, and overpromising long recordings.
3. It compressed the meeting into one noisy key point instead of separating decisions, actions, risks, and evidence.
