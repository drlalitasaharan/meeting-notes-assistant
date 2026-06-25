# MeetIQ Quality Engine v2 Baseline

## Purpose

This folder captures current MeetIQ note quality before Quality Engine v2 changes.

## Baseline samples

1. M01 — 30–60 minute baseline
2. M02 — 30–60 minute baseline
3. M03 — 30–60 minute baseline
4. M04 — 30–60 minute baseline / long meeting
5. S01_client_weekly_sync — short client-style meeting

## Automated score baseline

Existing client-facing quality gate scores:

| Recording | Score | Result |
|---|---:|---|
| M01 | 35 | Review needed |
| M02 | 35 | Review needed |
| M03 | 70 | Review needed |
| M04 | 35 | Review needed |
| S01_client_weekly_sync | 35 | Review needed |

## Existing known failure modes

From the previous 30–60 minute consolidated review:

1. Important owner-based actions are sometimes missed.
2. Repeated actions are not always merged into the strongest owner/task/deadline version.
3. Decision extraction includes broken fragments.
4. Risk extraction misses reliability, dependency, delay, and long-recording caution content.
5. Next steps can be too generic.
6. Summary can be too narrow.
7. Markdown/ASR cleanup issues remain.

## Quality Engine v2 target fixes

1. Purpose inference fallback
2. Stronger action recall
3. Stronger decision extraction
4. Open-question separation
5. Owner/deadline extraction
6. Known entity/domain guardrails
7. Cleanup of transcript-like phrasing
8. Quality-check/critic pass
9. Regression score gate

## Safety rule

Do not change billing, auth, upload limits, deployment settings, or production environment configuration in this quality baseline task.
