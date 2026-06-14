# Chunk Action Extraction Scorecard

## Status

Updated after real long-meeting audio regression capture.

## Completed captures

| Meeting | Duration class | Status | Result |
|---|---:|---|---|
| IB4001 | ~30 min | PASS | Captured expected Speaker C action to create files from delimited segments / prepare data for annotation merge. |
| IS1000b | ~39 min | PASS / review | Captured Speaker B entropy/vocabulary action and minutes/shared-folder action. |
| IN1016 | ~60 min | PASS | Captured both expected must-have actions: Speaker C annotation-merge data prep and Speaker B entropy/vocabulary deliverable. |
| ES2006c | ~36 min | PASS / review | Captured useful shared-folder/smartboard actions, but included one noisy voice-recognition false positive. |

## Key findings

- Real audio uploads completed successfully for 30–60 minute meetings.
- Long-meeting action recall is materially improved.
- Expected must-have actions were captured for IB4001 and IN1016.
- IS1000b captured the important Speaker B entropy/vocabulary action.
- ES2006c completed without the earlier stuck-processing/language-detection issue.
- False-positive review is still needed, especially for vague statements such as “do something with voice recognition.”
- Current `/notes/ai` output does not expose source chunk metadata; `source` and `chunk` are blank in captured action objects.

## Launch interpretation

Hosted pilot readiness impact: positive.

Public-launch interpretation: pass with follow-up. The action recall behavior is improved enough for pilot/public-beta confidence, but a stricter public-launch version should still improve false-positive filtering and expose source chunk metadata in final action objects.

## Follow-up items

1. Filter vague/non-committal action phrases such as “do something with...”
2. Preserve `source=chunk_action_recovery` and `source_chunk` in `/notes/ai` output when chunk recovery contributes actions.
3. Add the 4 captured after outputs to regression evidence.
4. Use these captures as baseline evidence for future long-meeting regressions.
