# M03 — Manually Corrected Perfect Notes

## Purpose

Review pilot implementation and billing readiness for controlled early access, including checkout scope, public URLs, support readiness, risks, and unresolved operational questions.

## Executive Summary

The team confirmed controlled early access with Starter checkout as the main public plan and Acjen AI as the public URL. Pro Pilot live payment testing is useful but not required before the first controlled launch, and single sign-on remains out of scope unless a client asks. The team assigned concrete work for smoke testing, BetaList submission, support macros, pricing-table confirmation, webhook-log verification, launch-copy cleanup, and onboarding. The main risks are paid-plan activation, Pro Pilot pricing confusion, support load from failed uploads, and overpromising two-hour meeting quality.

## Decisions

- Launch as controlled early access, not a full public enterprise launch.
- Starter checkout is the primary public plan for now.
- Pro Pilot live payment testing is useful but not required before the first controlled launch.
- Use Acjen AI as the primary public URL.
- Avoid submitting the raw Vercel URL to launch sites.
- Keep single sign-on outside the first pilot scope unless a client specifically requests it.

## Action Items

- [ ] **Sam** — Run a production smoke test for signup, checkout, upload, notes generation, download, and usage tracking _(deadline: noon tomorrow, status: open)_
- [ ] **Priya** — Prepare the BetaList submission using the Acjen AI URL _(deadline: end of week, status: open)_
- [ ] **Nora** — Draft the first support macro for failed uploads and long processing _(deadline: Wednesday, status: open)_
- [ ] **Ethan** — Confirm whether the public pricing table should show Starter at $23 and Pro Pilot at $49 _(deadline: none clearly stated, status: open)_
- [ ] **Sam** — Verify Square and PayPal webhook logs after the next test payment _(deadline: after the next test payment, status: open)_
- [ ] **Priya** — Remove language that says perfect notes for two-hour meetings from public launch copy _(deadline: none clearly stated, status: open)_
- [ ] **Nora** — Create a simple onboarding checklist for the first ten users _(deadline: before Monday morning, status: open)_

## Open Questions

- Should Business Team stay manual request only on the pricing page?
- Who will monitor the first weekend of paid signups?
- Should early access users receive a welcome email immediately after checkout?
- Should failed payment attempts be visible in the admin dashboard?

## Risks

- If webhook activation fails, paid users may not receive the correct upload limit.
- Pro Pilot pricing may confuse early users if it is shown before testing is complete.
- Support load may increase if failed uploads do not show a helpful message.
- Overpromising two-hour meeting quality could create trust problems during launch.

## Key Points

- Billing readiness is being treated as launch-critical, but Pro Pilot live payment testing is not a blocker for controlled launch.
- The public launch URL should be Acjen AI rather than the raw Vercel URL.
- Sam's checkout, upload, download, and usage-tracking checks should remain one smoke-test action.
- "Follow up on billing" was clarified as Sam verifying Square and PayPal webhook logs.
- "Check launch copy" was clarified as Priya removing perfect two-hour meeting claims.

## Evidence Notes

- Priya explicitly listed five confirmed decisions.
- Sam, Priya, Nora, Ethan, and Sam again were each assigned concrete tasks in the action section.
- Nora repeatedly restated webhook activation failure as the blocker to capture.
- Ethan repeated the open questions without later answers, so they remain unresolved.

## Quality Notes

What current MeetIQ output missed or got wrong:

1. Current action recall was strong and should be preserved.
2. The current summary was too narrow and did not fully cover billing readiness, support, launch URL, and scope decisions.
3. Decision cleanup and risk extraction needed tightening to remove fragments and include all four practical risks.
