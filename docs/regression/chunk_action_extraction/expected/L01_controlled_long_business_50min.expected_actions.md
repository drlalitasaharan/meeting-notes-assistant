# L01 controlled long business 50-minute expected action evidence

## File

`demo_media/regression/pack/L01_controlled_long_business_50min.m4a`

## Duration

Approximately 50 minutes.

## Regression purpose

This controlled long business meeting validates long-meeting action recall across early, middle, and late sections.

The expected behavior is that MeetIQ should preserve important assigned work across the whole meeting, not only the final recap.

## Expected action behavior

Expected action item count: 4–8

Expected action qualities:
- Actions from early, middle, and late sections should be preserved.
- Owners should be preserved when stated.
- Deadlines/timing should be preserved when explicitly stated.
- Similar repeated actions should be deduplicated.
- Distinct owners, deadlines, or deliverables should not be over-merged.
- Vague or conversational statements should not become action items.

## Must-capture categories

MeetIQ should capture actions related to:
- Pilot/demo readiness work.
- Upload or structured-notes workflow validation.
- Client-facing messaging or onboarding preparation.
- Quality checks for summary, decisions, risks, action items, and markdown/export behavior.
- Any explicitly assigned owner-specific follow-up.

## Unacceptable output

- Capturing only late-meeting recap actions while missing earlier assigned work.
- Over-merging actions with different owners or deliverables.
- Promoting vague discussion into action items.
- Generic workflow actions such as “review summary” or “copy/export.”

## Pass condition

PASS if MeetIQ captures multiple concrete actions across the long meeting and keeps duplicates/noise low.

FAIL if early/middle actions are lost, owner-specific actions are merged incorrectly, or vague discussion is promoted.
