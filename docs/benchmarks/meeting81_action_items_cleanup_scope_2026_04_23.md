# Meeting 81 action-items cleanup pass

## Goal
Improve action-item precision and recall so action items are more concrete, less conversational, and better aligned with real business follow-up tasks.

## Scope
Limited to action-item extraction and cleanup only.

## Validation set
- Meeting 81 = primary benchmark
- Meeting 86 = safety benchmark
- 30-minute script = regression benchmark

## Promotion rule
Promote only if:
- Meeting 81 action items become more concrete and useful
- malformed or vague action items are reduced
- Meeting 86 remains safely downgraded
- 30-minute benchmark remains stable
