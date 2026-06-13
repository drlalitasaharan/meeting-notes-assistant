# Chunk-Level Long-Meeting Action Extraction Plan

## Goal

Improve long-meeting action recall by extracting candidate actions from transcript chunks before final note generation.

## Candidate action fields

Each extracted candidate should include:

- action
- owner
- deadline
- reason/context
- related decision
- related risk
- source chunk
- confidence

## Consolidation rules

- Merge duplicate actions.
- Do not merge if owner, deliverable, or deadline differs.
- Keep specific actions over vague actions.
- Preserve actions from the beginning, middle, and end of the meeting.
- Do not invent owners or deadlines.
- Use "Unassigned" when owner is unclear.
- Use "No deadline stated" when deadline is unclear.

## Scoring

Compare actual output against expected action ground truth.

Score:
- must-capture action recall
- owner accuracy
- deadline accuracy
- duplicate rate
- hallucination rate
- coverage across beginning/middle/end
