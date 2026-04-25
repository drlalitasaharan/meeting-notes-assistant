# Pilot RC1 live execution pack

Status: Draft
Release baseline: v0.1.0-pilot-rc1
Purpose: Prepare the first controlled pilot run with real users.

## Pilot scope

Pilot RC1 should be used with:

- Short, structured business meetings
- Clear discussion topics
- Action-oriented meetings
- Users who understand this is an early pilot

Pilot RC1 should not yet be positioned as:

- A general-purpose transcription platform
- A replacement for legal, medical, or regulated meeting records
- A solution for noisy, multi-hour, or highly unstructured recordings

## Recommended pilot size

Start with 3 to 5 pilot users.

The goal is not scale yet. The goal is to learn whether the output is useful enough for real work.

## Pilot success criteria

A pilot meeting is successful if:

- The meeting uploads successfully.
- The job completes without manual intervention.
- The markdown export is readable.
- The summary is directionally correct.
- Decisions are not misleading.
- Action items are useful enough for follow-up.
- The user would consider using the tool again.

## Before each pilot

Confirm:

- Local app or demo environment is running.
- `/healthz` is healthy.
- Demo fallback output is ready.
- The meeting file is short and structured.
- The user knows this is a controlled pilot.
- No sensitive or regulated data is used.

## During the pilot

Follow this flow:

1. Introduce the product in one sentence.
2. Explain that the goal is to convert meeting recordings into structured notes.
3. Upload the recording.
4. Wait for processing.
5. Review summary, key points, decisions, and action items.
6. Export or copy markdown.
7. Ask the user for feedback immediately.

## Feedback questions

Ask:

1. Is the summary useful?
2. Are the action items clear?
3. Are any decisions missing?
4. Is anything inaccurate or misleading?
5. Would this save you time after a real meeting?
6. What would make this good enough to use weekly?

## Pilot scoring

Use a 1 to 5 score for each area:

| Area | Score | Notes |
|---|---:|---|
| Upload flow |  |  |
| Processing reliability |  |  |
| Summary quality |  |  |
| Decision quality |  |  |
| Action item quality |  |  |
| Markdown usefulness |  |  |
| Overall usefulness |  |  |

## Issue log template

| Date | User | Meeting type | Issue | Severity | Follow-up |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

Severity levels:

- Low: polish or wording issue
- Medium: useful output but needs correction
- High: misleading, missing major decisions, or failed processing
- Blocker: cannot complete pilot flow

## Go / no-go rule after first 3 pilots

Continue pilot if:

- At least 2 of 3 users say the output would save time.
- No blocker issues occur.
- No high-severity hallucination or misleading decision issue occurs.

Pause and fix if:

- Upload or processing fails repeatedly.
- Users cannot understand the exported notes.
- Decisions or action items are consistently wrong.
- The product needs heavy manual explanation to be useful.

## Next step after this pack

Run the first real pilot session and document the result in the Pilot RC1 execution tracker.
