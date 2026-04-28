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

---

## Hardened validation run

After adding polling timeout hardening and worker preflight protection, the Pilot RC1 golden consistency gate was rerun successfully.

Latest hardened output directory:

test_outputs/pilot_rc1_golden_consistency_gate_20260428_221515

Archived evidence:

../mna_pilot_rc1_hardened_golden_consistency_gate_20260428_221515.tar.gz

## Hardened validation result

Overall average score: **95.5 / 100**

Passing samples: **4 / 4**

| Sample | Status | Score | Actions | Decisions | Markdown | Safety Signal |
|---|---:|---:|---:|---:|---:|---:|
| client_weekly_sync_10min_m4a | PASS | 97 | 6 | 4 | True | False |
| meeting_30min_script_wav | PASS | 100 | 6 | 5 | True | False |
| meeting_81_m4a | PASS | 97 | 6 | 4 | True | False |
| meeting_86_mp3 | PASS | 88 | 0 | 0 | True | True |

## Hardened gate confirmation

This validation confirms:

- the worker preflight fails fast when the worker is not running
- the gate prints clear remediation steps instead of silently waiting on queued jobs
- the full benchmark still passes after worker preflight hardening
- the longer polling timeout supports slower safety samples
- Meeting 86 continues to protect against fake decisions and fake action items

## Updated launch-readiness interpretation

Pilot RC1 is now approximately **92-95 / 100** ready for controlled pilot demos.

The strongest supported external claim remains:

Best for short, structured business meetings.
