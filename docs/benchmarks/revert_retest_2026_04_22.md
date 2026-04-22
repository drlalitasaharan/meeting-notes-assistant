# Revert retest - April 22, 2026

## Meeting 81
- meeting id: 109
- result: still weak
- decisions_count: 2
- action_items_count: 1
- issue: summary remains long, duplicated, transcript-like

## Meeting 86
- meeting id: 110
- result: safety issue remains
- decisions_count: 0
- action_items_count: 0
- issue: non-meeting audio still gets fake meeting-style summary ending

## 30-minute script
- meeting id: 111
- result: still strongest baseline
- decisions_count: 6
- action_items_count: 4
- issue: slightly lower than prior retest, but still usable

## Conclusion
The signal boost was not the root cause.
Core issues remain in baseline extraction / summarization:
- weak precision on meeting 81
- false meeting framing on meeting 86

Recommended next step:
- add meeting-confidence guardrail
- add precision-only decision/action extractor
- keep 30-minute path as regression benchmark
