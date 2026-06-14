# Chunk Action Extraction Scorecard

| Meeting | Duration | Expected must-capture | Found | Recall | Owner accuracy | Deadline accuracy | False positives | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| S01 | short | TBD | TBD | TBD | TBD | TBD | TBD | Template only |
| IB4001 | 29m | 1 | TBD | TBD | TBD | TBD | TBD | Starter ground truth filled |
| ES2006c | 36m | TBD | TBD | TBD | TBD | TBD | TBD | Review-needed ground truth |
| IS1000b | 39m | TBD | TBD | TBD | TBD | TBD | TBD | Template only |
| IN1016 | 60m | 2 | TBD | TBD | TBD | TBD | TBD | Starter ground truth filled |

## Current status

- Planning scaffold: complete.
- Public-launch acceptance criteria: complete.
- Starter ground truth: complete for IB4001 and IN1016.
- ES2006c: completion proof exists, but expected actions still need manual transcript validation.
- Automated scoring scaffold: complete.
- Chunk-level extraction scaffold: complete.
- Consolidation pass: complete.
- Chunk action recovery orchestrator: complete.
- Persisted action contract integration: complete.
- Existing transcript-recall fallback is preserved before chunk recovery.
- Broader action-recall safety tests passed: 36 passed.

## Remaining before PR merge

- Fill ground truth for S01, IS1000b, and ES2006c.
- Run real long-meeting regression outputs through the new path.
- Update actual Found/Recall/Owner/Deadline/False-positive columns.
- Document remaining limitations.
