# Automated Gate Results — Current Baseline

Existing script used:

PYTHONPATH=backend .venv/bin/python scripts/quality_gates/pilot_rc1_client_facing_gate.py <notes_json>

## Results

| Recording | Decision Count | Action Count | Next Steps Count | Existing Gate Score | Result |
|---|---:|---:|---:|---:|---|
| M01 | 2 | 1 | 1 | 35 | Review needed |
| M02 | 0 | 2 | 2 | 35 | Review needed |
| M03 | 2 | 7 | 5 | 70 | Review needed |
| M04 | 1 | 1 | 1 | 35 | Review needed |
| S01_client_weekly_sync | 0 | 0 | 0 | 35 | Review needed |

## Interpretation

The existing gate confirms the baseline quality gap:

1. M01, M02, M04, and S01 have thin action/decision/next-step extraction.
2. M03 is the strongest sample and should be preserved during Quality Engine v2.
3. All five samples require review before claiming best-in-class quality.
4. Quality Engine v2 should improve action recall, decision recall, next-step specificity, and structure.
