# M02 — Manually Corrected Perfect Notes

## Purpose

Review product onboarding, supported recording copy, the sample meeting option, and early-access onboarding decisions with clear owners, risks, and unresolved questions.

## Executive Summary

The team aligned on a clearer onboarding path for MeetIQ: keep the main CTA as Start Early Access, recommend MP3 and MP4 without overpromising WAV, and make longer-recording expectations honest through review-recommended language. The sample meeting option is useful but should not block real uploads. The strongest follow-ups are Aisha updating and sending onboarding copy, Marco improving the sample/upload copy, Lena reviewing supported-recording wording, and Dev checking status/warning behavior for longer recordings.

## Decisions

- Keep the main CTA as Start Early Access and link it to the strongest pricing or checkout page.
- Promote MP3 and MP4 as recommended formats.
- Do not promise WAV support until it is fully verified.
- The sample meeting option is helpful but should not block real uploads.
- Longer recordings should show review-recommended language rather than a guarantee of full detail capture.

## Action Items

- [ ] **Aisha** — Update the landing page onboarding copy, including Upload, Process, and Review steps _(deadline: Friday morning, status: open)_
- [ ] **Marco** — Add a sample recording link to the upload page _(deadline: before the next product review, status: open)_
- [ ] **Lena** — Review the supported recordings page and confirm wording about AI-generated notes _(deadline: Thursday afternoon, status: open)_
- [ ] **Dev** — Check whether the frontend displays a clear processing status for recordings above 30 minutes _(deadline: none clearly stated, status: open)_
- [ ] **Aisha** — Send the final onboarding text to Marco _(deadline: 5 PM tomorrow, status: open)_
- [ ] **Marco** — Remove vague copy saying all formats are supported and replace it with recommended formats _(deadline: none clearly stated, status: open)_
- [ ] **Dev** — Add a warning if a recording is longer than 60 minutes and confidence is low _(deadline: none clearly stated, status: open)_

## Open Questions

- Should the upload page show estimated processing time before the user starts upload?
- Should the review-recommended message appear at 60 minutes or only when quality confidence is low?
- Should the sample meeting live on Acjen AI or inside the app dashboard?
- What exact maximum file size should be shown publicly?

## Risks

- Users may upload WAV files if supported-format copy sounds too broad.
- The Vercel checkout URL may look less trustworthy than the Acjen AI domain.
- Users may misunderstand early access if the contact form and self-checkout both appear without explanation.
- Long recordings may miss details, so important action items should be reviewed before sharing externally.

## Key Points

- Aisha's onboarding-copy work and 5 PM handoff to Marco are related but distinct enough to keep as separate actions.
- Marco's sample recording link and sample meeting button mentions should be merged into one sample/upload-page action.
- "Follow up on wording" was clarified as Lena owning supported-recording/AI-generated-note wording review.
- "Check the upload page" was clarified as Dev checking processing-status display for recordings above 30 minutes.

## Evidence Notes

- Aisha stated the four confirmed decisions at the start of the meeting.
- Lines about Aisha, Marco, Lena, and Dev used explicit "will" language with concrete tasks.
- The risk section explicitly named WAV confusion, domain trust, early-access misunderstanding, and long-recording detail loss.
- Open questions were introduced as unresolved and repeated later without being answered.

## Quality Notes

What current MeetIQ output missed or got wrong:

1. Earlier output over-focused on Aisha and missed several owner-based actions from Marco, Lena, and Dev.
2. Decision extraction previously produced broken fragments instead of the four confirmed decisions.
3. Risk and open-question sections needed complete structured extraction rather than generic next steps.
