# Quality Engine v2 Shadow Comparison

This local QA report compares current baseline notes JSON against `run_quality_engine_v2(..., mode="v2")` output. It does not enable `NOTES_ENGINE=v2` or modify production behavior.

Baseline directory: `qa_results/quality_engine_v2_baseline`

## Summary

| Case | Transcript source | Purpose v1 | Purpose v2 | Actions v1 | Actions v2 | Decisions v1 | Decisions v2 | Next steps v1 | Next steps v2 | Risks v1 | Risks v2 | Open questions v1 | Open questions v2 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M01 | not available | yes | yes | 1 | 1 | 2 | 2 | 1 | 1 | 2 | 2 | n/a | 0 |
| M02 | not available | yes | yes | 2 | 2 | 0 | 0 | 2 | 2 | 1 | 1 | n/a | 0 |
| M03 | not available | yes | yes | 7 | 7 | 2 | 2 | 5 | 5 | 1 | 1 | n/a | 0 |
| M04 | not available | yes | yes | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 2 | n/a | 0 |
| S01_client_weekly_sync | not available | yes | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | n/a | 0 |

## Per-Case Metric Deltas

### M01

- Notes file: `qa_results/quality_engine_v2_baseline/M01_current_notes.json`
- Transcript source: `not available`
- V2 metadata: `{"applied": true, "fallback_used": false, "mode": "v2", "warnings": []}`

| Metric | v1 | v2 | Delta/changed |
| --- | ---: | ---: | ---: |
| purpose_present | yes | yes | no |
| action_count | 1 | 1 | 0 |
| decision_count | 2 | 2 | 0 |
| next_step_count | 1 | 1 | 0 |
| risk_count | 2 | 2 | 0 |
| open_question_count | n/a | 0 | n/a |

### M02

- Notes file: `qa_results/quality_engine_v2_baseline/M02_current_notes.json`
- Transcript source: `not available`
- V2 metadata: `{"applied": true, "fallback_used": false, "mode": "v2", "warnings": []}`

| Metric | v1 | v2 | Delta/changed |
| --- | ---: | ---: | ---: |
| purpose_present | yes | yes | no |
| action_count | 2 | 2 | 0 |
| decision_count | 0 | 0 | 0 |
| next_step_count | 2 | 2 | 0 |
| risk_count | 1 | 1 | 0 |
| open_question_count | n/a | 0 | n/a |

### M03

- Notes file: `qa_results/quality_engine_v2_baseline/M03_current_notes.json`
- Transcript source: `not available`
- V2 metadata: `{"applied": true, "fallback_used": false, "mode": "v2", "warnings": []}`

| Metric | v1 | v2 | Delta/changed |
| --- | ---: | ---: | ---: |
| purpose_present | yes | yes | no |
| action_count | 7 | 7 | 0 |
| decision_count | 2 | 2 | 0 |
| next_step_count | 5 | 5 | 0 |
| risk_count | 1 | 1 | 0 |
| open_question_count | n/a | 0 | n/a |

### M04

- Notes file: `qa_results/quality_engine_v2_baseline/M04_current_notes.json`
- Transcript source: `not available`
- V2 metadata: `{"applied": true, "fallback_used": false, "mode": "v2", "warnings": []}`

| Metric | v1 | v2 | Delta/changed |
| --- | ---: | ---: | ---: |
| purpose_present | yes | yes | no |
| action_count | 1 | 1 | 0 |
| decision_count | 1 | 1 | 0 |
| next_step_count | 1 | 1 | 0 |
| risk_count | 2 | 2 | 0 |
| open_question_count | n/a | 0 | n/a |

### S01_client_weekly_sync

- Notes file: `qa_results/quality_engine_v2_baseline/S01_client_weekly_sync_current_notes.json`
- Transcript source: `not available`
- V2 metadata: `{"applied": true, "fallback_used": false, "mode": "v2", "warnings": []}`

| Metric | v1 | v2 | Delta/changed |
| --- | ---: | ---: | ---: |
| purpose_present | yes | yes | no |
| action_count | 0 | 0 | 0 |
| decision_count | 0 | 0 | 0 |
| next_step_count | 0 | 0 | 0 |
| risk_count | 0 | 0 | 0 |
| open_question_count | n/a | 0 | n/a |
