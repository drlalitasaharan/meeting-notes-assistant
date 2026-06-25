# M04 — Manually Corrected Perfect Notes

## Purpose

Review early-access support operations and reliability, including support address policy, retry messaging, review guidance, delete-meeting behavior, support response targets, monitoring, and refund escalation.

## Executive Summary

The team confirmed support and reliability policies for launch: use support@acjen.ai once the alias is ready, show helpful retry messaging for failed uploads, explain that AI notes need review before important external sharing, keep delete meeting available without resetting lifetime free-trial usage, and set a one-business-day first response target. The team assigned clear work across Arun, Ben, Sofia, and Maya for support templates, Render monitoring, support page copy, issue tracking, delete-meeting verification, refund escalation, and recommended format messaging. Major risks center on usage-policy confusion, queue delays, inconsistent support replies, very long recordings, and messy manual refunds.

## Decisions

- Use support@acjen.ai as the public support address once the email alias is ready.
- Failed uploads should show a helpful retry message instead of a generic error.
- The support page should explain that AI notes must be reviewed before important external sharing.
- Delete meeting should remain available and should not reset lifetime free-trial usage.
- The first response target for early support is one business day, not instant live chat.

## Action Items

- [ ] **Arun** — Write a failed-upload support response template _(deadline: tomorrow afternoon, status: open)_
- [ ] **Ben** — Check Render worker logs and queue health every morning during the first launch week _(deadline: every morning during launch week, status: open)_
- [ ] **Sofia** — Update the support page with review-recommended language for long recordings _(deadline: before the launch post goes live, status: open)_
- [ ] **Maya** — Create a simple issue tracker for signup, checkout, upload, and notes-generation issues _(deadline: Friday, status: open)_
- [ ] **Ben** — Verify that delete meeting removes the file from storage and keeps usage history correct _(deadline: none clearly stated, status: open)_
- [ ] **Arun** — Prepare a refund escalation note for failed paid access activation _(deadline: Monday, status: open)_
- [ ] **Sofia** — Add a public note that MP3 and MP4 are recommended recording formats _(deadline: none clearly stated, status: open)_

## Open Questions

- Should the support page mention a typical processing-time range?
- Who owns refunds when PayPal and Square results differ?
- Should the admin page show queue depth or only recent failures?
- Should the review-recommended language appear on the upload page, the generated notes page, or both?
- Should there be a separate status page later?

## Risks

- Users may think delete meeting gives another free-trial upload if the usage policy is unclear.
- Worker queue delays could look like product failure if there is no processing-status message.
- Support messages may be inconsistent without a standard failed-upload response.
- Early users may upload very long recordings before long-meeting recall is fully hardened.
- Manual refund handling can become messy if payment attempt records are not easy to find.

## Key Points

- Queue-health monitoring and Render worker monitoring are the same Ben-owned launch-week action.
- Sofia's review-recommended language mentions should merge into one support-page action for long recordings.
- "Follow up on support" was clarified as Arun preparing the failed-upload response template.
- "Check the system" was clarified as Ben checking Render worker logs and queue health.
- The support page needs both review guidance and recommended-format language.

## Evidence Notes

- Maya listed the five confirmed support/reliability decisions at the beginning of the meeting.
- The transcript explicitly assigns support-template, monitoring, support-page, issue-tracker, delete-meeting, refund, and format-copy tasks.
- Risks were stated with "Risk:" labels and repeated as blocker examples later in the recording.
- The open questions were asked repeatedly and were not resolved in the transcript.

## Quality Notes

What current MeetIQ output missed or got wrong:

1. It captured Sofia's support-page action but missed most other owner-based actions.
2. It listed only one useful decision and dropped the broader support/reliability decision set.
3. It missed several explicit risks and kept generic/meta key points that should not appear as decisions or actions.
