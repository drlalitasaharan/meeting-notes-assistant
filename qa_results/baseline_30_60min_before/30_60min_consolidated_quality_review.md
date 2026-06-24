# 30–60 Minute Meeting Baseline Consolidated Quality Review

## Technical conclusion

M01, M02, M03, and M04 all uploaded and processed successfully.

This confirms that the plan-aware recording-duration fix works locally for paid/pilot users.

## Evidence pack

- M01: 37.9 minutes, processed successfully
- M02: 35.38 minutes, processed successfully
- M03: 44.06 minutes, processed successfully
- M04: 53.54 minutes, processed successfully

## Quality conclusion

30–60 minute processing works technically, but generated note quality still needs hardening before confidently marketing strong 30–60 minute meeting support.

## Repeated failure modes

1. Important owner-based actions are sometimes missed.
2. Repeated actions are not always merged into the strongest owner/task/deadline version.
3. Decision extraction includes broken fragments.
4. Risk extraction misses reliability, dependency, delay, and long-recording caution content.
5. Next steps can be too generic.
6. Summary can be too narrow.
7. Markdown/ASR cleanup issues remain.

## Positive signal

M03 showed much stronger action recall, proving that long-meeting action recovery can work. The hardening task should preserve the improved M03 behavior while fixing M01, M02, and M04 failure modes.

## Recommended next task

Run a focused 30–60 minute meeting quality hardening task using M01, M02, M03, and M04 as the evidence pack.

Scope:
- Improve action recall.
- Promote owner-based speaker instructions into action items.
- Merge repeated actions into stronger final actions.
- Remove broken decision fragments.
- Improve risk extraction.
- Improve concrete next-step generation.
- Improve safe Markdown/readability cleanup.

Do not touch:
- Billing checkout
- Payment provider logic
- Webhooks
- Auth
- Frontend UI
- Deployment settings
- Production environment configuration
- Current plan-duration limits
