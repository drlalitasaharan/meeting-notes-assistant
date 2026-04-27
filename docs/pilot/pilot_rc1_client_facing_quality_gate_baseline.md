# Pilot RC1 Client-Facing Extraction Quality Gate Baseline

Date: 2026-04-27

## Summary

A focused client-facing extraction quality gate was added and tested against the 10-minute client weekly sync demo audio.

The infrastructure path passed: backend health, meeting creation, audio upload, worker processing, notes JSON generation, and Markdown generation all completed successfully.

The extraction quality gate did not pass, which confirms that the next workstream should focus on action-item and next-step recall rather than general infrastructure.

## Observed Gate Result

```text
decision_count: 5
action_count: 2
next_steps_count: 1
has_weekly_priority_action: False
client_facing_score: 50
CLIENT_FACING_REHEARSAL_REVIEW_NEEDED
```

## Quality Gaps Observed

- Action recall is still below the client-facing threshold.
- Next-step recall is still below the client-facing threshold.
- The weekly-priority action was not captured as an action item.
- A malformed decision fragment appeared in the Decisions section.
- A false action owner was produced from phrase-like text.

## Acceptance Target

```text
- decision_count >= 3
- action_count >= 3
- next_steps_count >= 3
- has_weekly_priority_action is True
- no malformed decisions
- no false action owners
- no bad next steps
- no duplicate actions
- client_facing_score >= 95
```

## Decision

This branch commits the reusable quality gate and baseline evidence only.

Production extraction logic should be improved in a separate focused patch after this gate is merged.
