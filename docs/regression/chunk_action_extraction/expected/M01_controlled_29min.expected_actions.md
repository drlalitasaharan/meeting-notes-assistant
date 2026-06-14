# M01 controlled 29-minute expected action evidence

## File

`demo_media/regression/pack/M01_controlled_29min.m4a`

## Duration

Approximately 29.07 minutes.

## Regression purpose

This controlled medium-length business meeting is used to validate action recall across a realistic 20–30 minute meeting.

The expected behavior is that MeetIQ should preserve concrete follow-up work while avoiding vague discussion fragments.

## Expected action items

- Keep one backup meeting processed and ready before any live demo
- Create the clean ten-minute audio test and run it through the product
- Prepare the short live-demo recording
- Review and finalize the landing page and outreach message
- Add stage timing logs to the worker output
- Package the final demo commands into one short runbook

## Must-capture actions

| must_capture | owner | action | deadline | source/evidence | notes |
|---|---|---|---|---|---|
| yes | Team | Keep one backup meeting processed and ready before any live demo | No deadline stated | Fixture expected action + final action recap | Concrete demo-readiness action |
| yes | Lalita | Create the clean ten-minute audio test and run it through the product | today | Fixture expected action + final action recap | Concrete test/run action |
| yes | Lalita | Prepare the short live-demo recording | No deadline stated | Fixture expected action + final action recap | Concrete demo-preparation action |
| yes | Team | Review and finalize the landing page and outreach message | Friday | Fixture expected action + transcript line: “Team will review and finalize the landing page and outreach message by Friday.” | Captured by current output |
| yes | Team | Add stage timing logs to the worker output | No deadline stated | Fixture expected action + final action recap | Concrete engineering follow-up |
| yes | Lalita | Package the final demo commands into one short runbook | No deadline stated | Fixture expected action + final action recap | Concrete runbook follow-up |

## Acceptable additional actions

| owner | action | reason |
|---|---|---|
| Lalita | Save the strongest current output as the primary demo artifact and retain the older example only for internal comparison | Listed as acceptable additional action in fixture |
| Team | Keep a short command checklist for meeting creation, upload, logs, JSON notes, and Markdown notes | Listed as acceptable additional action in fixture |
| Lalita | Keep the current action-item cleanup and defer deeper summarization tuning until after the pilot | Listed as acceptable additional action in fixture |

## Should-not-capture / false-positive risks

| action/topic | reason |
|---|---|
| Generic workflow instructions such as review summary or copy/export | Workflow description only, not a concrete assigned follow-up |
| Conditional statements beginning with “if” | Conditional discussion, not a committed task |
| Action ownership assigned to John or Kevin | Fixture explicitly says expected owners are Team and Lalita |
| The thirty-minute recording as the default live demonstration | Fixture says this should not be invented |
| Immediate public launch | Fixture says this should not be invented |

## Pass condition

PASS if MeetIQ captures the main concrete follow-up tasks with low duplication and no unsupported action invention.

FAIL if important assigned work is missing or discussion fragments are promoted into action items.
