# M01 — Manually Corrected Perfect Notes

## Purpose

Confirm what MeetIQ can launch this week, what remains out of scope, and what needs to improve for 30-60 minute meeting recall without blocking the early-access launch.

## Executive Summary

The team agreed to launch MeetIQ as controlled early access through practical launch channels while quality work continues in parallel. The launch should use Acjen.ai as the public URL, avoid overpromising long-recording quality, and keep social copy focused on value rather than plan limits. Engineering will focus the first quality branch on 30-60 minute recall, evidence metadata, action extraction, deduplication, decision precision, and unresolved open-question handling without touching checkout, payment webhooks, plan activation, or usage ledger. The team also aligned on lightweight baseline scoring, support/review language, and a single feedback tracker.

## Decisions

- Launch as controlled early access, not a broad full public SaaS launch.
- Use BetaList, Indie Hackers, selected AI directories, LinkedIn, and X as first public channels; Product Hunt can wait.
- Use Acjen.ai as the main product URL for public submissions.
- Limit the first quality branch to 30-60 minute meeting recall; 90-120 minute meetings are deferred.
- Preserve evidence metadata internally first; UI evidence display is not required for launch.
- Do not pay for every directory in the first launch week; prioritize free, credible, or low-cost options.
- Social launch copy should not lead with plan limits.
- Final notes should favor fewer, stronger action items over many vague ones.
- Risks should be practical and context-specific.
- Open questions should only include questions still unresolved at the end of the meeting.
- The quality branch must not touch checkout, plan activation, payment webhooks, or usage ledger.
- If one platform blocks submission, continue with the other launch channels.
- Maya owns final launch-post approval.
- Use GitHub issues for engineering bugs and a feedback spreadsheet for user wording, pain points, and launch-channel notes.
- Baseline evaluation should be lightweight enough to support practical improvements.

## Action Items

- [ ] **Priya** — Prepare BetaList and Indie Hackers copy and reuse the core description for directory submissions _(deadline: tomorrow noon Eastern, status: open)_
- [ ] **Priya** — Create two LinkedIn versions and one short X version with calm long-recording review language _(deadline: tomorrow noon Eastern, status: open)_
- [ ] **Priya** — Submit at least five free or low-cost directories and log paid-only directories as skipped _(deadline: end of week, status: open)_
- [ ] **Priya** — Create one feedback tracker with source, user comment, meeting length, issue type, severity, and follow-up status _(deadline: Friday afternoon, status: open)_
- [ ] **Alex** — Add a pricing-page transition note saying MeetIQ is by Acjen AI and the page is the secure app checkout page _(deadline: Friday evening if possible, status: open)_
- [ ] **Alex** — Check whether extracted actions, decisions, risks, and open questions can carry source chunk, speaker, timestamp, evidence text, and confidence _(deadline: next Monday, status: open)_
- [ ] **Alex** — Improve extraction so action items prefer owner, concrete task, due date, and context _(deadline: next Monday, status: open)_
- [ ] **Alex** — Add a dedupe test where similar pricing actions should not be merged _(deadline: next Monday, status: open)_
- [ ] **Alex** — Add a later resolution pass that removes open questions answered by later chunks _(deadline: after action recall improvement, status: open)_
- [ ] **Jordan** — Create baseline quality sheets for M01, M02, and M03 _(deadline: Thursday 5 PM Eastern, status: open)_
- [ ] **Jordan** — Mark vague items separately from missed items in the baseline _(deadline: Thursday 5 PM Eastern, status: open)_
- [ ] **Jordan** — Include decision recall and decision precision in the baseline _(deadline: Thursday 5 PM Eastern, status: open)_
- [ ] **Jordan** — Label synthetic recordings clearly as synthetic _(deadline: when the baseline pack is created, status: open)_
- [ ] **Jordan** — Prepare a support response template for early users who report poor long-meeting recall _(deadline: Friday noon Eastern, status: open)_
- [ ] **Maya** — Review support page language, make sure MP3 and MP4 are recommended, and add review-recommended language for longer recordings _(deadline: tomorrow evening, status: open)_
- [ ] **Maya and Priya** — Write calm review language using "review suggested" for normal meetings and "review recommended" for longer recordings _(deadline: tomorrow evening, status: open)_

## Open Questions

- Whether synthetic test recordings should ever be stored in the repo remains deferred; the current direction is to keep recordings outside the repo unless they are small and clearly licensed.

## Risks

- Landing page and app live on different domains, which could create a trust gap during signup or checkout.
- Exposing too much evidence detail in the UI immediately could slow launch.
- Support copy may confuse users if supported formats and review expectations are unclear.
- Aggressive deduplication could merge related but different actions.
- A perfect evaluator could delay practical quality improvements.
- Review-recommended language could sound too alarming if written too strongly.
- Feedback may be scattered across email, LinkedIn comments, and directories.
- Directory costs could become wasteful if paid submissions are used too early.

## Key Points

- The launch and quality tracks are parallel: public copy can proceed while 30-60 minute recall improves.
- The output quality target is concrete actions, confirmed decisions, practical risks, unresolved open questions, and fewer vague duplicates.
- Resolved questions, such as whether Acjen.ai or the pricing page should be the canonical submission URL, should not remain open.
- Launch copy should say MeetIQ helps founders, consultants, and small teams turn meeting recordings into structured notes without claiming perfect capture of every detail.

## Evidence Notes

- Maya explicitly confirmed controlled early access, Acjen.ai as the public URL, 30-60 minute quality scope, launch-safety constraints, and final launch-post approval.
- Priya repeated ownership for BetaList, Indie Hackers, LinkedIn, X, directory submissions, and the feedback tracker.
- Alex described the evidence metadata and extraction/deduplication work as engineering follow-up.
- Jordan described the baseline scoring method, support template need, and synthetic-labeling requirement.
- Risks were raised with practical context: trust gap, evidence UI scope, support clarity, dedupe false merges, scattered feedback, and review-language tone.

## Quality Notes

What current MeetIQ output missed or got wrong:

1. It captured only one action item and missed most owner/deadline-based actions.
2. It merged many confirmed decisions into noisy text and included instruction-like content as decision material.
3. It under-captured risks, next steps, and unresolved question handling despite the transcript stating them clearly.
