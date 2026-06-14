# M05 risks and open questions expected action evidence

## File

`demo_media/regression/pack/M05_risks_open_questions_medium.m4a`

## Duration

Approximately 15.28 minutes.

## Regression purpose

This controlled medium meeting focuses on risks, open questions, and unresolved items.

The expected behavior is that MeetIQ should distinguish risks/open questions from true action items.

## Expected action behavior

Expected action item count: 1–4

Expected action qualities:
- Only explicit follow-up work should become action items.
- Risks should remain risks unless someone is clearly assigned to resolve them.
- Open questions should not become action items unless paired with an owner and task.
- Owners should be preserved when stated.
- Deadlines should be preserved only when explicitly stated.

## Must-capture categories

MeetIQ should capture actions related to:
- Resolving or following up on clearly assigned open questions.
- Confirming risk mitigation steps when assigned.
- Preparing or sharing specific follow-up material when stated as work.
- Checking unclear assumptions only when assigned to a person/team.

## Unacceptable output

- Converting every risk into an action item.
- Converting every open question into an action item.
- Vague “follow up on risks” items without owner or concrete task.
- Generic summary/review/copy/export actions.

## Pass condition

PASS if MeetIQ keeps risks/open questions separate and captures only clearly assigned follow-up work.

FAIL if the output creates many unsupported action items from risk discussion.
