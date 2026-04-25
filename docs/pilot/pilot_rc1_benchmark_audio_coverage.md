# Pilot RC1 Benchmark Audio Coverage

## Purpose

This benchmark expands Pilot RC1 validation beyond one controlled demo file by testing multiple realistic meeting formats.

## Coverage Set

- Client weekly sync
- Product planning meeting
- Sales discovery call
- Engineering standup
- Executive decision review

## Result

- Benchmark cases: 5
- Jobs succeeded: 5/5
- Average benchmark score: 64/100

## Scoring Model

| Signal | Points |
|---|---:|
| Job succeeded | 20 |
| Summary generated | 20 |
| Purpose and outcome generated | 15 |
| Key points generated | 15 |
| Decisions generated | 15 |
| Action items generated | 15 |
| Total | 100 |

## Benchmark Summary

| Case | Status | Score | Key Points | Decisions | Actions |
|---|---|---:|---:|---:|---:|
| 01_client_weekly_sync | succeeded | 55 | 1 | 0 | 0 |
| 02_product_planning | succeeded | 70 | 3 | 0 | 0 |
| 03_sales_discovery | succeeded | 85 | 6 | 0 | 6 |
| 04_engineering_standup | succeeded | 55 | 1 | 0 | 0 |
| 05_executive_decision_review | succeeded | 55 | 1 | 0 | 0 |

## Evidence Location

Benchmark outputs are saved under test_outputs/pilot_rc1_benchmark_audio/.

Text scripts used to generate local benchmark audio are saved under test_assets/pilot_rc1_benchmark_audio/.

Generated audio binaries are intentionally ignored by Git to avoid committing media files.

## Product Interpretation

A strong result here means Pilot RC1 is not only passing one live rehearsal, but also performing across several realistic meeting formats that include summaries, decisions, and action items.
