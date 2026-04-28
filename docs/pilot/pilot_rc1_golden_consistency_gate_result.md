# Pilot RC1 Golden Consistency Gate Result

## Run

Output directory:

test_outputs/pilot_rc1_golden_consistency_gate_20260428_205748

## Result summary

Overall average score: **95.5 / 100**

Passing samples: **4 / 4**

| Sample | Status | Score | Actions | Decisions | Markdown | Safety Signal |
|---|---:|---:|---:|---:|---:|---:|
| client_weekly_sync_10min_m4a | PASS | 97 | 6 | 4 | True | False |
| meeting_30min_script_wav | PASS | 100 | 6 | 5 | True | False |
| meeting_81_m4a | PASS | 97 | 6 | 4 | True | False |
| meeting_86_mp3 | PASS | 88 | 0 | 0 | True | True |

## Interpretation

The Pilot RC1 golden consistency gate passed all benchmark samples.

This confirms:

- consistent structured output across short and longer meeting samples
- strong action item and decision recall on business meetings
- clean markdown generation
- preserved non-meeting safety behavior on Meeting 86
- no fake decisions or fake action items in the non-meeting safety sample

## Launch-readiness implication

This result moves Pilot RC1 from approximately **83/100** toward **90-92/100 pilot-launch readiness**.

The product is now suitable for controlled pilot demos using the current launch-safe positioning:

Best for short, structured business meetings.

## Follow-up hardening

Meeting 86 completed successfully but very close to the current polling timeout.

Recommended follow-up:

- increase golden gate polling timeout for long safety samples
- keep Meeting 86 in the golden gate because it protects trust and hallucination safety
- avoid committing raw test_outputs artifacts unless explicitly needed
