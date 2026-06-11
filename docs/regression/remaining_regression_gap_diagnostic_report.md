# Remaining Regression Gap Diagnostic Report

## Purpose

This report isolates the remaining low-scoring regression cases after the long-meeting action recall and decision/risk synthesis improvements.

The current full baseline after the latest merged improvement is:

- Average score: **0.5057**
- Passed cases: **3/12**

## Target Cases

These are the next cases to improve:

| Case | Score | Decisions | Actions | Risks | Context |
|---|---:|---:|---:|---:|---:|
| S03 | 0.0779 | 0/0 (1.0) | 0/1 (0.0) | 0/0 (1.0) | 2/7 (0.2857) |
| M02 | 0.15 | 0/2 (0.0) | 0/0 (1.0) | 0/5 (0.0) | 3/5 (0.6) |
| M03 | 0.21 | 2/6 (0.3333) | 0/1 (0.0) | 2/5 (0.4) | 1/3 (0.3333) |
| L01 | 0.35 | 1/8 (0.125) | 4/10 (0.4) | 4/6 (0.6667) | 0/0 (1.0) |

## Guardrail Cases

These cases should remain stable while improving the weak cases:

| Case | Score | Decisions | Actions | Risks | Context |
|---|---:|---:|---:|---:|---:|
| S01 | 0.8824 | 2/3 (0.6667) | 3/3 (1.0) | 1/1 (1.0) | 0/0 (1.0) |
| M01 | 0.5686 | 2/6 (0.3333) | 5/6 (0.8333) | 1/3 (0.3333) | 0/0 (1.0) |
| M04 | 0.625 | 5/8 (0.625) | 0/0 (1.0) | 0/0 (1.0) | 0/0 (1.0) |
| M05 | 0.4118 | 0/2 (0.0) | 1/2 (0.5) | 5/5 (1.0) | 0/0 (1.0) |
| L02 | 0.8271 | 6/7 (0.8571) | 5/5 (1.0) | 4/5 (0.8) | 1/3 (0.3333) |
| L03 | 0.8643 | 5/7 (0.7143) | 5/5 (1.0) | 6/6 (1.0) | 2/3 (0.6667) |
| L04 | 0.6018 | 3/9 (0.3333) | 5/5 (1.0) | 3/7 (0.4286) | 1/4 (0.25) |

## Current Reading

The weakest remaining cases are no longer purely long-meeting action recall failures.

The remaining gap appears to be a mixed quality problem across short, medium, noisy, and partially structured transcripts:

- **S03** remains the lowest short case.
- **M02** remains a low medium case.
- **M03** improved from 0.05 to 0.21 but still remains weak.
- **L01** remains below passing despite long-meeting improvements.

## Recommended Next Implementation Direction

The next implementation should not broadly expand the long-meeting synthesis helpers again.

Recommended next branch should be one of:

1. **Improve noisy/low-signal transcript normalization** if M03 and S03 share evidence loss.
2. **Improve medium-case decision/action/risk extraction** if M02 and M03 share owner/action or decision phrasing failures.
3. **Improve structured summary fallback quality** if the weak cases mostly depend on generated summary text instead of extracted signals.

## Commit Rule for Next Code Branch

Only commit a follow-up code branch if it satisfies all of the following:

- At least one of S03, M02, M03, or L01 improves.
- No guardrail case drops meaningfully.
- Full baseline stays above **0.5057**.
- No evaluator or fixture changes are used to create the improvement.
