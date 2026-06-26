# Quality Engine v2 Shadow Comparison

This local QA report compares current baseline notes JSON against `run_quality_engine_v2(..., mode="v2")` output. It does not enable `NOTES_ENGINE=v2` or modify production behavior.

Baseline directory: `qa_results/quality_engine_v2_baseline`

## Summary

| Case | Transcript source | Purpose v1 | Purpose v2 | Actions v1 | Actions v2 | Decisions v1 | Decisions v2 | Next steps v1 | Next steps v2 | Risks v1 | Risks v2 | Open questions v1 | Open questions v2 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M01 | qa_results/quality_engine_v2_baseline/transcripts/M01.txt | yes | yes | 1 | 28 | 2 | 14 | 1 | 5 | 2 | 9 | n/a | 6 |
| M02 | qa_results/quality_engine_v2_baseline/transcripts/M02.txt | yes | yes | 2 | 11 | 0 | 3 | 2 | 5 | 1 | 5 | n/a | 10 |
| M03 | qa_results/quality_engine_v2_baseline/transcripts/M03.txt | yes | yes | 7 | 14 | 2 | 6 | 5 | 5 | 1 | 5 | n/a | 9 |
| M04 | qa_results/quality_engine_v2_baseline/transcripts/M04.txt | yes | yes | 1 | 8 | 1 | 4 | 1 | 5 | 2 | 7 | n/a | 9 |
| S01_client_weekly_sync | qa_results/quality_engine_v2_baseline/transcripts/S01_client_weekly_sync.txt | yes | yes | 0 | 8 | 0 | 0 | 0 | 5 | 0 | 0 | n/a | 0 |

## Per-Case Metric Deltas

### M01

- Notes file: `qa_results/quality_engine_v2_baseline/M01_current_notes.json`
- Transcript source: `qa_results/quality_engine_v2_baseline/transcripts/M01.txt`
- V2 metadata: `{"applied": true, "fallback_used": false, "mode": "v2", "warnings": []}`

| Metric | v1 | v2 | Delta/changed |
| --- | ---: | ---: | ---: |
| purpose_present | yes | yes | no |
| action_count | 1 | 28 | 27 |
| decision_count | 2 | 14 | 12 |
| next_step_count | 1 | 5 | 4 |
| risk_count | 2 | 9 | 7 |
| open_question_count | n/a | 6 | n/a |

### M02

- Notes file: `qa_results/quality_engine_v2_baseline/M02_current_notes.json`
- Transcript source: `qa_results/quality_engine_v2_baseline/transcripts/M02.txt`
- V2 metadata: `{"applied": true, "fallback_used": false, "mode": "v2", "warnings": []}`

| Metric | v1 | v2 | Delta/changed |
| --- | ---: | ---: | ---: |
| purpose_present | yes | yes | no |
| action_count | 2 | 11 | 9 |
| decision_count | 0 | 3 | 3 |
| next_step_count | 2 | 5 | 3 |
| risk_count | 1 | 5 | 4 |
| open_question_count | n/a | 10 | n/a |

### M03

- Notes file: `qa_results/quality_engine_v2_baseline/M03_current_notes.json`
- Transcript source: `qa_results/quality_engine_v2_baseline/transcripts/M03.txt`
- V2 metadata: `{"applied": true, "fallback_used": false, "mode": "v2", "warnings": []}`

| Metric | v1 | v2 | Delta/changed |
| --- | ---: | ---: | ---: |
| purpose_present | yes | yes | no |
| action_count | 7 | 14 | 7 |
| decision_count | 2 | 6 | 4 |
| next_step_count | 5 | 5 | 0 |
| risk_count | 1 | 5 | 4 |
| open_question_count | n/a | 9 | n/a |

### M04

- Notes file: `qa_results/quality_engine_v2_baseline/M04_current_notes.json`
- Transcript source: `qa_results/quality_engine_v2_baseline/transcripts/M04.txt`
- V2 metadata: `{"applied": true, "fallback_used": false, "mode": "v2", "warnings": []}`

| Metric | v1 | v2 | Delta/changed |
| --- | ---: | ---: | ---: |
| purpose_present | yes | yes | no |
| action_count | 1 | 8 | 7 |
| decision_count | 1 | 4 | 3 |
| next_step_count | 1 | 5 | 4 |
| risk_count | 2 | 7 | 5 |
| open_question_count | n/a | 9 | n/a |

### S01_client_weekly_sync

- Notes file: `qa_results/quality_engine_v2_baseline/S01_client_weekly_sync_current_notes.json`
- Transcript source: `qa_results/quality_engine_v2_baseline/transcripts/S01_client_weekly_sync.txt`
- V2 metadata: `{"applied": true, "fallback_used": false, "mode": "v2", "warnings": []}`

| Metric | v1 | v2 | Delta/changed |
| --- | ---: | ---: | ---: |
| purpose_present | yes | yes | no |
| action_count | 0 | 8 | 8 |
| decision_count | 0 | 0 | 0 |
| next_step_count | 0 | 5 | 5 |
| risk_count | 0 | 0 | 0 |
| open_question_count | n/a | 0 | n/a |
