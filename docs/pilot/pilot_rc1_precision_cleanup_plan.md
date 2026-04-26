# Pilot RC1 Precision Cleanup Plan

## Purpose

Improve client-facing quality after the successful Pilot RC1 structured recall pass.

The previous workstream proved technical recall:
- Jobs succeeded: 5/5
- Structured decisions captured: 5/5
- Structured actions captured: 5/5
- Benchmark score: 100/100

This follow-up workstream focuses on precision and readability.

## Current issue

The structured fallback now captures decisions and actions reliably, but some generated outputs may still contain:
- duplicate decision/action text
- generic owners such as Team, Product, Engineering, Leadership, or Operations
- action phrasing that is technically valid but less client-ready
- repeated decision wording when both heuristic and fallback extraction fire

## Goals

1. Preserve recall:
   - decisions remain at least 5/5 on Pilot RC1 benchmark
   - actions remain at least 5/5 on Pilot RC1 benchmark

2. Improve precision:
   - reduce duplicate decisions
   - reduce duplicate action items
   - normalize weak/generic owner labels when possible
   - keep output clear and client-ready

3. Avoid regressions:
   - all jobs should still succeed
   - non-meeting safety behavior should remain intact
   - existing code checks must pass

## Proposed implementation

- Add deterministic deduplication for Pilot RC1 decision/action fallback outputs.
- Normalize action owners only when confidence is high.
- Prefer explicit named owners over department/generic owners.
- Preserve generic owners when they are the only available owner signal.
- Add or update benchmark documentation after validation.

## Acceptance criteria

- Pilot RC1 spoken-audio benchmark succeeds: 5/5 jobs.
- Structured decisions: at least 5/5 cases.
- Structured actions: at least 5/5 cases.
- No duplicate-heavy output in inspected notes.
- py_compile passes.
- ruff passes.
- mypy passes.
- pre-commit passes.

## Status

Planned.
