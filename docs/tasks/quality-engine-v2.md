# Quality Engine v2

## Goal

Improve MeetIQ notes quality for 30–60 minute uploaded recordings while keeping the current working product stable.

## Baseline

Use the merged five-recording baseline:

- qa_results/quality_engine_v2_baseline/M01_current_notes.json
- qa_results/quality_engine_v2_baseline/M02_current_notes.json
- qa_results/quality_engine_v2_baseline/M03_current_notes.json
- qa_results/quality_engine_v2_baseline/M04_current_notes.json
- qa_results/quality_engine_v2_baseline/S01_client_weekly_sync_current_notes.json

Current automated baseline scores:

- M01: 35
- M02: 35
- M03: 70
- M04: 35
- S01_client_weekly_sync: 35

## Scope

Implement a production-safe notes quality improvement layer focused on:

1. Purpose inference fallback
2. Stronger action recall
3. Stronger decision extraction
4. Open-question separation
5. Owner/deadline normalization
6. Known entity/domain guardrails
7. Cleanup of transcript-like phrasing
8. Quality-check/critic pass
9. Regression score gate

## Safety rules

Do not change:

- billing
- checkout
- webhooks
- auth
- upload limits
- plan limits
- deployment settings
- production environment configuration

Keep the current notes pipeline stable.

Prefer additive changes behind safe functions, tests, or feature flags.

## Acceptance criteria

- Purpose should not be missing when meeting topic is clear.
- Action item recall should improve for M01, M02, M04, and S01.
- M03 should not regress.
- Decisions should be separated from general discussion.
- Open questions should be separated from key points.
- Known domains/emails should not be confidently rewritten incorrectly.
- Notes should be less transcript-like.
- Existing tests should pass.
- No regression in upload, processing, usage, or Markdown export.

## Release gate

A Quality Engine v2 change should not ship if:

- action recall decreases
- decision recall decreases
- hallucination risk increases
- purpose becomes missing more often
- known domains/emails are rewritten incorrectly
- Markdown export breaks
- 30–60 minute notes become less useful
