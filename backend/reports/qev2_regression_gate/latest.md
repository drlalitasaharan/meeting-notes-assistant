# Quality Engine v2 Regression Gate

This report is generated from fixture transcripts only. It does not enable Quality Engine v2 rollout or change production note behavior.

- Fixture directory: `backend/tests/fixtures/meeting_regression`
- Cases: S01, M01, M04, M05, L01
- Minimum v2 score: 0.7
- Result: FAIL

| Case | v1 score | v2 score | Result | Failed checks |
| --- | ---: | ---: | --- | --- |
| S01 | 0.8824 | 0.8824 | FAIL | critic_passed |
| M01 | 0.4117 | 0.647 | FAIL | v2_score_meets_threshold, critic_passed |
| M04 | 0.75 | 0.75 | FAIL | critic_passed |
| M05 | 0.1765 | 0.1765 | FAIL | v2_score_meets_threshold, critic_passed |
| L01 | 1.0 | 1.0 | FAIL | critic_passed |

## Warnings

- S01: Quality Engine v2 critic reported warnings.
- M01: Quality Engine v2 score is below the regression threshold.
- M01: Quality Engine v2 critic reported warnings.
- M04: Quality Engine v2 critic reported warnings.
- M05: Quality Engine v2 score is below the regression threshold.
- M05: Quality Engine v2 critic reported warnings.
- L01: Quality Engine v2 critic reported warnings.
