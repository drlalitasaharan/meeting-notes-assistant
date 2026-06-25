# MeetIQ Quality Engine v2 — Five Recording Baseline Scorecard

Purpose:
Create a baseline before improving MeetIQ note quality.

Scoring:
1 = poor
5 = acceptable MVP
8 = strong
10 = best-in-class

## Score table

| Recording | Purpose | Summary | Actions | Decisions | Owners | Deadlines | Open Questions | Entity Accuracy | Hallucination Risk | Structure | Usefulness | Overall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M01 |  |  |  |  |  |  |  |  |  |  |  |  |
| M02 |  |  |  |  |  |  |  |  |  |  |  |  |
| M03 |  |  |  |  |  |  |  |  |  |  |  |  |
| M04 |  |  |  |  |  |  |  |  |  |  |  |  |
| S01_client_weekly_sync |  |  |  |  |  |  |  |  |  |  |  |  |

## Automated gate baseline

| Recording | Existing Gate Score | Result |
|---|---:|---|
| M01 | 35 | Review needed |
| M02 | 35 | Review needed |
| M03 | 70 | Review needed |
| M04 | 35 | Review needed |
| S01_client_weekly_sync | 35 | Review needed |

## Repeated failure modes

1. Important owner-based actions are sometimes missed.
2. Action recall is inconsistent across meetings.
3. Repeated actions are not always merged into the strongest owner/task/deadline version.
4. Decision extraction can be too thin or missing.
5. Decision extraction can include weak or broken fragments.
6. Next steps can be too generic.
7. Summary can be too narrow or not sufficiently executive-ready.
8. Risk extraction misses reliability, dependency, delay, and long-recording caution content.
9. Open questions are not consistently separated as their own review section.
10. Markdown/ASR cleanup issues remain, including transcript-like phrasing and possible entity/domain errors.

## Best fast fixes for Quality Engine v2

1. Add chunk-level action recall pass.
2. Add decision-only extraction pass.
3. Add purpose inference fallback.
4. Add open-question separation.
5. Add owner/deadline normalization.
6. Add known entity/domain guardrail.
7. Add critic pass before final notes are saved.
8. Add regression gate so action/decision recall cannot get worse.

## Release-blocking quality gates

A new notes engine should not ship if:
- action recall decreases
- decision recall decreases
- purpose becomes missing more often
- hallucination risk increases
- known domains/emails are rewritten incorrectly
- markdown structure breaks
- notes become less useful for 30–60 minute recordings
