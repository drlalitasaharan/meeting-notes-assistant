# L01 controlled long business expected action evidence

## File

`demo_media/regression/pack/L01_controlled_long_business_50min.m4a`

## Duration

Approximately 50 minutes.

## Regression purpose

This controlled long business meeting validates action recall across a long commercial pilot readiness discussion with many decisions, risks, open questions, rejected proposals, and recap items.

The expected behavior is that MeetIQ should preserve explicit assigned actions from the final recap and avoid converting recommendations, risks, rejected proposals, open questions, or discussion framing into action items.

## Expected action items

- Circulate the approved pilot pricing table by 2026-06-18 17:00
- Upload the final demonstration recording by 2026-06-19 15:00
- Complete the storage and access-control security review by 2026-06-22 12:00
- Prepare the pilot support-response templates by 2026-06-23 17:00
- Confirm the first pilot customer participant list by 2026-06-24 12:00
- Run the twelve-recording regression suite and document failures by 2026-06-25 17:00
- Verify recording deletion from storage after the retention test
- Create the customer onboarding checklist
- Confirm whether regional data storage is required
- Review whether contractor accounts may join the pilot

## Must-capture actions

| must_capture | owner | action | deadline | source/evidence | notes |
|---|---|---|---|---|---|
| yes | Priya | Circulate the approved pilot pricing table | 2026-06-18 17:00 | Recap action | Explicit recap action |
| yes | Jordan | Upload the final demonstration recording | 2026-06-19 15:00 | Recap action | Explicit recap action |
| yes | Alex | Complete the storage and access-control security review | 2026-06-22 12:00 | Recap action | Explicit recap action |
| yes | Morgan | Prepare the pilot support-response templates | 2026-06-23 17:00 | Recap action | Explicit recap action |
| yes | Priya | Confirm the first pilot customer participant list | 2026-06-24 12:00 | Recap action | Explicit recap action |
| yes | Jordan | Run the twelve-recording regression suite and document failures | 2026-06-25 17:00 | Recap action | Explicit recap action |
| yes | Alex | Verify recording deletion from storage after the retention test | No deadline stated | Recap action | Explicit recap action |
| yes | Morgan | Create the customer onboarding checklist | No deadline stated | Recap action | Explicit recap action |
| yes | Unassigned | Confirm whether regional data storage is required | No deadline stated | Recap action | Explicit unassigned action |
| yes | Unassigned | Review whether contractor accounts may join the pilot | No deadline stated | Recap action | Explicit unassigned action |

## Should-not-capture / false-positive risks

| action/topic | reason |
|---|---|
| Test that recommendation against the pilot objective and current evidence | Recommendation-framing language; not a final assigned action. |
| Use explicit confirmation language when the group reaches agreement and explicit rejection language when an option is not selected | Meeting-process guidance; not a final assigned action. |
| Proposed or rejected options | Transcript says rejected proposals must not appear as decisions, commitments, next steps, or promised capabilities. |
| Risks without explicit owners | Risks should remain risks unless explicitly assigned. |
| Open questions without explicit action language | Open questions should remain open questions unless explicitly assigned or intentionally unassigned. |

## Pass condition

PASS if MeetIQ captures the explicit recap actions, preserves owners/deadlines when stated, keeps unassigned actions unassigned, and avoids converting recommendation/framing language into action items.

FAIL if expected recap actions are missing or discussion/recommendation text is promoted into unsupported action items.
