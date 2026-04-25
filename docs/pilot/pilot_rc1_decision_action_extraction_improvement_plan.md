# Pilot RC1 Decision and Action Extraction Improvement Plan

## Purpose

This plan targets the highest-impact quality gap from the Pilot RC1 benchmark baseline: structured decision and action extraction across realistic meeting types.

## Current Benchmark Signal

- Benchmark cases analyzed: 5
- Jobs succeeded: 5/5
- Cases missing structured decisions: 5/5
- Cases missing structured actions: 4/5

## Gap Summary

| Case | Job Status | Key Points | Decisions | Actions | Needs Decision Fix | Needs Action Fix |
|---|---|---:|---:|---:|---|---|
| 01_client_weekly_sync | succeeded | 1 | 0 | 0 | yes | yes |
| 02_product_planning | succeeded | 3 | 0 | 0 | yes | yes |
| 03_sales_discovery | succeeded | 6 | 0 | 6 | yes | no |
| 04_engineering_standup | succeeded | 1 | 0 | 0 | yes | yes |
| 05_executive_decision_review | succeeded | 1 | 0 | 0 | yes | yes |

## Recommended Implementation Scope

Improve deterministic extraction for explicit business-meeting language:

- `Decision:` prefixes
- `we decided to ...`
- `we agreed to ...`
- `we will ...` when stated as an outcome or decision
- `we will not ...` for negative executive decisions
- `Action item for OWNER: TASK`
- `OWNER should ...`
- `OWNER will ...` when the sentence clearly assigns work

## Acceptance Criteria

The next patch should raise the benchmark from 64/100 to at least 80/100 by improving:

- decision recall across at least 4 of 5 benchmark cases
- action recall across at least 4 of 5 benchmark cases
- no regression to job completion
- no regression to summary/key-point generation

## Best-Practice Guardrail

This should be implemented as a narrow extraction improvement, not as broad prompt-style rewriting. The goal is to improve structured recall while avoiding hallucinated decisions or fake owners.
