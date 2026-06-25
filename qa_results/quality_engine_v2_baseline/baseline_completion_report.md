# Quality Engine v2 Baseline Completion Report

## Status

The five-recording quality baseline has been created.

## Completed

- [x] Selected five fixed test meetings:
  - M01
  - M02
  - M03
  - M04
  - S01_client_weekly_sync

- [x] Saved current MeetIQ generated notes for each meeting.
- [x] Saved current MeetIQ generated JSON outputs for each meeting.
- [x] Reused existing M01-M04 quality reviews.
- [x] Added fifth S01 client weekly sync sample.
- [x] Ran existing automated client-facing quality gate.
- [x] Captured automated baseline scores.
- [x] Listed top repeated quality failures.
- [x] Created scorecard template.
- [x] Created perfect-notes placeholder files.
- [x] Created transcript reference file.

## Partially complete

- [ ] Exact transcript/source mapping for each baseline sample still needs final confirmation.
- [ ] Manually corrected perfect notes still need to be filled.
- [ ] Manual section-by-section scorecard values still need to be filled.

## Automated baseline scores

| Recording | Score |
|---|---:|
| M01 | 35 |
| M02 | 35 |
| M03 | 70 |
| M04 | 35 |
| S01_client_weekly_sync | 35 |

## Follow-up plan added

The remaining manual evaluation items are tracked in:

- manual_evaluation_followup_plan.md

This covers:

- manually corrected perfect notes
- manual section-by-section scoring
- exact transcript/source mapping confirmation

## Conclusion

The baseline is complete enough to support the next task: Quality Engine v2 design and implementation.

Quality Engine v2 should not modify billing, auth, upload limits, deployment settings, or production environment configuration.

The next engineering task should focus only on note quality:

1. Purpose inference fallback
2. Stronger action recall
3. Stronger decision extraction
4. Open-question separation
5. Owner/deadline extraction
6. Known entity/domain guardrails
7. Cleanup of transcript-like phrasing
8. Quality-check/critic pass
9. Regression score gate
