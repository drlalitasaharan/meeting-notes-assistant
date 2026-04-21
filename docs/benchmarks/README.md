# Benchmarks Index

This folder contains the current benchmark set for Meeting Notes Assistant quality evaluation.

## Active benchmarks

### 1) meeting_81_phase4_ast_baseline
Role:
- Historical extraction-quality reference

Why it matters:
- Captured a strong structured output with clean decisions and action items
- Useful as a comparison point for extraction richness

Files:
- docs/benchmarks/meeting_81_phase4_ast_baseline.md
- test_outputs/meeting_81_phase4_ast_baseline_notes_ai.json
- test_outputs/meeting_81_phase4_ast_baseline_notes.md

---

### 2) meeting_84_trust_guardrails_10min_baseline
Role:
- Primary short-meeting launch/demo benchmark

Why it matters:
- Best current benchmark for short structured business meetings
- Recommended baseline for demos, pilot outreach, screenshots, and regression checks

Files:
- docs/benchmarks/meeting_84_trust_guardrails_10min_baseline.md
- test_outputs/meeting_84_trust_guardrails_10min_baseline_notes_ai.json
- test_outputs/meeting_84_trust_guardrails_10min_baseline_notes.md

---

### 3) meeting_86_non_meeting_safety_baseline
Role:
- Primary non-meeting safety benchmark

Why it matters:
- Confirms non-meeting audio does not generate fabricated business notes
- Protects trust and validates safe fallback behavior

Files:
- docs/benchmarks/meeting_86_non_meeting_safety_baseline.md
- test_outputs/meeting_86_non_meeting_safety_baseline_notes_ai.json
- test_outputs/meeting_86_non_meeting_safety_baseline_notes.md

---

## How to use this benchmark set

Use meeting 84 when validating:
- launch-readiness
- demo quality
- short structured business meeting extraction

Use meeting 86 when validating:
- non-meeting safety
- hallucination prevention
- trust guardrails

Use meeting 81 when validating:
- richer action/decision extraction behavior
- historical comparison after post-processing changes

---

## Current product interpretation

Current strongest supported claim:
- The product performs best on short, structured business meetings.

Current trust behavior:
- Non-meeting audio is safely downgraded instead of being turned into false meeting notes.

Current gap:
- 30-minute quality still needs another extraction-quality pass before broader launch claims.
