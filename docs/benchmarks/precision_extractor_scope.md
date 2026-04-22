# Precision extractor scope

## Goal
Improve structured meeting extraction quality without weakening:
- non-meeting safety
- 30-minute benchmark stability

## Problems to solve
1. Meeting 81 summary is too long and duplicated
2. Decision extraction is pulling giant transcript chunks
3. Action-item recall and normalization are still weak

## Non-goals
- Do not change the meeting-confidence guardrail behavior
- Do not broaden generic transcript boosting
- Do not reduce safety on non-meeting audio

## Validation set
- Meeting 81 = primary precision benchmark
- Meeting 86 = safety benchmark
- 30-minute script = regression benchmark

## Promotion rule
A change passes only if:
- Meeting 81 improves materially
- Meeting 86 remains safely downgraded
- 30-minute benchmark remains stable
