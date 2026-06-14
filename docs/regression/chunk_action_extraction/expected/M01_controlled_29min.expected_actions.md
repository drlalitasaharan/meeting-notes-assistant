# M01 controlled 29-minute expected action evidence

## File

`demo_media/regression/pack/M01_controlled_29min.m4a`

## Duration

Approximately 29.07 minutes.

## Regression purpose

This controlled medium-length business meeting is used to validate action recall across a realistic 20–30 minute meeting.

The expected behavior is that MeetIQ should preserve concrete follow-up work while avoiding vague discussion fragments.

## Expected action behavior

Expected action item count: 2–5

Expected action qualities:
- Each action should include a concrete task.
- Owners should be preserved when stated.
- Deadlines or timing should be preserved when explicitly stated.
- Similar repeated actions should be deduplicated.
- Discussion-only statements should not become action items.

## Must-capture categories

MeetIQ should capture actions related to:
- Client follow-up or pilot/demo preparation.
- Pricing, proposal, or scope confirmation when stated as assigned work.
- Upload, processing, structured notes, markdown export, or quality-check follow-up when stated as assigned work.
- Onboarding or client-facing guidance when assigned to a person/team.

## Unacceptable output

- Generic workflow instructions such as “review summary” or “copy/export.”
- Conditional statements beginning with “if.”
- Vague actions without an owner or deliverable.
- Duplicate versions of the same action.

## Pass condition

PASS if MeetIQ captures the main concrete follow-up tasks with low duplication and no unsupported action invention.

FAIL if important assigned work is missing or discussion fragments are promoted into action items.
