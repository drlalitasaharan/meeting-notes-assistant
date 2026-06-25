# Quality Engine v2

## Goal

Improve MeetIQ notes quality for 30–60 minute uploaded recordings while keeping the current working product stable.

## Baseline

Use the merged five-recording baseline:

* qa_results/quality_engine_v2_baseline/M01_current_notes.json
* qa_results/quality_engine_v2_baseline/M02_current_notes.json
* qa_results/quality_engine_v2_baseline/M03_current_notes.json
* qa_results/quality_engine_v2_baseline/M04_current_notes.json
* qa_results/quality_engine_v2_baseline/S01_client_weekly_sync_current_notes.json

Current automated baseline scores:

* M01: 35
* M02: 35
* M03: 70
* M04: 35
* S01_client_weekly_sync: 35

## Scope

Implement a production-safe notes quality improvement layer focused on:

1. Purpose inference fallback
2. Stronger action recall
3. Stronger decision extraction
4. Open-question separation
5. Owner/deadline normalization
6. Known entity/domain guardrails
7. Cleanup of transcript-like phrasing
8. Quality-check/critic pass
9. Regression score gate

## Safety rules

Do not change:

* billing
* checkout
* webhooks
* auth
* upload limits
* plan limits
* deployment settings
* production environment configuration

Keep the current notes pipeline stable.

Prefer additive changes behind safe functions, tests, or feature flags.

## V2 structured JSON schema

Quality Engine v2 should produce or improve the following internal structure:

```json
{
  "summary_slots": {
    "purpose": "",
    "edited_summary": "",
    "outcome": "",
    "risks": [],
    "next_steps": [],
    "open_questions": [],
    "known_entity_warnings": []
  },
  "decision_objects": [
    {
      "text": "",
      "confidence": 0.0,
      "evidence": ""
    }
  ],
  "action_item_objects": [
    {
      "owner": "",
      "task": "",
      "deadline": null,
      "status": "open",
      "priority": "medium",
      "confidence": 0.0,
      "evidence": ""
    }
  ],
  "key_points": [],
  "quality_engine_v2": {
    "applied": false,
    "mode": "v1",
    "warnings": [],
    "fallback_used": false
  }
}
```

## Required output sections

Quality Engine v2 should support these sections:

* purpose
* summary
* decisions
* action items
* open questions
* risks
* key points
* known entity warnings
* evidence/confidence internally

## Known entity list

Quality Engine v2 should protect known product, company, platform, plan, and support names from confident incorrect rewriting.

Known entities:

* Acjen AI
* MeetIQ
* [support@acjen.ai](mailto:support@acjen.ai)
* PayPal
* Square
* Render
* Vercel
* GoDaddy
* BetaList
* Indie Hackers
* Product Hunt
* GitHub
* Markdown
* Starter
* Pro Pilot

## Feature flag design

Use a notes-engine mode flag before enabling runtime behavior broadly.

### `NOTES_ENGINE=v1`

Current production behavior.

Quality Engine v2 is not applied.

This should remain the default until v2 has been validated.

### `NOTES_ENGINE=v2`

Apply Quality Engine v2 before notes are persisted.

This mode should only be enabled after tests and baseline comparison show quality improvement without regressions.

### `NOTES_ENGINE=shadow`

Generate v1 notes as the user-facing output.

Also run Quality Engine v2 internally for comparison.

Do not expose v2 output to users.

Store or log comparison metrics only if safe.

Shadow mode should be used before enabling v2 for real user-facing output.

## Fallback behavior

Quality Engine v2 must be fail-safe.

If v2 raises an exception, returns invalid structure, removes too many actions, removes existing decisions, or produces empty client-facing notes:

1. Keep the original v1 notes.
2. Mark `quality_engine_v2.fallback_used = true` if metadata is available.
3. Do not fail the upload or meeting processing job.
4. Do not block Markdown export.
5. Do not affect billing, usage, auth, upload limits, or checkout.

## Shadow-mode comparison behavior

In shadow mode, compare v1 and v2 on:

* purpose presence
* action count
* decision count
* next-step count
* open-question presence
* known entity warnings
* hallucination-risk warnings
* Markdown safety

Shadow mode should help validate v2 without changing user-facing output.

## Acceptance criteria

* Purpose should not be missing when meeting topic is clear.
* Action item recall should improve for M01, M02, M04, and S01.
* M03 should not regress.
* Decisions should be separated from general discussion.
* Open questions should be separated from key points.
* Known domains/emails should not be confidently rewritten incorrectly.
* Notes should be less transcript-like.
* Existing tests should pass.
* No regression in upload, processing, usage, or Markdown export.

## Release gate

A Quality Engine v2 change should not ship if:

* action recall decreases
* decision recall decreases
* hallucination risk increases
* purpose becomes missing more often
* known domains/emails are rewritten incorrectly
* Markdown export breaks
* 30–60 minute notes become less useful

## Implementation order

Implement in small safe steps:

1. Keep current v1 behavior unchanged.
2. Add Quality Engine v2 helper functions.
3. Add unit tests for each helper.
4. Add feature flag support.
5. Add shadow-mode support before user-facing v2 output.
6. Compare v1 and v2 against the five-recording baseline.
7. Only enable v2 user-facing behavior after it improves quality without regressions.

## Out of scope

Quality Engine v2 should not modify:

* billing
* checkout
* PayPal integration
* Square integration
* auth
* upload limits
* plan limits
* usage metering
* frontend pricing UI
* deployment settings
* production environment configuration

## Current implementation status

Completed:

* Quality Engine v2 task branch created.
* Task spec created.
* Quality Engine v2 foundation module added.
* Unit tests added for:

  * purpose fallback
  * next-step sync from actions
  * decision preservation
* Full validation passed with 215 tests.

Not yet done:

* Feature flag wiring.
* Shadow-mode comparison.
* Runtime integration into `process_meeting.py`.
* Full five-recording v1 vs v2 comparison.
* Manual perfect notes.
* Manual section-by-section scoring.
* Exact transcript/source mapping confirmation for every baseline sample.
